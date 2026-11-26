import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { SearchBar } from '../components/SearchBar';
import { ProductCard } from '../components/ProductCard';
import { endpoints } from '../api/endpoints';
import type { ProductSummary } from '../types';
import { Sparkles, ShieldCheck, HeartPulse, History, ArrowRight } from 'lucide-react';

export const HomePage: React.FC = () => {
  const [categories, setCategories] = useState<Array<{ id: number; name: string; slug: string }>>([]);
  const [recentBarcodes, setRecentBarcodes] = useState<string[]>([]);
  const [recentProducts, setRecentProducts] = useState<ProductSummary[]>([]);
  const [loadingRecent, setLoadingRecent] = useState(false);

  useEffect(() => {
    // Load categories
    endpoints.getCategories().then((cats) => setCategories(cats.slice(0, 8))).catch(() => {});

    // Load recent searches from localStorage
    const saved = localStorage.getItem('ssa_recent_searches');
    if (saved) {
      try {
        const barcodes: string[] = JSON.parse(saved);
        setRecentBarcodes(barcodes.slice(0, 4));
      } catch {}
    }
  }, []);

  // Fetch product summaries for recent barcodes
  useEffect(() => {
    if (recentBarcodes.length > 0) {
      setLoadingRecent(true);
      Promise.all(
        recentBarcodes.map((bc) =>
          endpoints.getProductByBarcode(bc).then((res) => res.product || res).catch(() => null)
        )
      ).then((prods) => {
        setRecentProducts(prods.filter((p): p is ProductSummary => p !== null));
        setLoadingRecent(false);
      });
    }
  }, [recentBarcodes]);

  return (
    <div className="space-y-12 py-8 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      {/* Hero Section */}
      <section className="text-center space-y-4 max-w-3xl mx-auto pt-6">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-50 text-emerald-800 text-xs font-bold border border-emerald-200">
          <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
          <span>AI-Powered Food & Beverage Health Intelligence</span>
        </div>
        <h1 className="text-3xl sm:text-5xl font-black text-slate-900 tracking-tight leading-tight">
          Unmask Ultra-Processed Food. <br />
          <span className="text-emerald-600">Discover Healthier Alternatives.</span>
        </h1>
        <p className="text-slate-600 text-sm sm:text-base leading-relaxed">
          Evaluate groceries through a transparent dual-layer framework: the official{' '}
          <strong className="text-slate-900 font-semibold">Nutri-Score 2023</strong> reference standard combined with our{' '}
          <strong className="text-slate-900 font-semibold">0–100 Proposed Project Score</strong> with dynamic missing-data handling and ML alternative retrieval.
        </p>

        {/* Search Bar */}
        <div className="pt-4">
          <SearchBar />
        </div>
      </section>

      {/* Feature Pillars */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-4">
        <div className="p-5 bg-white border border-slate-200 rounded-2xl shadow-xs">
          <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center mb-3">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <h3 className="font-bold text-slate-900 text-sm mb-1">Dual-Layer Scientific Scoring</h3>
          <p className="text-xs text-slate-600 leading-relaxed">
            Side-by-side assessment pairing statutory Nutri-Score 2023 with our continuous 0-100 framework with dynamic missing-data renormalization.
          </p>
        </div>

        <div className="p-5 bg-white border border-slate-200 rounded-2xl shadow-xs">
          <div className="w-10 h-10 rounded-xl bg-indigo-100 text-indigo-700 flex items-center justify-center mb-3">
            <Sparkles className="w-5 h-5" />
          </div>
          <h3 className="font-bold text-slate-900 text-sm mb-1">Multimodal Machine Learning</h3>
          <p className="text-xs text-slate-600 leading-relaxed">
            TF-IDF semantic analysis and 7-dimensional standardized nutrient proximity for genuine category-coherent healthier alternatives.
          </p>
        </div>

        <div className="p-5 bg-white border border-slate-200 rounded-2xl shadow-xs">
          <div className="w-10 h-10 rounded-xl bg-teal-100 text-teal-700 flex items-center justify-center mb-3">
            <HeartPulse className="w-5 h-5" />
          </div>
          <h3 className="font-bold text-slate-900 text-sm mb-1">Trade-Off Guard & Transparency</h3>
          <p className="text-xs text-slate-600 leading-relaxed">
            Every alternative provides granular +/- deltas on sugar, saturated fat, and sodium, flagging compromises before you buy.
          </p>
        </div>
      </section>

      {/* Recently Analysed Products */}
      {recentProducts.length > 0 && (
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <History className="w-5 h-5 text-emerald-600" />
              Recently Analysed Products
            </h2>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {recentProducts.map((p) => (
              <ProductCard key={p.id} product={p} />
            ))}
          </div>
        </section>
      )}

      {/* Categories Grid */}
      {categories.length > 0 && (
        <section className="space-y-4">
          <h2 className="text-lg font-bold text-slate-900">Explore Catalog by Category</h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {categories.map((cat) => (
              <Link
                key={cat.id}
                to={`/search?q=${encodeURIComponent(cat.name)}`}
                className="p-4 bg-white border border-slate-200 rounded-xl hover:border-emerald-500 hover:shadow-xs transition text-center group"
              >
                <div className="text-xs font-bold text-slate-800 group-hover:text-emerald-700">
                  {cat.name}
                </div>
                <div className="text-[10px] text-slate-400 capitalize mt-0.5">{cat.slug.replace(/-/g, ' ')}</div>
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* Demonstration Barcode Quick Links */}
      <section className="p-6 bg-slate-900 text-white rounded-2xl shadow-sm space-y-3">
        <h3 className="text-sm font-bold text-emerald-400 uppercase tracking-wider">
          Quick Demonstration Barcodes (Real Open Food Facts Records)
        </h3>
        <p className="text-xs text-slate-300">
          Click any verified live product to test real-time analysis, sub-scores, radar visuals, and alternatives:
        </p>
        <div className="flex flex-wrap gap-2 pt-1">
          {[
            { name: 'Nutella (Hazelnut Spread)', bc: '3017620422003' },
            { name: 'Coca-Cola Original 1.5L', bc: '5449000000996' },
            { name: 'Britannia Marie Gold', bc: '8901063162914' },
            { name: 'Kellogg\'s Corn Flakes', bc: '5000127003884' },
            { name: 'Quaker Whole Oats', bc: '8901058800012' },
          ].map((item) => (
            <Link
              key={item.bc}
              to={`/product/${item.bc}`}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-emerald-300 rounded-lg border border-slate-700 transition"
            >
              <span>{item.name}</span>
              <ArrowRight className="w-3 h-3 text-emerald-400" />
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
};
