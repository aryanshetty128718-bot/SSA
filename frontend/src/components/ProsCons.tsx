import React from 'react';
import type { ProConItem } from '../types';
import { CheckCircle2, AlertCircle } from 'lucide-react';

interface ProsConsProps {
  pros?: ProConItem[];
  cons?: ProConItem[];
}

export const ProsCons: React.FC<ProsConsProps> = ({ pros = [], cons = [] }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {/* Pros */}
      <div className="bg-emerald-50/60 border border-emerald-200 rounded-xl p-4">
        <h4 className="text-sm font-bold text-emerald-900 flex items-center gap-1.5 mb-3">
          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          Nutritional Pros ({pros.length})
        </h4>
        {pros.length === 0 ? (
          <p className="text-xs text-slate-500 italic">No standout positive highlights detected.</p>
        ) : (
          <ul className="space-y-2">
            {pros.map((p, idx) => (
              <li key={idx} className="text-xs">
                <span className="font-semibold text-emerald-900">{p.title}: </span>
                <span className="text-emerald-700">{p.evidence}</span>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Cons */}
      <div className="bg-rose-50/60 border border-rose-200 rounded-xl p-4">
        <h4 className="text-sm font-bold text-rose-900 flex items-center gap-1.5 mb-3">
          <AlertCircle className="w-4 h-4 text-rose-600" />
          Nutritional Cons / Flags ({cons.length})
        </h4>
        {cons.length === 0 ? (
          <p className="text-xs text-slate-500 italic">No significant negative concerns flagged.</p>
        ) : (
          <ul className="space-y-2">
            {cons.map((c, idx) => (
              <li key={idx} className="text-xs">
                <span className="font-semibold text-rose-900">{c.title}: </span>
                <span className="text-rose-700">{c.evidence}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};
