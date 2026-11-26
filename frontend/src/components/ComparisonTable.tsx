import React from 'react';
import type { ComparisonResult } from '../types';
import { getScoreBand } from '../utils/scoreUtils';
import { Award, Package } from 'lucide-react';

interface ComparisonTableProps {
  comparison: ComparisonResult;
}

export const ComparisonTable: React.FC<ComparisonTableProps> = ({ comparison }) => {
  const { products, differences, summary } = comparison;

  return (
    <div className="space-y-6">
      {/* Products Column Headers */}
      <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white shadow-xs">
        <table className="w-full text-left text-sm border-collapse">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200">
              <th className="p-4 font-semibold text-slate-500 text-xs uppercase w-48">Parameter</th>
              {products.map((p) => {
                const band = getScoreBand(p.overall_project_score);
                return (
                  <th key={p.product_id} className="p-4 text-center min-w-44 border-l border-slate-200">
                    <div className="flex flex-col items-center">
                      <div className="w-16 h-16 bg-white rounded-lg p-1 border border-slate-100 flex items-center justify-center mb-2">
                        {p.image_url ? (
                          <img src={p.image_url} alt={p.product_name} className="max-h-full max-w-full object-contain" />
                        ) : (
                          <Package className="w-6 h-6 text-slate-300" />
                        )}
                      </div>
                      <span className="font-bold text-slate-900 text-xs line-clamp-1">{p.product_name}</span>
                      <span className="text-[10px] text-slate-400 font-medium">{p.brand || 'Brand'}</span>
                      <span className={`inline-block mt-1 px-2 py-0.5 rounded text-xs font-black ${band.colorClass} ${band.bgClass}`}>
                        Score: {p.overall_project_score !== undefined ? p.overall_project_score.toFixed(1) : 'N/A'}
                      </span>
                    </div>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {differences.map((diff, idx) => (
              <tr key={idx} className="hover:bg-slate-50/50">
                <td className="p-4 font-semibold text-slate-700 bg-slate-50/30">
                  {diff.label} <span className="text-xs text-slate-400 font-normal">({diff.unit})</span>
                </td>
                {products.map((p) => {
                  const val = diff.values[p.product_id];
                  const isBest = diff.best_product_id === p.product_id;

                  return (
                    <td
                      key={p.product_id}
                      className={`p-4 text-center border-l border-slate-100 font-mono text-sm ${
                        isBest ? 'bg-emerald-50/60 font-bold text-emerald-800' : 'text-slate-700'
                      }`}
                    >
                      <div className="flex items-center justify-center gap-1">
                        {isBest && <Award className="w-3.5 h-3.5 text-emerald-600 shrink-0" />}
                        <span>{val !== null && val !== undefined ? `${val} ${diff.unit}` : '—'}</span>
                      </div>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Nuanced Summary */}
      {summary && (
        <div className="bg-slate-900 text-white rounded-2xl p-6 shadow-md">
          <h4 className="text-sm font-bold text-emerald-400 uppercase tracking-wider mb-2">
            Nuanced Analytical Summary
          </h4>
          <p className="text-sm text-slate-300 leading-relaxed">{summary}</p>
          <p className="text-[11px] text-slate-400 mt-3 italic">
            * Note: Best values are evaluated on a per-nutrient basis. No single winner badge is awarded to encourage balanced dietary choices.
          </p>
        </div>
      )}
    </div>
  );
};
