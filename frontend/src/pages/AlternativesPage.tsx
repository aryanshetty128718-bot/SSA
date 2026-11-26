import React, { useEffect, useState } from 'react';
import { useSearchParams, useParams, Link, useNavigate } from 'react-router-dom';
import { Sparkles, ArrowLeft, AlertCircle, Scale, ExternalLink } from 'lucide-react';
import { endpoints } from '../api/endpoints';
import type { ProductAnalysis, AlternativeItem } from '../types';
import { AlternativeCard } from '../components/AlternativeCard';
import { LoadingSkeleton } from '../components/LoadingSkeleton';
import { ErrorState } from '../components/ErrorState';
import { EmptyState } from '../components/EmptyState';

export const AlternativesPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const params = useParams<{ barcode?: string }>();
  const navigate = useNavigate();

  const barcode = params.barcode || searchParams.get('barcode') || '';

  const [analysis, setAnalysis] = useState<ProductAnalysis | null>(null);
  const [alternatives, setAlternatives] = useState<AlternativeItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedForCompare, setSelectedForCompare] = useState<string[]>([]);

  useEffect(() => {
    if (!barcode) {
      setError('No product barcode specified.');
      setLoading(false);
      return;
    }

    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        const prodRes = await endpoints.getProductByBarcode(barcode);
        const prodId = prodRes.product?.id || prodRes.id || barcode;
        const [analysisRes, recoRes] = await Promise.all([
          endpoints.getProductAnalysis(prodId),
          endpoints.getAlternatives(prodId, 6)
        ]);

        setAnalysis(analysisRes);
        setAlternatives(recoRes.recommendations || []);
        setSelectedForCompare([prodId]);
      } catch (err: any) {
        console.error(err);
        setError(err.response?.data?.detail || 'Failed to load recommendations. Please verify the barcode.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [barcode]);

  const toggleCompare = (alt: AlternativeItem) => {
    setSelectedForCompare((prev) => {
      if (prev.includes(alt.id)) {
        return prev.filter((id) => id !== alt.id);
      } else {
        if (prev.length >= 4) {
          alert('You can compare a maximum of 4 products at once.');
          return prev;
        }
        return [...prev, alt.id];
      }
    });
  };

  const handleLaunchCompare = () => {
    if (selectedForCompare.length < 2) {
      alert('Please select at least 2 products to compare.');
      return;
    }
    navigate(`/compare?ids=${selectedForCompare.join(',')}`);
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <LoadingSkeleton rows={4} />
      </div>
    );
  }

  if (error || !analysis) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <ErrorState
          title="Could Not Load Alternatives"
          message={error || 'Product information unavailable.'}
          onRetry={() => window.location.reload()}
        />
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Navigation header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <Link
          to={`/products/${analysis.barcode}`}
          className="inline-flex items-center text-sm font-medium text-emerald-700 hover:text-emerald-800"
        >
          <ArrowLeft className="w-4 h-4 mr-1.5" /> Back to Product Analysis
        </Link>

        {selectedForCompare.length > 1 && (
          <button
            onClick={handleLaunchCompare}
            className="inline-flex items-center px-4 py-2 bg-emerald-600 text-white text-sm font-medium rounded-lg shadow-sm hover:bg-emerald-700 transition-colors"
          >
            <Scale className="w-4 h-4 mr-2" />
            Compare Selected ({selectedForCompare.length})
          </button>
        )}
      </div>

      {/* Query Product Summary Card */}
      <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center space-x-4">
            <div className="w-16 h-16 bg-gray-50 border border-gray-100 rounded-lg flex items-center justify-center p-2 flex-shrink-0">
              {analysis.image_url ? (
                <img src={analysis.image_url} alt={analysis.product_name} className="max-h-full max-w-full object-contain" />
              ) : (
                <span className="text-xs text-gray-400">No Image</span>
              )}
            </div>
            <div>
              <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
                Reference Product (Current Selection)
              </span>
              <h1 className="text-xl font-bold text-gray-900">{analysis.product_name}</h1>
              <p className="text-sm text-gray-600">
                {analysis.brand || 'Unknown Brand'} • Barcode: <span className="font-mono text-gray-800">{analysis.barcode}</span>
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-6 border-t sm:border-t-0 pt-3 sm:pt-0 w-full sm:w-auto justify-between sm:justify-end">
            <div className="text-center sm:text-right">
              <span className="text-xs text-gray-500 block">Current Project Score</span>
              <span className="text-2xl font-black text-gray-900">
                {analysis.overall_project_score?.toFixed(1) ?? 'N/A'}
                <span className="text-xs font-normal text-gray-500"> / 100</span>
              </span>
            </div>
            <div className="text-center sm:text-right">
              <span className="text-xs text-gray-500 block">Nutri-Score</span>
              <span className="inline-block px-2.5 py-0.5 rounded text-sm font-bold bg-gray-100 text-gray-800 uppercase">
                {analysis.official_reference?.grade || 'N/A'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Recommendations Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-gray-900 flex items-center">
              <Sparkles className="w-5 h-5 text-emerald-600 mr-2" />
              Healthier Category-Coherent Alternatives
            </h2>
            <p className="text-sm text-gray-600">
              Ranked by nutritional improvement within the same or closely related culinary category.
            </p>
          </div>
          <span className="text-xs font-medium text-gray-500 bg-gray-100 px-2.5 py-1 rounded-full">
            {alternatives.length} {alternatives.length === 1 ? 'Alternative' : 'Alternatives'} Found
          </span>
        </div>

        {alternatives.length === 0 ? (
          <EmptyState
            title="No Healthier Alternatives Found"
            description="We could not find any products in the same category with a strictly higher score or sufficient data completeness."
            actionText="Explore All Products"
            onAction={() => navigate('/')}
          />
        ) : (
          <div className="space-y-4">
            {alternatives.length < 3 && (
              <div className="flex items-center p-3 bg-amber-50 border border-amber-200 rounded-lg text-amber-800 text-xs">
                <AlertCircle className="w-4 h-4 mr-2 flex-shrink-0" />
                <span>
                  Fewer than 3 healthier alternatives were found matching strict category coherence and nutritional improvement criteria.
                </span>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {alternatives.map((alt) => (
                <AlternativeCard
                  key={alt.id}
                  alternative={alt}
                  onCompareToggle={toggleCompare}
                  isComparing={selectedForCompare.includes(alt.id)}
                />
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Methodology notice */}
      <div className="p-4 bg-gray-50 border border-gray-200 rounded-xl text-xs text-gray-600 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
        <span>
          <strong>Category Coherence Guard:</strong> Alternatives are restricted to products within the same project category or documented culinary equivalents. Cross-category leaps (e.g. gum for sweet spreads) are strictly prevented.
        </span>
        <Link to="/methodology" className="inline-flex items-center text-emerald-700 hover:text-emerald-800 font-medium whitespace-nowrap">
          Learn More <ExternalLink className="w-3 h-3 ml-1" />
        </Link>
      </div>
    </div>
  );
};
export default AlternativesPage;
