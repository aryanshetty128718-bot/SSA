import React from 'react';
import type { NutritionInfo } from '../types';

interface NutritionTableProps {
  nutrition?: NutritionInfo;
  productType?: 'solid' | 'beverage';
}

export const NutritionTable: React.FC<NutritionTableProps> = ({
  nutrition,
  productType = 'solid',
}) => {
  if (!nutrition) {
    return <div className="text-sm text-slate-500 italic p-4">No nutritional data declared for this product.</div>;
  }

  const basisLabel = productType === 'beverage' ? 'per 100 ml' : 'per 100 g';

  const rows = [
    { label: 'Energy', val: nutrition.energy_kcal !== undefined ? `${nutrition.energy_kcal} kcal` : null },
    { label: 'Sugars', val: nutrition.sugars_g !== undefined ? `${nutrition.sugars_g} g` : null, highlight: (nutrition.sugars_g || 0) > 22.5 },
    { label: 'Saturated Fat', val: nutrition.saturated_fat_g !== undefined ? `${nutrition.saturated_fat_g} g` : null, highlight: (nutrition.saturated_fat_g || 0) > 5.0 },
    { label: 'Total Fat', val: nutrition.fat_g !== undefined ? `${nutrition.fat_g} g` : null },
    { label: 'Sodium', val: nutrition.sodium_mg !== undefined ? `${nutrition.sodium_mg} mg` : null, highlight: (nutrition.sodium_mg || 0) > 600 },
    { label: 'Salt (derived)', val: nutrition.salt_g !== undefined ? `${nutrition.salt_g} g` : null },
    { label: 'Dietary Fiber', val: nutrition.fiber_g !== undefined ? `${nutrition.fiber_g} g` : null, positive: (nutrition.fiber_g || 0) >= 6.0 },
    { label: 'Proteins', val: nutrition.proteins_g !== undefined ? `${nutrition.proteins_g} g` : null, positive: (nutrition.proteins_g || 0) >= 10.0 },
    { label: 'Carbohydrates', val: nutrition.carbohydrates_g !== undefined ? `${nutrition.carbohydrates_g} g` : null },
  ];

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-xs">
      <table className="w-full text-left text-sm">
        <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200">
          <tr>
            <th className="py-3 px-4">Nutrient</th>
            <th className="py-3 px-4 text-right">Quantity ({basisLabel})</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {rows.map((r, i) => (
            <tr key={i} className="hover:bg-slate-50/50">
              <td className="py-2.5 px-4 font-medium text-slate-700">{r.label}</td>
              <td className="py-2.5 px-4 text-right">
                {r.val !== null ? (
                  <span
                    className={`inline-block font-mono ${
                      r.highlight
                        ? 'text-rose-600 font-bold'
                        : r.positive
                        ? 'text-emerald-600 font-bold'
                        : 'text-slate-800'
                    }`}
                  >
                    {r.val}
                  </span>
                ) : (
                  <span className="text-slate-400 text-xs italic">Not declared</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
