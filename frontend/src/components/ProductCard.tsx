import React from 'react';
import { Link } from 'react-router-dom';
import type { ProductSummary } from '../types';
import { getScoreBand, getNutriScoreColor } from '../utils/scoreUtils';
import { Package, Shield } from 'lucide-react';

interface ProductCardProps {
  product: ProductSummary;
  onSelectCompare?: (product: ProductSummary) => void;
  isSelectedForCompare?: boolean;
}

export const ProductCard: React.FC<ProductCardProps> = ({
  product,
  onSelectCompare,
  isSelectedForCompare = false,
}) => {
  const band = getScoreBand(product.overall_score);
  const nutriColor = getNutriScoreColor(product.nutri_score_grade);

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-xs hover:shadow-md transition flex flex-col justify-between">
      <div>
        {/* Product Image & Badges */}
        <div className="relative w-full h-40 bg-slate-50 rounded-xl overflow-hidden flex items-center justify-center mb-3">
          {product.image_url ? (
            <img
              src={product.image_url}
              alt={product.name}
              className="max-h-full max-w-full object-contain p-2"
              loading="lazy"
              onError={(e) => {
                // Fallback to placeholder on broken image
                (e.target as HTMLElement).style.display = 'none';
              }}
            />
          ) : (
            <Package className="w-12 h-12 text-slate-300" />
          )}

          {/* Nutri-Score badge top-right */}
          {product.nutri_score_grade && (
            <span
              className={`absolute top-2 right-2 text-xs font-black uppercase px-2 py-0.5 rounded shadow-xs ${nutriColor.bg} ${nutriColor.text}`}
              title={`Nutri-Score ${product.nutri_score_grade}`}
            >
              Nutri-Score {product.nutri_score_grade}
            </span>
          )}

          {/* Sample Data badge top-left */}
          {product.source === 'seed' && (
            <span className="absolute top-2 left-2 text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-100/90 text-amber-800 border border-amber-300 shadow-xs">
              Sample Data
            </span>
          )}
        </div>

        {/* Brand & Category */}
        <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1 truncate">
          {product.brand || 'Brand Unspecified'} • {product.category_name || 'Food'}
        </div>

        {/* Title */}
        <h3 className="text-sm font-bold text-slate-900 line-clamp-2 mb-2" title={product.name}>
          {product.name}
        </h3>
      </div>

      <div>
        {/* Score Pill */}
        <div className="flex items-center justify-between pt-3 border-t border-slate-100">
          <div>
            <span className="text-[10px] text-slate-400 block font-medium">Project Score</span>
            <span className={`inline-flex items-center gap-1 font-black text-sm ${band.colorClass}`}>
              <Shield className="w-3.5 h-3.5" />
              {product.overall_score !== undefined && product.overall_score !== null
                ? product.overall_score.toFixed(1)
                : 'N/A'}
            </span>
          </div>

          <Link
            to={`/product/${product.barcode}`}
            className="px-3 py-1.5 text-xs font-semibold text-emerald-700 bg-emerald-50 hover:bg-emerald-100 rounded-lg transition"
          >
            Analyze
          </Link>
        </div>

        {onSelectCompare && (
          <button
            type="button"
            onClick={() => onSelectCompare(product)}
            className={`w-full mt-2 py-1 text-xs font-medium rounded-lg border transition ${
              isSelectedForCompare
                ? 'bg-slate-900 text-white border-slate-900'
                : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-50'
            }`}
          >
            {isSelectedForCompare ? '✓ Selected to Compare' : '+ Compare'}
          </button>
        )}
      </div>
    </div>
  );
};
