import React from 'react';
import { getScoreBand } from '../utils/scoreUtils';
import { Shield, Info } from 'lucide-react';

interface ScoreGaugeProps {
  score: number | null | undefined;
  size?: 'md' | 'lg';
}

export const ScoreGauge: React.FC<ScoreGaugeProps> = ({ score, size = 'lg' }) => {
  const band = getScoreBand(score);
  const displayScore = score !== null && score !== undefined && score >= 0 ? score.toFixed(1) : 'N/A';

  const radius = size === 'lg' ? 64 : 44;
  const stroke = size === 'lg' ? 12 : 8;
  const normalizedRadius = radius - stroke * 2;
  const circumference = normalizedRadius * 2 * Math.PI;

  const validScore = score !== null && score !== undefined && score >= 0 ? Math.min(100, Math.max(0, score)) : 0;
  const strokeDashoffset = circumference - (validScore / 100) * circumference;

  return (
    <div className="flex flex-col items-center text-center p-4">
      <div className="relative inline-flex items-center justify-center">
        <svg height={radius * 2} width={radius * 2} className="transform -rotate-90">
          <circle
            stroke="#e2e8f0"
            fill="transparent"
            strokeWidth={stroke}
            r={normalizedRadius}
            cx={radius}
            cy={radius}
          />
          <circle
            stroke="currentColor"
            fill="transparent"
            strokeWidth={stroke}
            strokeDasharray={`${circumference} ${circumference}`}
            style={{ strokeDashoffset }}
            strokeLinecap="round"
            className={`${band.colorClass} transition-all duration-1000 ease-out`}
            r={normalizedRadius}
            cx={radius}
            cy={radius}
          />
        </svg>
        <div className="absolute flex flex-col items-center justify-center">
          <span className={`font-black tracking-tight ${size === 'lg' ? 'text-3xl' : 'text-xl'} ${band.colorClass}`}>
            {displayScore}
          </span>
          <span className="text-[10px] font-semibold text-slate-400 uppercase">/ 100</span>
        </div>
      </div>

      <div className="mt-3 flex flex-col items-center">
        <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border ${band.bgClass} ${band.borderClass} ${band.textClass}`}>
          <Shield className="w-3.5 h-3.5" />
          {band.label}
        </span>
        <p className="text-xs text-slate-500 mt-1 max-w-xs">{band.description}</p>
      </div>

      <div className="mt-2 text-[11px] text-slate-400 flex items-center gap-1">
        <Info className="w-3 h-3" />
        <span>Project-Defined Scoring Framework (0-100)</span>
      </div>
    </div>
  );
};
