import React from 'react';
import { Link } from 'react-router-dom';
import type { AlternativeItem } from '../types';
import { getScoreBand, getNutriScoreColor } from '../utils/scoreUtils';
import { DeltaChip } from './DeltaChip';
import { Package, ArrowUpRight, AlertTriangle, ShieldCheck } from 'lucide-react';

interface AlternativeCardProps {
  alternative: AlternativeItem;
  onCompareToggle?: (alt: AlternativeItem) => void;
  isComparing?: boolean;
}

export const AlternativeCard: React.FC<AlternativeCardProps> = ({
  alternative,
  onCompareToggle,
  isComparing = false,
}) => {
  const band = getScoreBand(alternative.overall_score);
  const nutriColor = getNutriScoreColor(alternative.nutri_score_grade);

  const deltas = Object.entries(alternative.parameter_deltas || {});
  const simPct = Math.round(alternative.similarity_score * 100);

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs hover:shadow-md transition flex flex-col justify-between">
      <div>
        {/* Top Header: Image, Badges, Brand */}
        <div className="flex gap-4 mb-3">
          <div className="w-20 h-20 bg-slate-50 rounded-xl overflow-hidden shrink-0 flex items-center justify-center p-1 border border-slate-100">
            {alternative.image_url ? (
              <img
                src={alternative.image_url}
                alt={alternative.name}
                className="max-h-full max-w-full object-contain"
                loading="lazy"
                onError={(e) => {
                  (e.target as HTMLElement).style.display = 'none';
                }}
              />
            ) : (
              <Package className="w-8 h-8 text-slate-300" />
            )}
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between gap-1 mb-1">
              <div className="flex items-center gap-1.5 truncate">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider truncate">
                  {alternative.brand || 'Brand Unspecified'}
                </span>
                {alternative.source === 'seed' && (
                  <span className="text-[9px] font-bold px-1.5 py-0.2 rounded bg-amber-100 text-amber-800 border border-amber-300">
                    Sample Data
                  </span>
                )}
                {alternative.source === 'user_entered' && (
                  <span className="text-[9px] font-bold px-1.5 py-0.2 rounded bg-purple-100 text-purple-800 border border-purple-300">
                    User-Entered
                  </span>
                )}
              </div>
              {alternative.nutri_score_grade && (
                <span
                  className={`text-[10px] font-black uppercase px-2 py-0.5 rounded shadow-xs ${nutriColor.bg} ${nutriColor.text}`}
                >
                  Nutri-Score {alternative.nutri_score_grade}
                </span>
              )}
            </div>

            <h4 className="text-sm font-bold text-slate-900 line-clamp-2" title={alternative.name}>
              {alternative.name}
            </h4>

            <div className="mt-1 flex items-center gap-2 text-xs">
              <span className={`font-black ${band.colorClass}`}>
                Score: {alternative.overall_score.toFixed(1)}
              </span>
              <span className="text-emerald-700 font-semibold bg-emerald-50 px-1.5 py-0.5 rounded text-[11px] inline-flex items-center">
                <ArrowUpRight className="w-3 h-3" /> +{alternative.score_improvement.toFixed(1)}
              </span>
            </div>
          </div>
        </div>

        {/* Tier Chip & Similarity Match */}
        <div className="mb-3 flex flex-wrap items-center gap-1.5">
          {alternative.tier_badge && (
            <span
              className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                alternative.tier_badge.startsWith('Same')
                  ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                  : 'bg-indigo-50 text-indigo-800 border-indigo-200'
              }`}
            >
              {alternative.tier_badge}
            </span>
          )}
          {alternative.ingredient_similarity !== undefined && (
            <span className="text-[10px] font-semibold text-slate-500 bg-slate-100 px-2 py-0.5 rounded-full">
              {Math.round(alternative.ingredient_similarity * 100)}% Ing. Match
            </span>
          )}
        </div>

        {/* Delta Chips */}
        {deltas.length > 0 && (
          <div className="mb-3 flex flex-wrap gap-1.5">
            {deltas.slice(0, 4).map(([param, delta]) => (
              <DeltaChip
                key={param}
                parameter={param}
                delta={delta}
                unit={param === 'sodium' ? 'mg' : param === 'energy' ? 'kcal' : 'g'}
              />
            ))}
          </div>
        )}

        {/* Explanation text */}
        <p className="text-xs text-slate-600 bg-slate-50 p-2.5 rounded-lg border border-slate-100 mb-3">
          {alternative.explanation}
        </p>

        {/* Trade-off notes */}
        {alternative.trade_offs && alternative.trade_offs.length > 0 && (
          <div className="mb-3 p-2 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-800 flex items-start gap-1.5">
            <AlertTriangle className="w-3.5 h-3.5 shrink-0 text-amber-600 mt-0.5" />
            <div>
              <span className="font-bold">Trade-offs to note: </span>
              {alternative.trade_offs.join('; ')}
            </div>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex gap-2 pt-2 border-t border-slate-100">
        <Link
          to={`/products/${alternative.barcode}`}
          className="flex-1 py-2 text-center text-xs font-bold text-emerald-700 bg-emerald-50 hover:bg-emerald-100 rounded-lg transition"
        >
          View Full Analysis
        </Link>
        {onCompareToggle && (
          <button
            type="button"
            onClick={() => onCompareToggle(alternative)}
            className={`px-3 py-2 text-xs font-semibold rounded-lg border transition ${
              isComparing
                ? 'bg-slate-900 text-white border-slate-900'
                : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-50'
            }`}
          >
            {isComparing ? '✓ Comparing' : '+ Compare'}
          </button>
        )}
      </div>
    </div>
  );
};
