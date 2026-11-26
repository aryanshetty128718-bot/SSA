import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';

interface ScoreBarProps {
  subScores?: Record<string, number | null>;
}

export const ScoreBar: React.FC<ScoreBarProps> = ({ subScores = {} }) => {
  const parameters = [
    { key: 'sugars', label: 'Sugars' },
    { key: 'sodium', label: 'Sodium' },
    { key: 'saturated_fat', label: 'Saturated Fat' },
    { key: 'energy', label: 'Energy Density' },
    { key: 'fiber', label: 'Dietary Fiber' },
    { key: 'proteins', label: 'Proteins' },
    { key: 'ingredient_quality', label: 'Ingredient Quality' },
    { key: 'additives', label: 'Additive Freedom' },
  ];

  const data = parameters
    .filter((p) => subScores[p.key] !== undefined && subScores[p.key] !== null)
    .map((p) => {
      const val = Math.round(subScores[p.key]!);
      return {
        name: p.label,
        score: val,
      };
    });

  const getBarColor = (val: number) => {
    if (val >= 80) return '#10b981'; // emerald
    if (val >= 65) return '#14b8a6'; // teal
    if (val >= 50) return '#f59e0b'; // amber
    if (val >= 35) return '#f97316'; // orange
    return '#ef4444'; // rose
  };

  return (
    <div className="w-full h-72">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          layout="vertical"
          margin={{ top: 10, right: 20, left: 80, bottom: 10 }}
        >
          <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e2e8f0" />
          <XAxis type="number" domain={[0, 100]} tick={{ fill: '#64748b', fontSize: 11 }} />
          <YAxis dataKey="name" type="category" tick={{ fill: '#334155', fontSize: 11, fontWeight: 500 }} />
          <Tooltip
            formatter={(value: any) => [`${value} / 100`, 'Sub-score']}
            contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', color: '#fff', borderRadius: '8px' }}
          />
          <Bar dataKey="score" radius={[0, 4, 4, 0]}>
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getBarColor(entry.score)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
