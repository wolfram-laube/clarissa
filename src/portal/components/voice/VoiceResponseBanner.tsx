/**
 * VoiceResponseBanner - Display component for voice command responses
 * 
 * Shows responses as toast notifications with different styles for:
 * - Success (green)
 * - Error (red)
 * - Info/Question (blue)
 * - Confirmation (yellow)
 */

import React, { useState, useEffect, useCallback } from 'react';

// Types
export interface VoiceResponse {
  id: string;
  text: string;
  type: 'success' | 'error' | 'info' | 'confirmation';
  timestamp: number;
  action?: string;
  duration?: number;
  onConfirm?: () => void;
  onCancel?: () => void;
}

export interface VoiceResponseBannerProps {
  responses: VoiceResponse[];
  onDismiss: (id: string) => void;
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'top-center';
  maxVisible?: number;
  defaultDuration?: number;
}

// Icon components
const CheckIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
  </svg>
);

const ErrorIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
  </svg>
);

const InfoIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const QuestionIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const MicIcon = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
  </svg>
);

// Single toast component
const VoiceToast: React.FC<{
  response: VoiceResponse;
  onDismiss: () => void;
}> = ({ response, onDismiss }) => {
  const [isExiting, setIsExiting] = useState(false);

  useEffect(() => {
    if (response.type !== 'confirmation') {
      const duration = response.duration || 4000;
      const timer = setTimeout(() => {
        setIsExiting(true);
        setTimeout(onDismiss, 300);
      }, duration);
      return () => clearTimeout(timer);
    }
  }, [response, onDismiss]);

  const handleDismiss = useCallback(() => {
    setIsExiting(true);
    setTimeout(onDismiss, 300);
  }, [onDismiss]);

  const handleConfirm = useCallback(() => {
    response.onConfirm?.();
    handleDismiss();
  }, [response, handleDismiss]);

  const handleCancel = useCallback(() => {
    response.onCancel?.();
    handleDismiss();
  }, [response, handleDismiss]);

  // Style configurations
  const styles = {
    success: {
      bg: 'bg-green-50 border-green-200',
      icon: 'text-green-500',
      text: 'text-green-800',
      Icon: CheckIcon,
    },
    error: {
      bg: 'bg-red-50 border-red-200',
      icon: 'text-red-500',
      text: 'text-red-800',
      Icon: ErrorIcon,
    },
    info: {
      bg: 'bg-blue-50 border-blue-200',
      icon: 'text-blue-500',
      text: 'text-blue-800',
      Icon: InfoIcon,
    },
    confirmation: {
      bg: 'bg-amber-50 border-amber-200',
      icon: 'text-amber-500',
      text: 'text-amber-800',
      Icon: QuestionIcon,
    },
  };

  const style = styles[response.type];
  const { Icon } = style;

  return (
    <div
      className={`
        flex items-start gap-3 p-4 rounded-lg border shadow-lg
        transform transition-all duration-300 ease-out
        ${style.bg}
        ${isExiting ? 'opacity-0 translate-x-4' : 'opacity-100 translate-x-0'}
      `}
      role="alert"
      aria-live="polite"
    >
      {/* Voice indicator */}
      <div className={`flex-shrink-0 p-1 rounded-full bg-white/50 ${style.icon}`}>
        <MicIcon />
      </div>

      {/* Icon */}
      <div className={`flex-shrink-0 ${style.icon}`}>
        <Icon />
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <p className={`text-sm font-medium ${style.text}`}>
          {response.text}
        </p>
        {response.action && (
          <p className={`text-xs mt-1 ${style.text} opacity-70`}>
            Action: {response.action}
          </p>
        )}

        {/* Confirmation buttons */}
        {response.type === 'confirmation' && (
          <div className="flex gap-2 mt-3">
            <button
              onClick={handleConfirm}
              className="px-3 py-1.5 text-xs font-medium rounded-md
                bg-green-600 text-white hover:bg-green-700
                focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-1"
            >
              Yes, proceed
            </button>
            <button
              onClick={handleCancel}
              className="px-3 py-1.5 text-xs font-medium rounded-md
                bg-gray-200 text-gray-700 hover:bg-gray-300
                focus:outline-none focus:ring-2 focus:ring-gray-400 focus:ring-offset-1"
            >
              Cancel
            </button>
          </div>
        )}
      </div>

      {/* Close button (for non-confirmation) */}
      {response.type !== 'confirmation' && (
        <button
          onClick={handleDismiss}
          className={`flex-shrink-0 p-1 rounded hover:bg-black/5 ${style.text} opacity-50 hover:opacity-100`}
          aria-label="Dismiss"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      )}
    </div>
  );
};

// Main banner component
export const VoiceResponseBanner: React.FC<VoiceResponseBannerProps> = ({
  responses,
  onDismiss,
  position = 'top-right',
  maxVisible = 5,
}) => {
  const positionClasses = {
    'top-right': 'top-4 right-4',
    'top-left': 'top-4 left-4',
    'bottom-right': 'bottom-4 right-4',
    'bottom-left': 'bottom-4 left-4',
    'top-center': 'top-4 left-1/2 -translate-x-1/2',
  };

  const visibleResponses = responses.slice(0, maxVisible);

  if (visibleResponses.length === 0) {
    return null;
  }

  return (
    <div
      className={`fixed z-50 flex flex-col gap-2 w-96 max-w-[calc(100vw-2rem)] ${positionClasses[position]}`}
      aria-label="Voice command responses"
    >
      {visibleResponses.map((response) => (
        <VoiceToast
          key={response.id}
          response={response}
          onDismiss={() => onDismiss(response.id)}
        />
      ))}
    </div>
  );
};

// Hook for managing voice responses
export const useVoiceResponses = () => {
  const [responses, setResponses] = useState<VoiceResponse[]>([]);

  const addResponse = useCallback((
    text: string,
    type: VoiceResponse['type'] = 'info',
    options?: Partial<VoiceResponse>
  ) => {
    const response: VoiceResponse = {
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      text,
      type,
      timestamp: Date.now(),
      ...options,
    };
    setResponses((prev) => [response, ...prev]);
    return response.id;
  }, []);

  const removeResponse = useCallback((id: string) => {
    setResponses((prev) => prev.filter((r) => r.id !== id));
  }, []);

  const clearAll = useCallback(() => {
    setResponses([]);
  }, []);

  const addSuccess = useCallback((text: string, action?: string) => {
    return addResponse(text, 'success', { action, duration: 3000 });
  }, [addResponse]);

  const addError = useCallback((text: string) => {
    return addResponse(text, 'error', { duration: 6000 });
  }, [addResponse]);

  const addInfo = useCallback((text: string) => {
    return addResponse(text, 'info', { duration: 4000 });
  }, [addResponse]);

  const addConfirmation = useCallback((
    text: string,
    onConfirm: () => void,
    onCancel?: () => void
  ) => {
    return addResponse(text, 'confirmation', { onConfirm, onCancel });
  }, [addResponse]);

  return {
    responses,
    addResponse,
    removeResponse,
    clearAll,
    addSuccess,
    addError,
    addInfo,
    addConfirmation,
  };
};

export default VoiceResponseBanner;