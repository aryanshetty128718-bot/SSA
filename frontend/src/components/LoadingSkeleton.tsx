import React from 'react';

export const LoadingSkeleton: React.FC<{ rows?: number; className?: string }> = ({ rows = 3, className = '' }) => {
  return (
    <div className={`animate-pulse space-y-4 ${className}`} data-testid="loading-skeleton">
      <div className="h-6 bg-slate-200 rounded w-1/3"></div>
      <div className="space-y-2">
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="h-4 bg-slate-200 rounded w-full"></div>
        ))}
      </div>
    </div>
  );
};
