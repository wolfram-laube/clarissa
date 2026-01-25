/**
 * RecorderToolbar - Compact toolbar for screen recording in Portal
 * 
 * Provides a floating toolbar for screen recording that can be
 * positioned anywhere in the Portal UI.
 * 
 * Issue: #77 - Portal Screen Recorder Integration
 */

import React, { useState, useCallback } from 'react';
import { useScreenRecorder, RecordingOptions } from './useScreenRecorder';

interface RecorderToolbarProps {
  /** Position of the toolbar */
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'floating';
  /** Callback when recording is ready for upload */
  onUpload?: (blob: Blob) => Promise<void>;
  /** Show upload button (requires onUpload) */
  showUpload?: boolean;
  /** Recording options */
  recordingOptions?: RecordingOptions;
  /** Custom class name */
  className?: string;
}

const formatDuration = (seconds: number): string => {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
};

const positionStyles: Record<string, React.CSSProperties> = {
  'top-right': { top: 16, right: 16 },
  'top-left': { top: 16, left: 16 },
  'bottom-right': { bottom: 16, right: 16 },
  'bottom-left': { bottom: 16, left: 16 },
  'floating': { top: '50%', right: 16, transform: 'translateY(-50%)' },
};

export const RecorderToolbar: React.FC<RecorderToolbarProps> = ({
  position = 'top-right',
  onUpload,
  showUpload = false,
  recordingOptions,
  className = '',
}) => {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [isExpanded, setIsExpanded] = useState(false);

  const handleRecordingComplete = useCallback((blob: Blob, url: string) => {
    console.log('Recording complete:', blob.size, 'bytes');
    setIsExpanded(true);
  }, []);

  const {
    state,
    startRecording,
    stopRecording,
    pauseRecording,
    resumeRecording,
    downloadRecording,
    clearRecording,
    getBlob,
  } = useScreenRecorder(handleRecordingComplete);

  const handleUpload = async () => {
    if (!onUpload) return;
    
    const blob = getBlob();
    if (!blob) return;

    setIsUploading(true);
    setUploadStatus('idle');
    
    try {
      await onUpload(blob);
      setUploadStatus('success');
      setTimeout(() => setUploadStatus('idle'), 3000);
    } catch (error) {
      console.error('Upload failed:', error);
      setUploadStatus('error');
    } finally {
      setIsUploading(false);
    }
  };

  const handleStart = () => {
    setIsExpanded(true);
    startRecording(recordingOptions);
  };

  const handleClear = () => {
    clearRecording();
    setIsExpanded(false);
    setUploadStatus('idle');
  };

  return (
    <div
      className={`recorder-toolbar ${className}`}
      style={{
        position: 'fixed',
        ...positionStyles[position],
        zIndex: 10000,
        display: 'flex',
        flexDirection: 'column',
        gap: '8px',
        padding: '12px',
        background: 'rgba(30, 30, 30, 0.95)',
        borderRadius: '12px',
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.3)',
        backdropFilter: 'blur(10px)',
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        fontSize: '14px',
        color: '#fff',
        minWidth: isExpanded ? '200px' : 'auto',
        transition: 'all 0.3s ease',
      }}
    >
      {/* Header Row */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        {/* Recording indicator */}
        {state.isRecording && (
          <div
            style={{
              width: '12px',
              height: '12px',
              borderRadius: '50%',
              background: state.isPaused ? '#ffc107' : '#f44336',
              animation: state.isPaused ? 'none' : 'pulse 1.5s infinite',
            }}
          />
        )}
        
        {/* Duration */}
        {(state.isRecording || state.previewUrl) && (
          <span style={{ fontVariantNumeric: 'tabular-nums', minWidth: '50px' }}>
            {formatDuration(state.duration)}
          </span>
        )}
        
        {/* Main action button */}
        {!state.isRecording ? (
          <button
            onClick={handleStart}
            style={{
              padding: '8px 16px',
              background: '#f44336',
              color: '#fff',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              fontWeight: 600,
              transition: 'background 0.2s',
            }}
            onMouseOver={(e) => e.currentTarget.style.background = '#d32f2f'}
            onMouseOut={(e) => e.currentTarget.style.background = '#f44336'}
          >
            <span>⏺</span>
            Record
          </button>
        ) : (
          <button
            onClick={stopRecording}
            style={{
              padding: '8px 16px',
              background: '#4caf50',
              color: '#fff',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              fontWeight: 600,
            }}
          >
            <span>⏹</span>
            Stop
          </button>
        )}
      </div>

      {/* Control row (when recording) */}
      {state.isRecording && (
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={state.isPaused ? resumeRecording : pauseRecording}
            style={{
              padding: '6px 12px',
              background: 'rgba(255, 255, 255, 0.1)',
              color: '#fff',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              flex: 1,
            }}
          >
            {state.isPaused ? '▶️ Resume' : '⏸️ Pause'}
          </button>
        </div>
      )}

      {/* Preview row (when complete) */}
      {state.previewUrl && !state.isRecording && (
        <>
          {/* Video preview */}
          <video
            src={state.previewUrl}
            controls
            style={{
              width: '100%',
              maxHeight: '120px',
              borderRadius: '8px',
              background: '#000',
            }}
          />
          
          {/* Action buttons */}
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            <button
              onClick={() => downloadRecording()}
              style={{
                padding: '6px 12px',
                background: '#2196f3',
                color: '#fff',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                flex: 1,
              }}
            >
              💾 Download
            </button>
            
            {showUpload && onUpload && (
              <button
                onClick={handleUpload}
                disabled={isUploading}
                style={{
                  padding: '6px 12px',
                  background: uploadStatus === 'success' 
                    ? '#4caf50' 
                    : uploadStatus === 'error' 
                    ? '#f44336' 
                    : '#9c27b0',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: isUploading ? 'wait' : 'pointer',
                  flex: 1,
                  opacity: isUploading ? 0.7 : 1,
                }}
              >
                {isUploading ? '⏳ Uploading...' : 
                 uploadStatus === 'success' ? '✅ Uploaded' :
                 uploadStatus === 'error' ? '❌ Retry' :
                 '☁️ Upload'}
              </button>
            )}
            
            <button
              onClick={handleClear}
              style={{
                padding: '6px 12px',
                background: 'rgba(255, 255, 255, 0.1)',
                color: '#fff',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
              }}
            >
              🗑️
            </button>
          </div>
        </>
      )}

      {/* Error display */}
      {state.error && (
        <div style={{ 
          color: '#f44336', 
          fontSize: '12px', 
          padding: '8px',
          background: 'rgba(244, 67, 54, 0.1)',
          borderRadius: '6px',
        }}>
          ⚠️ {state.error}
        </div>
      )}

      {/* Pulse animation */}
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
      `}</style>
    </div>
  );
};

export default RecorderToolbar;
