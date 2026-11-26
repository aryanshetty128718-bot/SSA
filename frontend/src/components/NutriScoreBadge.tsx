import React from 'react';
import { getNutriScoreColor } from '../utils/scoreUtils';
import { HelpCircle } from 'lucide-react';

interface NutriScoreBadgeProps {
  grade?: string;
  points?: number;
  status?: string;
  missingInputs?: string[];
  size?: 'sm' | 'md' | 'lg';
}

export const NutriScoreBadge: React.FC<NutriScoreBadgeProps> = ({
  grade,
  points,
  status,
  missingInputs = [],
  size = 'md',
}) => {
  const isComputable = status !== 'not_computable' && !!grade;
  const color = getNutriScoreColor(grade);

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-sm px-3 py-1',
    lg: 'text-lg px-4 py-2 font-black',
  };

  if (!isComputable) {
    return (
      <div className="inline-flex flex-col items-start gap-1">
        <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
          Official Reference Standard
        </span>
        <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-100 border border-slate-300 text-slate-700 text-xs font-medium">
          <HelpCircle className="w-3.5 h-3.5 text-slate-500" />
          <span>Nutri-Score: Not Computable</span>
        </div>
        {missingInputs.length > 0 && (
          <span className="text-[10px] text-slate-500">
            Missing: {missingInputs.join(', ')}
          </span>
        )}
      </div>
    );
  }

  return (
    <div className="inline-flex flex-col items-start gap-0.5">
      <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">
        Official Reference Standard
      </span>
      <div className="inline-flex items-center gap-1.5">
        <div
          className={`inline-flex items-center justify-center font-black rounded-md uppercase tracking-wider shadow-sm ${color.bg} ${color.text} ${sizeClasses[size]}`}
          title={`Official Nutri-Score 2023 Grade ${grade} (${points ?? 0} points)`}
        >
          Nutri-Score {grade}
        </div>
        {points !== undefined && (
          <span className="text-xs font-semibold text-slate-500">
            ({points} pts)
          </span>
        )}
      </div>
    </div>
  );
};
