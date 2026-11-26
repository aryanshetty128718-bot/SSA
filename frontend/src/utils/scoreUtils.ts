export interface ScoreBandInfo {
  label: string;
  colorClass: string;
  bgClass: string;
  borderClass: string;
  textClass: string;
  description: string;
}

export function getScoreBand(score: number | null | undefined): ScoreBandInfo {
  if (score === null || score === undefined || score < 0) {
    return {
      label: 'Insufficient Data',
      colorClass: 'text-slate-500',
      bgClass: 'bg-slate-100',
      borderClass: 'border-slate-300',
      textClass: 'text-slate-700',
      description: 'Crucial nutritional parameters are absent from product packaging.'
    };
  }

  if (score >= 80.0) {
    return {
      label: 'Excellent Choice',
      colorClass: 'text-emerald-600',
      bgClass: 'bg-emerald-50',
      borderClass: 'border-emerald-500',
      textClass: 'text-emerald-700',
      description: 'Exemplary nutrient density with minimal negative nutrients.'
    };
  }
  if (score >= 65.0) {
    return {
      label: 'Healthy Choice',
      colorClass: 'text-teal-600',
      bgClass: 'bg-teal-50',
      borderClass: 'border-teal-500',
      textClass: 'text-teal-700',
      description: 'Balanced nutritional profile recommended for regular consumption.'
    };
  }
  if (score >= 50.0) {
    return {
      label: 'Moderate',
      colorClass: 'text-amber-600',
      bgClass: 'bg-amber-50',
      borderClass: 'border-amber-400',
      textClass: 'text-amber-700',
      description: 'Moderate nutritional balance; enjoy in reasonable portions.'
    };
  }
  if (score >= 35.0) {
    return {
      label: 'Less Healthy',
      colorClass: 'text-orange-600',
      bgClass: 'bg-orange-50',
      borderClass: 'border-orange-400',
      textClass: 'text-orange-700',
      description: 'Contains elevated sugars, saturated fat, or sodium; limit intake.'
    };
  }
  return {
    label: 'Unhealthy / Ultra-Processed',
    colorClass: 'text-rose-600',
    bgClass: 'bg-rose-50',
    borderClass: 'border-rose-500',
    textClass: 'text-rose-700',
    description: 'High levels of harmful nutrients; frequent consumption not recommended.'
  };
}

export function getNutriScoreColor(grade: string | undefined): { bg: string; text: string } {
  const g = (grade || '').toUpperCase();
  switch (g) {
    case 'A': return { bg: 'bg-[#038141]', text: 'text-white' };
    case 'B': return { bg: 'bg-[#85bb2f]', text: 'text-white' };
    case 'C': return { bg: 'bg-[#fecb02]', text: 'text-slate-900' };
    case 'D': return { bg: 'bg-[#ee8100]', text: 'text-white' };
    case 'E': return { bg: 'bg-[#e63e11]', text: 'text-white' };
    default: return { bg: 'bg-slate-300', text: 'text-slate-700' };
  }
}
