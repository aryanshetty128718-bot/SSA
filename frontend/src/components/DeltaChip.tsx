import React from 'react';
import { ArrowDownRight, ArrowUpRight, Minus } from 'lucide-react';

interface DeltaChipProps {
  parameter: string;
  delta: number;
  unit?: string;
}

export const DeltaChip: React.FC<DeltaChipProps> = ({
  parameter,
  delta,
  unit = 'g',
}) => {
  // Parameters where higher is WORSE (negative nutrients)
  const isNegativeNutrient = ['sugars', 'saturated_fat', 'sodium', 'energy', 'energy_kcal'].includes(parameter);

  const absDelta = Math.abs(delta);
  const formattedVal = absDelta < 1 ? absDelta.toFixed(2) : absDelta.toFixed(1);

  if (Math.abs(delta) < 0.01) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-600 border border-slate-200">
        <Minus className="w-3 h-3" />
        <span className="capitalize">{parameter.replace('_', ' ')}: unchanged</span>
      </span>
    );
  }

  // If negative nutrient decreased -> GREEN (good)
  // If negative nutrient increased -> RED (bad)
  // If positive nutrient (fiber, protein) increased -> GREEN (good)
  // If positive nutrient decreased -> RED (bad)
  const isHealthyGain = isNegativeNutrient ? delta < 0 : delta > 0;

  const colorClasses = isHealthyGain
    ? 'bg-emerald-50 text-emerald-800 border-emerald-300'
    : 'bg-rose-50 text-rose-800 border-rose-300';

  const Icon = delta > 0 ? ArrowUpRight : ArrowDownRight;
  const sign = delta > 0 ? '+' : '-';

  return (
    <span
      className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold border shadow-xs ${colorClasses}`}
      aria-label={`${parameter} difference: ${sign}${formattedVal}${unit}`}
    >
      <Icon className="w-3.5 h-3.5" />
      <span className="capitalize">{parameter.replace('_', ' ')}:</span>
      <span>{sign}{formattedVal}{unit}</span>
    </span>
  );
};
