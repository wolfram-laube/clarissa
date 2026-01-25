/**
 * CLARISSA Voice Input Component
 * 
 * WebAudio-based voice capture with VAD for browser-based speech input.
 * 
 * Features:
 * - Real-time audio capture from microphone
 * - Client-side Voice Activity Detection
 * - Audio streaming to backend
 * - Visual feedback (recording indicator, waveform)
 * 
 * ADR-028 Reference: Section 1 - Audio Capture Layer
 * Issue: #67 - WebAudio Capture with VAD
 */

import React, { useState, useRef, useCallback, useEffect } from 'react';

// Types
interface VoiceInputProps {
  /** Callback when audio is ready for transcription */
  onAudioReady: (audioBlob: Blob) => void;
  /** Callback for streaming audio chunks */
  onAudioChunk?: (chunk: Float32Array, isSpeech: boolean) => void;
  /** Callback when transcription is received */
  onTranscription?: (text: string) => void;
  /** WebSocket URL for streaming mode */
  wsUrl?: string;
  /** Enable visual waveform display */
  showWaveform?: boolean;
  /** VAD sensitivity: 'aggressive' | 'normal' | 'sensitive' */
  vadMode?: 'aggressive' | 'normal' | 'sensitive';
  /** Custom class name */
  className?: string;
}

interface AudioState {
  isRecording: boolean;
  isSpeaking: boolean;
  audioLevel: number;
  duration: number;
  error: string | null;
}

// VAD thresholds for different modes
const VAD_THRESHOLDS = {
  aggressive: { energy: -35, zcr: 0.15 },
  normal: { energy: -40, zcr: 0.1 },
  sensitive: { energy: -45, zcr: 0.08 },
};

/**
 * Voice Activity Detection using energy and zero-crossing rate
 */
function detectVoiceActivity(
  samples: Float32Array,
  mode: 'aggressive' | 'normal' | 'sensitive' = 'normal'
): { isSpeech: boolean; energy: number; confidence: number } {
  const threshold = VAD_THRESHOLDS[mode];
  
  // Calculate RMS energy in dB
  const rms = Math.sqrt(samples.reduce((sum, s) => sum + s * s, 0) / samples.length);
  const energyDb = 20 * Math.log10(Math.max(rms, 1e-10));
  
  // Calculate zero-crossing rate
  let zeroCrossings = 0;
  for (let i = 1; i < samples.length; i++) {
    if ((samples[i] >= 0 && samples[i - 1] < 0) || 
        (samples[i] < 0 && samples[i - 1] >= 0)) {
      zeroCrossings++;
    }
  }
  const zcr = zeroCrossings / samples.length;
  
  // Speech detection: moderate energy and ZCR
  const energyOk = energyDb > threshold.energy;
  const zcrOk = zcr > threshold.zcr && zcr < 0.5;
  const isSpeech = energyOk && zcrOk;
  
  // Confidence based on how clearly it matches
  let confidence = 0.5;
  if (isSpeech) {
    confidence = Math.min(0.95, 0.7 + (energyDb - threshold.energy) / 20);
  } else {
    confidence = Math.max(0.1, 0.3 - (threshold.energy - energyDb) / 20);
  }
  
  return { isSpeech, energy: energyDb, confidence };
}

/**
 * Convert Float32Array to Int16Array (PCM) for backend
 */
function float32ToInt16(float32: Float32Array): Int16Array {
  const int16 = new Int16Array(float32.length);
  for (let i = 0; i < float32.length; i++) {
    const s = Math.max(-1, Math.min(1, float32[i]));
    int16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
  }
  return int16;
}

/**
 * Create a WAV blob from audio samples
 */
function createWavBlob(samples: Int16Array, sampleRate: number): Blob {
  const buffer = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(buffer);
  
  // WAV header
  const writeString = (offset: number, str: string) => {
    for (let i = 0; i < str.length; i++) {
      view.setUint8(offset + i, str.charCodeAt(i));
    }
  };
  
  writeString(0, 'RIFF');
  view.setUint32(4, 36 + samples.length * 2, true);
  writeString(8, 'WAVE');
  writeString(12, 'fmt ');
  view.setUint32(16, 16, true); // Subchunk1Size
  view.setUint16(20, 1, true); // PCM
  view.setUint16(22, 1, true); // Mono
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true); // ByteRate
  view.setUint16(32, 2, true); // BlockAlign
  view.setUint16(34, 16, true); // BitsPerSample
  writeString(36, 'data');
  view.setUint32(40, samples.length * 2, true);
  
  // Audio data
  const dataView = new Int16Array(buffer, 44);
  dataView.set(samples);
  
  return new Blob([buffer], { type: 'audio/wav' });
}

/**
 * VoiceInput Component
 */
export const VoiceInput: React.FC<VoiceInputProps> = ({
  onAudioReady,
  onAudioChunk,
  onTranscription,
  wsUrl,
  showWaveform = true,
  vadMode = 'normal',
  className = '',
}) => {
  // State
  const [state, setState] = useState<AudioState>({
    isRecording: false,
    isSpeaking: false,
    audioLevel: 0,
    duration: 0,
    error: null,
  });
  
  // Refs
  const audioContextRef = useRef<AudioContext | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const recordedChunksRef = useRef<Float32Array[]>([]);
  const speechChunksRef = useRef<Float32Array[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const animationRef = useRef<number>(0);
  
  // Speech state tracking
  const speechStartRef = useRef<number | null>(null);
  const silenceStartRef = useRef<number | null>(null);
  
  const MIN_SPEECH_MS = 250;
  const MIN_SILENCE_MS = 500;
  const MAX_DURATION_S = 30;
  
  /**
   * Start recording
   */
  const startRecording = useCallback(async () => {
    try {
      // Request microphone access with noise suppression
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 16000,
        },
      });
      
      mediaStreamRef.current = stream;
      
      // Create audio context
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)({
        sampleRate: 16000,
      });
      audioContextRef.current = audioContext;
      
      // Create source and processor
      const source = audioContext.createMediaStreamSource(stream);
      const processor = audioContext.createScriptProcessor(4096, 1, 1);
      processorRef.current = processor;
      
      // Reset state
      recordedChunksRef.current = [];
      speechChunksRef.current = [];
      speechStartRef.current = null;
      silenceStartRef.current = null;
      
      // Process audio chunks
      processor.onaudioprocess = (e) => {
        const inputData = e.inputBuffer.getChannelData(0);
        const samples = new Float32Array(inputData);
        
        // Voice activity detection
        const vad = detectVoiceActivity(samples, vadMode);
        const now = Date.now();
        
        // Update audio level for visualization
        setState(prev => ({
          ...prev,
          audioLevel: Math.max(0, (vad.energy + 60) / 60), // Normalize to 0-1
        }));
        
        // Track speech/silence transitions
        if (vad.isSpeech) {
          silenceStartRef.current = null;
          
          if (speechStartRef.current === null) {
            speechStartRef.current = now;
          } else if (now - speechStartRef.current >= MIN_SPEECH_MS) {
            setState(prev => ({ ...prev, isSpeaking: true }));
          }
        } else {
          if (speechStartRef.current !== null) {
            if (silenceStartRef.current === null) {
              silenceStartRef.current = now;
            } else if (now - silenceStartRef.current >= MIN_SILENCE_MS) {
              // Speech ended - process the recording
              speechStartRef.current = null;
              setState(prev => ({ ...prev, isSpeaking: false }));
            }
          }
        }
        
        // Store audio
        recordedChunksRef.current.push(samples.slice());
        
        if (vad.isSpeech || speechStartRef.current !== null) {
          speechChunksRef.current.push(samples.slice());
        }
        
        // Callback for streaming
        if (onAudioChunk) {
          onAudioChunk(samples, vad.isSpeech);
        }
        
        // Send to WebSocket if available
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          const int16 = float32ToInt16(samples);
          wsRef.current.send(int16.buffer);
        }
        
        // Update duration
        setState(prev => ({
          ...prev,
          duration: recordedChunksRef.current.length * 4096 / 16000,
        }));
        
        // Stop if max duration reached
        if (recordedChunksRef.current.length * 4096 / 16000 >= MAX_DURATION_S) {
          stopRecording();
        }
      };
      
      // Connect audio graph
      source.connect(processor);
      processor.connect(audioContext.destination);
      
      // Connect WebSocket if URL provided
      if (wsUrl) {
        wsRef.current = new WebSocket(wsUrl);
        wsRef.current.binaryType = 'arraybuffer';
        wsRef.current.onmessage = (event) => {
          const data = JSON.parse(event.data);
          if (data.transcription && onTranscription) {
            onTranscription(data.transcription);
          }
        };
      }
      
      setState(prev => ({
        ...prev,
        isRecording: true,
        error: null,
      }));
      
      // Start waveform animation
      if (showWaveform) {
        drawWaveform();
      }
      
    } catch (err) {
      console.error('Failed to start recording:', err);
      setState(prev => ({
        ...prev,
        error: err instanceof Error ? err.message : 'Microphone access denied',
      }));
    }
  }, [vadMode, wsUrl, onAudioChunk, onTranscription, showWaveform]);
  
  /**
   * Stop recording
   */
  const stopRecording = useCallback(() => {
    // Stop audio processing
    if (processorRef.current) {
      processorRef.current.disconnect();
      processorRef.current = null;
    }
    
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(track => track.stop());
      mediaStreamRef.current = null;
    }
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    // Cancel animation
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
    }
    
    // Create WAV from speech chunks (or all if no speech detected)
    const chunks = speechChunksRef.current.length > 0 
      ? speechChunksRef.current 
      : recordedChunksRef.current;
    
    if (chunks.length > 0) {
      // Concatenate all chunks
      const totalLength = chunks.reduce((sum, c) => sum + c.length, 0);
      const concatenated = new Float32Array(totalLength);
      let offset = 0;
      for (const chunk of chunks) {
        concatenated.set(chunk, offset);
        offset += chunk.length;
      }
      
      // Convert to WAV
      const int16 = float32ToInt16(concatenated);
      const wavBlob = createWavBlob(int16, 16000);
      
      // Callback
      onAudioReady(wavBlob);
    }
    
    setState(prev => ({
      ...prev,
      isRecording: false,
      isSpeaking: false,
      audioLevel: 0,
    }));
  }, [onAudioReady]);
  
  /**
   * Draw waveform visualization
   */
  const drawWaveform = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    const width = canvas.width;
    const height = canvas.height;
    
    const draw = () => {
      ctx.clearRect(0, 0, width, height);
      
      // Background
      ctx.fillStyle = state.isSpeaking ? '#e8f5e9' : '#f5f5f5';
      ctx.fillRect(0, 0, width, height);
      
      // Level bar
      const level = state.audioLevel;
      const barHeight = height * level;
      
      ctx.fillStyle = state.isSpeaking ? '#4caf50' : '#2196f3';
      ctx.fillRect(0, height - barHeight, width, barHeight);
      
      // Speaking indicator
      if (state.isSpeaking) {
        ctx.fillStyle = '#4caf50';
        ctx.beginPath();
        ctx.arc(width - 15, 15, 8, 0, Math.PI * 2);
        ctx.fill();
      }
      
      if (state.isRecording) {
        animationRef.current = requestAnimationFrame(draw);
      }
    };
    
    draw();
  }, [state.isRecording, state.isSpeaking, state.audioLevel]);
  
  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (state.isRecording) {
        stopRecording();
      }
    };
  }, []);
  
  return (
    <div className={`voice-input ${className}`}>
      {/* Waveform canvas */}
      {showWaveform && (
        <canvas 
          ref={canvasRef}
          width={200}
          height={50}
          className="voice-input-waveform"
          style={{
            border: '1px solid #ddd',
            borderRadius: '4px',
            marginBottom: '8px',
          }}
        />
      )}
      
      {/* Controls */}
      <div className="voice-input-controls">
        <button
          onClick={state.isRecording ? stopRecording : startRecording}
          className={`voice-input-button ${state.isRecording ? 'recording' : ''}`}
          style={{
            padding: '12px 24px',
            fontSize: '16px',
            borderRadius: '8px',
            border: 'none',
            cursor: 'pointer',
            backgroundColor: state.isRecording ? '#f44336' : '#2196f3',
            color: 'white',
            transition: 'background-color 0.2s',
          }}
        >
          {state.isRecording ? (
            <>
              <span className="mic-icon">🔴</span> Stop Recording
            </>
          ) : (
            <>
              <span className="mic-icon">🎤</span> Start Recording
            </>
          )}
        </button>
        
        {/* Status */}
        {state.isRecording && (
          <div className="voice-input-status" style={{ marginTop: '8px' }}>
            <span>
              {state.isSpeaking ? '🗣️ Speaking...' : '👂 Listening...'}
            </span>
            <span style={{ marginLeft: '16px' }}>
              {state.duration.toFixed(1)}s / {MAX_DURATION_S}s
            </span>
          </div>
        )}
        
        {/* Error */}
        {state.error && (
          <div className="voice-input-error" style={{ color: 'red', marginTop: '8px' }}>
            ⚠️ {state.error}
          </div>
        )}
      </div>
    </div>
  );
};

export default VoiceInput;
