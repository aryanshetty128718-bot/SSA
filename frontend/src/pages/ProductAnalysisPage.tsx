import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { endpoints } from '../api/endpoints';
import type { ProductAnalysis } from '../types';
import { ScoreGauge } from '../components/ScoreGauge';
import { ScoreRadar } from '../components/ScoreRadar';
import { ScoreBar } from '../components/ScoreBar';
import { NutritionTable } from '../components/NutritionTable';
import { ProsCons } from '../components/ProsCons';
import { NutriScoreBadge } from '../components/NutriScoreBadge';
import { CompletenessBadge } from '../components/CompletenessBadge';
import { LoadingSkeleton } from '../components/LoadingSkeleton';
import { ErrorState } from '../components/ErrorState';
import { ManualEntryForm } from '../components/ManualEntryForm';
import { useAuth } from '../contexts/AuthContext';
import {
  Package,
  Sparkles,
  Bookmark,
  Share2,
  ExternalLink,
  Cpu,
  Info,
  Layers,
  ArrowRight,
  AlertCircle
} from 'lucide-react';

export const ProductAnalysisPage: React.FC = () => {
  const { barcode } = useParams<{ barcode: string }>();
  const [analysis, setAnalysis] = useState<ProductAnalysis | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'nutrition' | 'ingredients' | 'ml'>('overview');
  const [savedSuccess, setSavedSuccess] = useState<string | null>(null);
  const [showManualForm, setShowManualForm] = useState<boolean>(false);
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    if (!barcode) return;
    setLoading(true);
    setError(null);

    // Save barcode to recent searches in localStorage
    const saved = localStorage.getItem('ssa_recent_searches');
    let recent: string[] = saved ? JSON.parse(saved) : [];
    recent = [barcode, ...recent.filter((b) => b !== barcode)].slice(0, 10);
    localStorage.setItem('ssa_recent_searches', JSON.stringify(recent));

    endpoints
      .getProductByBarcode(barcode)
      .then((res) => {
        const prod = res.product || res;
        const prodId = prod.id || barcode;
        return endpoints.getProductAnalysis(prodId).then((data) => ({
          ...data,
          source: data.source || prod.source,
          nutrition: data.nutrition || prod.nutrition,
          ingredients: (data.ingredients && data.ingredients.length > 0) ? data.ingredients : (prod.ingredients || []),
        }));
      })
      .then((merged) => {
        setAnalysis(merged);
        setLoading(false);
      })
      .catch((err) => {
        const errorDetail = err.response?.data?.detail;
        const msg = typeof errorDetail === 'object' && errorDetail !== null
          ? (errorDetail.message || JSON.stringify(errorDetail))
          : (typeof errorDetail === 'string' ? errorDetail : (err.message || 'Failed to retrieve product analysis'));
        setError(msg);
        setLoading(false);
      });
  }, [barcode]);

  const handleSaveProduct = async () => {
    if (!analysis || !isAuthenticated) return;
    try {
      await endpoints.saveProduct(analysis.product_id, 'Bookmarked from product analysis');
      setSavedSuccess('Product saved to your bookmarks!');
      setTimeout(() => setSavedSuccess(null), 3000);
    } catch {
      setSavedSuccess('Could not save product');
    }
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">
        <LoadingSkeleton rows={6} />
      </div>
    );
  }

  if (error || !analysis) {
    if (showManualForm || (error && (error.toLowerCase().includes('not found') || error.toLowerCase().includes('database')))) {
      return (
        <div className="max-w-4xl mx-auto px-4 py-12 space-y-6">
          <ManualEntryForm
            barcode={barcode || ''}
            onSuccess={(prod) => {
              endpoints.getProductAnalysis(prod.id || barcode!).then((ana) => {
                setAnalysis({
                  ...ana,
                  source: prod.source || 'user_entered',
                  nutrition: ana.nutrition || prod.nutrition,
                  ingredients: ana.ingredients || prod.ingredients || []
                });
                setError(null);
                setShowManualForm(false);
              });
            }}
            onCancel={() => setShowManualForm(false)}
          />
        </div>
      );
    }

    return (
      <div className="max-w-2xl mx-auto px-4 py-16 space-y-4">
        <ErrorState
          title="Product Analysis Unavailable"
          message={error || 'Could not load product analysis for this barcode.'}
          onRetry={() => window.location.reload()}
        />
        <div className="text-center pt-2">
          <button
            type="button"
            onClick={() => setShowManualForm(true)}
            className="inline-flex items-center gap-1.5 px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-xl shadow-xs transition"
          >
            Enter Product Manually
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Top Header Card */}
      <section className="bg-white border border-slate-200 rounded-3xl p-6 sm:p-8 shadow-xs">
        <div className="flex flex-col lg:flex-row gap-8 items-start lg:items-center justify-between">
          {/* Product Image & Details */}
          <div className="flex flex-col sm:flex-row gap-6 items-start sm:items-center">
            <div className="w-32 h-32 bg-slate-50 border border-slate-200 rounded-2xl flex items-center justify-center p-2 shrink-0">
              {analysis.image_url ? (
                <img
                  src={analysis.image_url}
                  alt={analysis.product_name}
                  className="max-h-full max-w-full object-contain"
                  onError={(e) => {
                    (e.target as HTMLElement).style.display = 'none';
                  }}
                />
              ) : (
                <Package className="w-12 h-12 text-slate-300" />
              )}
            </div>

            <div className="space-y-2">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                  {analysis.brand || 'Brand Unspecified'}
                </span>
                <span className="text-xs px-2.5 py-0.5 rounded-full font-semibold bg-slate-100 text-slate-700 capitalize">
                  {analysis.product_type}
                </span>
                <span className="text-xs px-2.5 py-0.5 rounded-full font-mono bg-slate-100 text-slate-600">
                  Barcode: {analysis.barcode}
                </span>
                {analysis.source === 'seed' && (
                  <span className="text-xs px-2.5 py-0.5 rounded-full font-bold bg-amber-100 text-amber-800 border border-amber-300">
                    Sample Data (synthetic, for testing)
                  </span>
                )}
                {analysis.source === 'user_entered' && (
                  <span className="text-xs px-2.5 py-0.5 rounded-full font-bold bg-purple-100 text-purple-900 border border-purple-300 flex items-center gap-1">
                    <AlertCircle className="w-3.5 h-3.5 text-purple-700" />
                    Entered by a user; not verified
                  </span>
                )}
                {analysis.source === 'usda' && (
                  <span className="text-xs px-2.5 py-0.5 rounded-full font-bold bg-blue-100 text-blue-900 border border-blue-300">
                    USDA FoodData Central
                  </span>
                )}
              </div>

              <h1 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
                {analysis.product_name}
              </h1>

              <div className="flex flex-wrap items-center gap-4 pt-1">
                <NutriScoreBadge
                  grade={analysis.official_reference?.grade}
                  points={analysis.official_reference?.points}
                  status={analysis.official_reference?.status}
                  missingInputs={analysis.official_reference?.missing_inputs}
                  size="md"
                />

                <CompletenessBadge
                  score={analysis.confidence_score}
                  level={analysis.confidence_level}
                  missingParameters={analysis.missing_parameters}
                />

                {analysis.confidence_score !== undefined && analysis.confidence_score < 0.50 && (
                  <span
                    className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full font-bold bg-amber-100 text-amber-900 border border-amber-300 shadow-xs"
                    title="Computed via dynamic weight renormalization over available nutrients"
                  >
                    <AlertCircle className="w-3.5 h-3.5 text-amber-700" />
                    Provisional Score
                  </span>
                )}

                <Link
                  to="/methodology"
                  className="text-[11px] font-mono text-slate-500 hover:text-emerald-700 bg-slate-50 px-2 py-1 rounded border border-slate-200 transition"
                  title="View scoring methodology & changelog"
                >
                  Scoring Engine v{analysis.scoring_engine_version || '1.1.0'}
                </Link>
              </div>
            </div>
          </div>

          {/* Overall Project Score Gauge */}
          <div className="flex flex-col items-center justify-center bg-slate-50/80 p-4 rounded-2xl border border-slate-100 w-full lg:w-auto shrink-0">
            <ScoreGauge score={analysis.overall_project_score} size="lg" />
            
            <div className="mt-2 flex gap-2 w-full">
              <Link
                to={`/alternatives/${analysis.barcode}`}
                className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-xl shadow-xs transition"
              >
                <Sparkles className="w-4 h-4" />
                Find Healthier Alternatives
              </Link>
              {isAuthenticated && (
                <button
                  type="button"
                  onClick={handleSaveProduct}
                  className="px-3 py-2.5 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-xl transition"
                  title="Bookmark Product"
                >
                  <Bookmark className="w-4 h-4 text-emerald-600" />
                </button>
              )}
            </div>
            {savedSuccess && (
              <span className="text-xs text-emerald-600 font-semibold mt-1.5">{savedSuccess}</span>
            )}
          </div>
        </div>
      </section>

      {/* Tabs Navigation */}
      <section className="space-y-6">
        <div className="flex border-b border-slate-200 space-x-8">
          {[
            { id: 'overview', label: 'Score Analysis & Radar' },
            { id: 'nutrition', label: 'Nutrition Facts (per 100g/ml)' },
            { id: 'ingredients', label: 'Ingredients & Additives' },
            { id: 'ml', label: 'ML Model Insights' },
          ].map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id as any)}
              className={`pb-3 text-sm font-bold border-b-2 transition ${
                activeTab === tab.id
                  ? 'border-emerald-600 text-emerald-700'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab 1: Overview (Radar, Bar, Pros/Cons) */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Radar Chart Card */}
              <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="font-bold text-slate-900 text-sm">8-Parameter Nutritional Radar</h3>
                    <p className="text-xs text-slate-400">Balanced sub-scores across positive & negative criteria</p>
                  </div>
                  <span className="text-[10px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                    Proposed Framework
                  </span>
                </div>
                <ScoreRadar subScores={analysis.sub_scores} />
              </div>

              {/* Bar Chart Card */}
              <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="font-bold text-slate-900 text-sm">Sub-Scores Breakdown</h3>
                    <p className="text-xs text-slate-400">Continuous 0-100 values with traffic-light thresholds</p>
                  </div>
                  <span className="text-[10px] font-semibold text-slate-500">
                    Max: 100
                  </span>
                </div>
                <ScoreBar subScores={analysis.sub_scores} />
              </div>
            </div>

            {/* Pros and Cons Highlights */}
            <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs">
              <ProsCons pros={analysis.pros} cons={analysis.cons} />
            </div>
          </div>
        )}

        {/* Tab 2: Nutrition Table */}
        {activeTab === 'nutrition' && (
          <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-4">
            <h3 className="font-bold text-slate-900 text-sm">Declared Nutritional Declaration</h3>
            <NutritionTable nutrition={analysis.nutrition} productType={analysis.product_type} />
          </div>
        )}

        {/* Tab 3: Ingredients & Additives */}
        {activeTab === 'ingredients' && (
          <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-4">
            <h3 className="font-bold text-slate-900 text-sm">Ingredient Hierarchy & Additives</h3>
            {analysis.ingredients && analysis.ingredients.length > 0 ? (
              <div className="space-y-3">
                <div className="flex flex-wrap gap-2">
                  {analysis.ingredients.map((ing, i) => (
                    <span
                      key={i}
                      className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-medium border ${
                        ing.is_additive
                          ? 'bg-amber-50 text-amber-900 border-amber-200'
                          : ing.is_whole_grain
                          ? 'bg-emerald-50 text-emerald-900 border-emerald-200'
                          : 'bg-slate-50 text-slate-700 border-slate-200'
                      }`}
                    >
                      <span>{ing.canonical_name || (ing as any).ingredient_name || 'Ingredient'}</span>
                      {ing.ins_number && (
                        <span className="font-mono text-[10px] bg-white px-1 rounded text-amber-700">
                          {ing.ins_number}
                        </span>
                      )}
                    </span>
                  ))}
                </div>
                <p className="text-xs text-slate-500 pt-2">
                  * Note: Additives (INS/E-numbers) are neutrally highlighted based on statutory food additive indexes without toxicological harm claims.
                </p>
              </div>
            ) : (
              <p className="text-xs text-slate-400 italic">No ingredient list declared for this barcode record.</p>
            )}
          </div>
        )}

        {/* Tab 4: ML Model Insights */}
        {activeTab === 'ml' && (
          <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-4">
            <div className="flex items-center gap-2">
              <Cpu className="w-5 h-5 text-indigo-600" />
              <h3 className="font-bold text-slate-900 text-sm">Machine Learning Intelligence Architecture</h3>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-2">
                <span className="font-bold text-indigo-900 block">Model A: Multimodal Category Classifier</span>
                <p className="text-slate-600">
                  Combines sublinear TF-IDF character/word n-grams with 7-dimensional standardized nutrient features. Evaluated via GroupShuffleSplit to avoid near-duplicate data leakage.
                </p>
                <div className="pt-1">
                  <span className="inline-block bg-indigo-100 text-indigo-800 px-2 py-0.5 rounded font-mono text-[11px]">
                    Label: ML Prediction
                  </span>
                </div>
              </div>

              <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-2">
                <span className="font-bold text-indigo-900 block">Model B: Multimodal Similarity Retrieval</span>
                <p className="text-slate-600">
                  Calculates true pairwise TF-IDF cosine similarity combined with standardized nutrient Euclidean distance without artificial score floors.
                </p>
                <div className="pt-1">
                  <span className="inline-block bg-indigo-100 text-indigo-800 px-2 py-0.5 rounded font-mono text-[11px]">
                    Minimum Similarity: 0.05 (Calibrated)
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}
      </section>

      {/* Disclaimers & Methodology Link */}
      <footer className="pt-4 border-t border-slate-200 text-center space-y-2">
        <p className="text-xs text-slate-500 font-medium">
          Disclaimer: Scores and recommendations are informational and do not constitute clinical or medical advice.
        </p>
        <p className="text-xs text-slate-400">
          Want to know how scores are calculated? Read our transparent{' '}
          <Link to="/methodology" className="text-emerald-600 hover:underline font-semibold">
            Proposed Project Scoring Methodology
          </Link>
          .
        </p>
      </footer>
    </div>
  );
};
