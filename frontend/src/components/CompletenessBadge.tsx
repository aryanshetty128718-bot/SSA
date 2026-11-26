import React from 'react';
import { ShieldCheck, AlertTriangle } from 'lucide-react';

interface CompletenessBadgeProps {
  score?: number; // 0.0 - 1.0
  level?: string;
  missingParameters?: string[];
}

export const CompletenessBadge: React.FC<CompletenessBadgeProps> = ({
  score = 1.0,
  level = 'High',
  missingParameters = [],
}) => {
  const pct = Math.round(score * 100);

  let badgeColor = 'bg-emerald-50 text-emerald-700 border-emerald-300';
  let Icon = ShieldCheck;

  if (score < 0.5) {
    badgeColor = 'bg-rose-50 text-rose-700 border-rose-300';
    Icon = AlertTriangle;
  } else if (score < 0.8) {
    badgeColor = 'bg-amber-50 text-amber-700 border-amber-300';
    Icon = AlertTriangle;
  }

  return (
    <div className="inline-flex flex-col gap-1">
      <div
        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs font-semibold ${badgeColor}`}
        title={missingParameters.length > 0 ? `Missing inputs: ${missingParameters.join(', ')}` : 'Complete nutrition data'}
      >
        <Icon className="w-3.5 h-3.5" />
        <span>{pct}% Data Confidence ({level})</span>
      </div>
      {missingParameters.length > 0 && (
        <span className="text-[10px] text-slate-500">
          Unreported: {missingParameters.slice(0, 3).join(', ')}{missingParameters.length > 3 ? '...' : ''}
        </span>
      )}
    </div>
  );
};
