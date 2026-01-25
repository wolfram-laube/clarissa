/**
 * useScreenRecorder Hook
 * 
 * Reusable React hook for screen recording functionality.
 * Extracts recording logic from ScreenRecorder component for use
 * across different UI contexts (toolbar, modal, embedded).
 * 
 * Issue: #77 - Portal Screen Recorder Integration
 */

import { useState, useRef, useCallback, useEffect } from 'react';

export interface RecordingState {
  isRecording: boolean;
  isPaused: boolean;
  duration: number;
  previewUrl: string | null;
  error: string | null;
}

export interface RecordingOptions {
  /** Include system audio if available */
  includeSystemAudio?: boolean;
  /** Include microphone audio */
  includeMicrophone?: boolean;
  /** Video bitrate in bps (default: 3Mbps) */
  videoBitrate?: number;
  /** Maximum duration in seconds (0 = unlimited) */
  maxDuration?: number;
  /** Preferred display surface: 'browser' | 'window' | 'monitor' */
  displaySurface?: 'browser' | 'window' | 'monitor';
}

export interface UseScreenRecorderReturn {
  state: RecordingState;
  startRecording: (options?: RecordingOptions) => Promise<void>;
  stopRecording: () => void;
  pauseRecording: () => void;
  resumeRecording: () => void;
  downloadRecording: (filename?: string) => void;
  uploadRecording: (uploadFn: (blob: Blob) => Promise<string>) => Promise<string>;
  clearRecording: () => void;
  getBlob: () => Blob | null;
}

const DEFAULT_OPTIONS: RecordingOptions = {
  includeSystemAudio: true,
  includeMicrophone: true,
  videoBitrate: 3000000,
  maxDuration: 0,
  displaySurface: 'browser',
};

/**
 * Hook for screen recording functionality.
 * 
 * @param onRecordingComplete - Callback when recording finishes
 * @returns Recording state and control functions
 * 
 * @example
 * ```tsx
 * const { state, startRecording, stopRecording } = useScreenRecorder();
 * 
 * return (
 *   <button onClick={() => startRecording()}>
 *     {state.isRecording ? 'Stop' : 'Record'}
 *   </button>
 * );
 * ```
 */
export function useScreenRecorder(
  onRecordingComplete?: (blob: Blob, url: string) => void
): UseScreenRecorderReturn {
  const [state, setState] = useState<RecordingState>({
    isRecording: false,
    isPaused: false,
    duration: 0,
    previewUrl: null,
    error: null,
  });

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<number | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const blobRef = useRef<Blob | null>(null);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
      if (state.previewUrl) {
        URL.revokeObjectURL(state.previewUrl);
      }
    };
  }, []);

  const startRecording = useCallback(async (options: RecordingOptions = {}) => {
    const opts = { ...DEFAULT_OPTIONS, ...options };
    
    try {
      // Request screen capture
      const screenStream = await navigator.mediaDevices.getDisplayMedia({
        video: {
          cursor: 'always',
          displaySurface: opts.displaySurface,
        },
        audio: opts.includeSystemAudio,
      });

      // Request microphone if needed
      let micStream: MediaStream | null = null;
      if (opts.includeMicrophone) {
        try {
          micStream = await navigator.mediaDevices.getUserMedia({
            audio: {
              echoCancellation: true,
              noiseSuppression: true,
            },
          });
        } catch (e) {
          console.warn('Microphone access denied, continuing without');
        }
      }

      // Combine audio streams
      const tracks = [
        ...screenStream.getVideoTracks(),
        ...screenStream.getAudioTracks(),
      ];

      if (micStream) {
        // Mix microphone with system audio using AudioContext
        const audioContext = new AudioContext();
        const dest = audioContext.createMediaStreamDestination();

        if (screenStream.getAudioTracks().length > 0) {
          const systemSource = audioContext.createMediaStreamSource(screenStream);
          systemSource.connect(dest);
        }

        const micSource = audioContext.createMediaStreamSource(micStream);
        micSource.connect(dest);

        tracks.push(...dest.stream.getAudioTracks());
      }

      const combinedStream = new MediaStream(tracks);
      streamRef.current = combinedStream;

      // Setup MediaRecorder
      const mediaRecorder = new MediaRecorder(combinedStream, {
        mimeType: 'video/webm;codecs=vp9,opus',
        videoBitsPerSecond: opts.videoBitrate,
      });

      chunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'video/webm' });
        const url = URL.createObjectURL(blob);
        
        blobRef.current = blob;
        
        setState(prev => ({
          ...prev,
          isRecording: false,
          isPaused: false,
          previewUrl: url,
        }));

        if (onRecordingComplete) {
          onRecordingComplete(blob, url);
        }
      };

      // Handle user stopping via browser UI
      screenStream.getVideoTracks()[0].onended = () => {
        stopRecording();
      };

      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start(1000); // Collect data every second

      // Start duration timer
      timerRef.current = window.setInterval(() => {
        setState(prev => {
          const newDuration = prev.duration + 1;
          
          // Check max duration
          if (opts.maxDuration && newDuration >= opts.maxDuration) {
            stopRecording();
          }
          
          return { ...prev, duration: newDuration };
        });
      }, 1000);

      setState(prev => ({
        ...prev,
        isRecording: true,
        isPaused: false,
        duration: 0,
        error: null,
      }));

    } catch (error) {
      const message = error instanceof Error ? error.message : 'Recording failed';
      setState(prev => ({ ...prev, error: message }));
      console.error('Screen recording error:', error);
    }
  }, [onRecordingComplete]);

  const stopRecording = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }

    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
  }, []);

  const pauseRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.pause();
      
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
      
      setState(prev => ({ ...prev, isPaused: true }));
    }
  }, []);

  const resumeRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'paused') {
      mediaRecorderRef.current.resume();
      
      timerRef.current = window.setInterval(() => {
        setState(prev => ({ ...prev, duration: prev.duration + 1 }));
      }, 1000);
      
      setState(prev => ({ ...prev, isPaused: false }));
    }
  }, []);

  const downloadRecording = useCallback((filename?: string) => {
    if (!blobRef.current) return;
    
    const name = filename || `recording-${new Date().toISOString().slice(0, 19).replace(/[T:]/g, '-')}.webm`;
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blobRef.current);
    a.download = name;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }, []);

  const uploadRecording = useCallback(async (
    uploadFn: (blob: Blob) => Promise<string>
  ): Promise<string> => {
    if (!blobRef.current) {
      throw new Error('No recording to upload');
    }
    return uploadFn(blobRef.current);
  }, []);

  const clearRecording = useCallback(() => {
    if (state.previewUrl) {
      URL.revokeObjectURL(state.previewUrl);
    }
    blobRef.current = null;
    chunksRef.current = [];
    setState(prev => ({
      ...prev,
      previewUrl: null,
      duration: 0,
    }));
  }, [state.previewUrl]);

  const getBlob = useCallback(() => blobRef.current, []);

  return {
    state,
    startRecording,
    stopRecording,
    pauseRecording,
    resumeRecording,
    downloadRecording,
    uploadRecording,
    clearRecording,
    getBlob,
  };
}

export default useScreenRecorder;
