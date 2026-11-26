import React from 'react';
import { PackageOpen } from 'lucide-react';

interface EmptyStateProps {
  title: string;
  description: string;
  actionText?: string;
  onAction?: () => void;
  icon?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  actionText,
  onAction,
  icon,
}) => {
  return (
    <div className="p-8 text-center border-2 border-dashed border-slate-200 rounded-2xl max-w-md mx-auto my-6 bg-white">
      <div className="inline-flex p-4 rounded-full bg-slate-100 text-slate-500 mb-4">
        {icon || <PackageOpen className="w-10 h-10" />}
      </div>
      <h3 className="text-lg font-bold text-slate-800 mb-1">{title}</h3>
      <p className="text-sm text-slate-600 mb-5">{description}</p>
      {actionText && onAction && (
        <button
          onClick={onAction}
          className="px-4 py-2 text-sm font-semibold bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition"
        >
          {actionText}
        </button>
      )}
    </div>
  );
};
