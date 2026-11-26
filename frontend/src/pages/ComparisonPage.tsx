import React, { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { ArrowLeft, Scale, AlertCircle, BarChart2 } from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, CartesianGrid } from 'recharts';
import { endpoints } from '../api/endpoints';
import type { ComparisonResult } from '../types';
import { ComparisonTable } from '../components/ComparisonTable';
import { LoadingSkeleton } from '../components/LoadingSkeleton';
import { ErrorState } from '../components/ErrorState';

export const ComparisonPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const idsParam = searchParams.get('ids') || searchParams.get('barcodes');

  const [comparison, setComparison] = useState<ComparisonResult | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const ids = idsParam ? idsParam.split(',').filter(Boolean) : [];

    if (ids.length < 2) {
      setError('Please select at least 2 products to compare (up to 4).');
      setLoading(false);
      return;
    }

    if (ids.length > 4) {
      setError('You can compare a maximum of 4 products at a time.');
      setLoading(false);
      return;
    }

    const fetchComparison = async () => {
      try {
        setLoading(true);
        setError(null);

        const data = await endpoints.compareProducts(ids);
        setComparison(data);
      } catch (err: any) {
        console.error(err);
        setError(err.response?.data?.detail || 'Failed to generate comparison matrix.');
      } finally {
        setLoading(false);
      }
    };

    fetchComparison();
  }, [idsParam]);

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <LoadingSkeleton rows={5} />
      </div>
    );
  }

  if (error || !comparison || comparison.products.length < 2) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <ErrorState
          title="Comparison Unavailable"
          message={error || 'Unable to build product comparison.'}
          onRetry={() => window.location.reload()}
        />
      </div>
    );
  }

  const { products } = comparison;

  // Prepare chart data for Recharts
  const chartData = [
    {
      metric: 'Project Score (0-100)',
      ...products.reduce((acc, p) => ({ ...acc, [p.product_name]: p.overall_project_score || 0 }), {})
    },
    {
      metric: 'Sugars (g/100g)',
      ...products.reduce((acc, p) => ({ ...acc, [p.product_name]: p.nutrition?.sugars_g || 0 }), {})
    },
    {
      metric: 'Sat Fat (g/100g)',
      ...products.reduce((acc, p) => ({ ...acc, [p.product_name]: p.nutrition?.saturated_fat_g || 0 }), {})
    },
    {
      metric: 'Fibre (g/100g)',
      ...products.reduce((acc, p) => ({ ...acc, [p.product_name]: p.nutrition?.fiber_g || 0 }), {})
    },
    {
      metric: 'Protein (g/100g)',
      ...products.reduce((acc, p) => ({ ...acc, [p.product_name]: p.nutrition?.proteins_g || 0 }), {})
    }
  ];

  const colors = ['#059669', '#3b82f6', '#f59e0b', '#ec4899'];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <Link
            to={`/products/${products[0].barcode}`}
            className="inline-flex items-center text-sm font-medium text-emerald-700 hover:text-emerald-800 mb-2"
          >
            <ArrowLeft className="w-4 h-4 mr-1.5" /> Back to Reference Product
          </Link>
          <h1 className="text-2xl font-black text-gray-900 flex items-center">
            <Scale className="w-6 h-6 text-emerald-600 mr-2" />
            Nutritional Comparison ({products.length} Products)
          </h1>
          <p className="text-sm text-gray-600 mt-1">
            Side-by-side assessment of overall scores, key nutrients, additives, and reference Nutri-Score grades.
          </p>
        </div>
      </div>

      {/* Main Side-by-Side Matrix */}
      <ComparisonTable comparison={comparison} />

      {/* Recharts Visual Comparison Chart */}
      <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
        <h2 className="text-lg font-bold text-gray-900 mb-1 flex items-center">
          <BarChart2 className="w-5 h-5 text-emerald-600 mr-2" />
          Nutritional Profile Overview
        </h2>
        <p className="text-xs text-gray-500 mb-6">
          Direct bar comparison of normalized project scores and key nutrient amounts (per 100g/ml).
        </p>

        <div className="h-80 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
              <XAxis dataKey="metric" tick={{ fontSize: 12, fill: '#4b5563' }} />
              <YAxis tick={{ fontSize: 12, fill: '#4b5563' }} />
              <Tooltip
                contentStyle={{ backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #e5e7eb', fontSize: '12px' }}
              />
              <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
              {products.map((p, idx) => (
                <Bar
                  key={p.product_id}
                  dataKey={p.product_name}
                  fill={colors[idx % colors.length]}
                  radius={[4, 4, 0, 0]}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Nuanced Summary Notice */}
      <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-900 flex items-start space-x-3">
        <AlertCircle className="w-5 h-5 text-emerald-700 flex-shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold block mb-0.5">Decision Guidance:</span>
          When choosing an alternative, consider not just the overall project score, but your personal dietary priorities (e.g. lowering sodium vs. cutting refined sugars vs. minimizing artificial additives).
        </div>
      </div>
    </div>
  );
};
export default ComparisonPage;
