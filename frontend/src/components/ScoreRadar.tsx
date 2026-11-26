import React from 'react';
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';

interface ScoreRadarProps {
  subScores?: Record<string, number | null>;
}

export const ScoreRadar: React.FC<ScoreRadarProps> = ({ subScores = {} }) => {
  const parameters = [
    { key: 'sugars', label: 'Sugars' },
    { key: 'sodium', label: 'Sodium' },
    { key: 'saturated_fat', label: 'Sat. Fat' },
    { key: 'energy', label: 'Energy' },
    { key: 'fiber', label: 'Fiber' },
    { key: 'proteins', label: 'Protein' },
    { key: 'ingredient_quality', label: 'Ingredients' },
    { key: 'additives', label: 'Additives' },
  ];

  const data = parameters.map((param) => ({
    parameter: param.label,
    score: subScores[param.key] !== undefined && subScores[param.key] !== null ? Math.round(subScores[param.key]!) : 0,
    fullMark: 100,
  }));

  return (
    <div className="w-full h-72 flex flex-col items-center">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart cx="50%" cy="50%" outerRadius="75%" data={data}>
          <PolarGrid stroke="#e2e8f0" />
          <PolarAngleAxis dataKey="parameter" tick={{ fill: '#475569', fontSize: 11, fontWeight: 500 }} />
          <PolarRadiusAxis angle={30} domain={[0, 100]} stroke="#cbd5e1" tick={{ fill: '#94a3b8', fontSize: 9 }} />
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const item = payload[0].payload;
                return (
                  <div className="bg-slate-900 text-white text-xs px-3 py-1.5 rounded-lg shadow-lg">
                    <p className="font-semibold">{item.parameter}</p>
                    <p className="text-emerald-400">Sub-Score: {item.score} / 100</p>
                  </div>
                );
              }
              return null;
            }}
          />
          <Radar
            name="Score"
            dataKey="score"
            stroke="#10b981"
            fill="#10b981"
            fillOpacity={0.45}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
};
