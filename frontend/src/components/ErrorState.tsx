import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  className?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'An error occurred',
  message,
  onRetry,
  className = '',
}) => {
  return (
    <div className={`p-6 rounded-xl border border-rose-200 bg-rose-50/50 text-center max-w-lg mx-auto ${className}`}>
      <div className="inline-flex p-3 rounded-full bg-rose-100 text-rose-600 mb-3">
        <AlertCircle className="w-8 h-8" />
      </div>
      <h3 className="text-lg font-bold text-rose-900 mb-1">{title}</h3>
      <p className="text-sm text-rose-700 mb-4">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium bg-rose-600 text-white rounded-lg hover:bg-rose-700 transition"
        >
          <RefreshCw className="w-4 h-4" /> Try Again
        </button>
      )}
    </div>
  );
};
