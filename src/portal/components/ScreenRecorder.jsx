/**
 * CLARISSA Portal - Screen Recorder Component
 * 
 * Browser-basierte Bildschirmaufnahme mit Start/Stop
 * Verwendet: getDisplayMedia + MediaRecorder API
 */

import React, { useState, useRef, useCallback } from 'react';

const ScreenRecorder = ({ onRecordingComplete }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [duration, setDuration] = useState(0);
  const [previewUrl, setPreviewUrl] = useState(null);
  
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const timerRef = useRef(null);
  const streamRef = useRef(null);

  const startRecording = useCallback(async () => {
    try {
      // Screen + System Audio
      const screenStream = await navigator.mediaDevices.getDisplayMedia({
        video: { 
          cursor: 'always',
          displaySurface: 'browser'  // Prefer current tab
        },
        audio: true  // System audio (if shared)
      });

      // Microphone (separate, für Kommentar)
      let micStream = null;
      try {
        micStream = await navigator.mediaDevices.getUserMedia({ 
          audio: { 
            echoCancellation: true,
            noiseSuppression: true 
          } 
        });
      } catch (e) {
        console.warn('No microphone access, continuing without');
      }

      // Combine streams
      const tracks = [
        ...screenStream.getVideoTracks(),
        ...screenStream.getAudioTracks()
      ];
      
      if (micStream) {
        // Mix microphone with system audio
        const audioContext = new AudioContext();
        const dest = audioContext.createMediaStreamDestination();
        
        if (screenStream.getAudioTracks().length > 0) {
          const systemSource = audioContext.createMediaStreamSource(screenStream);
          systemSource.connect(dest);
        }
        
        const micSource = audioContext.createMediaStreamSource(micStream);
        micSource.connect(dest);
        
        // Replace audio tracks with mixed audio
        tracks.push(...dest.stream.getAudioTracks());
      }

      const combinedStream = new MediaStream(tracks);
      streamRef.current = combinedStream;

      // Setup MediaRecorder
      const mediaRecorder = new MediaRecorder(combinedStream, {
        mimeType: 'video/webm;codecs=vp9,opus',
        videoBitsPerSecond: 3000000  // 3 Mbps
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
        setPreviewUrl(url);
        
        if (onRecordingComplete) {
          onRecordingComplete(blob, url);
        }
      };

      // Handle user stopping screen share via browser UI
      screenStream.getVideoTracks()[0].onended = () => {
        stopRecording();
      };

      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start(1000);  // Chunk every second

      // Start timer
      setDuration(0);
      timerRef.current = setInterval(() => {
        setDuration(d => d + 1);
      }, 1000);

      setIsRecording(true);
      setIsPaused(false);

    } catch (err) {
      console.error('Failed to start recording:', err);
      alert(`Recording failed: ${err.message}`);
    }
  }, [onRecordingComplete]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      
      // Stop all tracks
      streamRef.current?.getTracks().forEach(track => track.stop());
      
      clearInterval(timerRef.current);
      setIsRecording(false);
      setIsPaused(false);
    }
  }, [isRecording]);

  const pauseRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      if (isPaused) {
        mediaRecorderRef.current.resume();
        timerRef.current = setInterval(() => {
          setDuration(d => d + 1);
        }, 1000);
      } else {
        mediaRecorderRef.current.pause();
        clearInterval(timerRef.current);
      }
      setIsPaused(!isPaused);
    }
  }, [isRecording, isPaused]);

  const downloadRecording = useCallback(() => {
    if (previewUrl) {
      const a = document.createElement('a');
      a.href = previewUrl;
      a.download = `clarissa-demo-${new Date().toISOString().slice(0,19).replace(/:/g,'-')}.webm`;
      a.click();
    }
  }, [previewUrl]);

  const formatTime = (seconds) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <div className="bg-gray-900 rounded-lg p-4 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-white font-semibold flex items-center gap-2">
          🎬 Demo Recording
        </h3>
        {isRecording && (
          <div className="flex items-center gap-2">
            <span className={`w-3 h-3 rounded-full ${isPaused ? 'bg-yellow-500' : 'bg-red-500 animate-pulse'}`} />
            <span className="text-white font-mono">{formatTime(duration)}</span>
          </div>
        )}
      </div>

      {/* Controls */}
      <div className="flex gap-2">
        {!isRecording ? (
          <button
            onClick={startRecording}
            className="flex-1 bg-red-600 hover:bg-red-700 text-white py-2 px-4 rounded-lg flex items-center justify-center gap-2 transition-colors"
          >
            <span className="w-3 h-3 bg-white rounded-full" />
            Start Recording
          </button>
        ) : (
          <>
            <button
              onClick={pauseRecording}
              className="flex-1 bg-yellow-600 hover:bg-yellow-700 text-white py-2 px-4 rounded-lg transition-colors"
            >
              {isPaused ? '▶️ Resume' : '⏸️ Pause'}
            </button>
            <button
              onClick={stopRecording}
              className="flex-1 bg-gray-600 hover:bg-gray-700 text-white py-2 px-4 rounded-lg transition-colors"
            >
              ⏹️ Stop
            </button>
          </>
        )}
      </div>

      {/* Preview */}
      {previewUrl && (
        <div className="space-y-2">
          <video 
            src={previewUrl} 
            controls 
            className="w-full rounded-lg"
          />
          <div className="flex gap-2">
            <button
              onClick={downloadRecording}
              className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-lg transition-colors"
            >
              💾 Download
            </button>
            <button
              onClick={() => setPreviewUrl(null)}
              className="bg-gray-600 hover:bg-gray-700 text-white py-2 px-4 rounded-lg transition-colors"
            >
              🗑️
            </button>
          </div>
        </div>
      )}

      {/* Info */}
      <p className="text-gray-400 text-xs">
        Records screen + microphone. Browser will ask for permissions.
      </p>
    </div>
  );
};

export default ScreenRecorder;
