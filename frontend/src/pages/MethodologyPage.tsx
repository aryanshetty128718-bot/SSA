import React from 'react';
import { BookOpen, ShieldCheck, Scale, Cpu, CheckCircle, AlertTriangle } from 'lucide-react';

export const MethodologyPage: React.FC = () => {
  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-10">
      <div>
        <h1 className="text-3xl font-black text-gray-900">Methodology & Algorithmic Provenance</h1>
        <p className="mt-2 text-base text-gray-600">
          Transparent, explainable documentation of our nutritional scoring framework, machine learning models, and official reference standards.
        </p>
      </div>

      <section className="bg-white border border-gray-200 rounded-2xl p-6 sm:p-8 shadow-sm space-y-4">
        <div className="flex items-center space-x-3 text-emerald-600">
          <Scale className="w-6 h-6" />
          <h2 className="text-xl font-bold text-gray-900">1. Project-Defined Scoring Framework (0–100)</h2>
        </div>
        <p className="text-sm text-gray-700 leading-relaxed">
          The primary score rendered by the Smart Shopping Assistant is an interpretable 0–100 continuous metric. It integrates eight distinct nutritional criteria, normalizing food quality into five intuitive color bands:
        </p>

        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 pt-2">
          <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-center">
            <span className="text-xs font-bold text-emerald-800 uppercase block">Optimal</span>
            <span className="text-lg font-black text-emerald-600">80 – 100</span>
          </div>
          <div className="p-3 bg-green-50 border border-green-200 rounded-xl text-center">
            <span className="text-xs font-bold text-green-800 uppercase block">Good</span>
            <span className="text-lg font-black text-green-600">65 – 79.9</span>
          </div>
          <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-xl text-center">
            <span className="text-xs font-bold text-yellow-800 uppercase block">Moderate</span>
            <span className="text-lg font-black text-yellow-600">50 – 64.9</span>
          </div>
          <div className="p-3 bg-orange-50 border border-orange-200 rounded-xl text-center">
            <span className="text-xs font-bold text-orange-800 uppercase block">Poor</span>
            <span className="text-lg font-black text-orange-600">35 – 49.9</span>
          </div>
          <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-center">
            <span className="text-xs font-bold text-red-800 uppercase block">Very Poor</span>
            <span className="text-lg font-black text-red-600">0 – 34.9</span>
          </div>
        </div>

        <div className="mt-4 pt-4 border-t border-gray-100 text-xs text-gray-600 space-y-2">
          <p>
            <strong>Sub-Score Parameters:</strong> Sodium/Salt, Saturated Fat, Added Sugars, Energy Density, Dietary Fibre, Protein, NOVA Ultra-Processing Index, and Food Additive Count.
          </p>
          <p>
            <strong>Version 1.1.0 Enhancements:</strong> Configurable Sugar Capping prevents high-sugar products (&gt;30g/100g) from exceeding an overall score of 39.0, unless exempted via whole dried fruit (dates, raisins) natural sugars. Beverage formulas place a 40% priority on sugar content.
          </p>
        </div>
      </section>

      <section className="bg-white border border-gray-200 rounded-2xl p-6 sm:p-8 shadow-sm space-y-4">
        <div className="flex items-center space-x-3 text-blue-600">
          <ShieldCheck className="w-6 h-6" />
          <h2 className="text-xl font-bold text-gray-900">2. Nutri-Score 2023 (Official Reference Standard)</h2>
        </div>
        <p className="text-sm text-gray-700 leading-relaxed">
          Nutri-Score is an independent, validated front-of-pack nutritional label established by Santé publique France and European health authorities. We implement the revised 2023 algorithm strictly according to official regulatory specifications.
        </p>

        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 text-xs text-blue-900 space-y-2">
          <div className="flex items-center space-x-2 font-bold">
            <CheckCircle className="w-4 h-4 text-blue-700" />
            <span>Strict Mathematical Integrity:</span>
          </div>
          <p>
            Unlike calculators that substitute 0.0 for missing values, our engine marks Nutri-Score as <strong>"Not Computable"</strong> if mandatory laboratory components (energy, sugar, saturated fat, sodium, fiber, protein) are unrecorded.
          </p>
        </div>
      </section>

      <section className="bg-white border border-gray-200 rounded-2xl p-6 sm:p-8 shadow-sm space-y-4">
        <div className="flex items-center space-x-3 text-purple-600">
          <Cpu className="w-6 h-6" />
          <h2 className="text-xl font-bold text-gray-900">3. Machine Learning Models & Categorization</h2>
        </div>
        <p className="text-sm text-gray-700 leading-relaxed">
          Machine learning assists in standardizing messy crowdsourced Open Food Facts entries without overruling verified nutritional facts:
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
          <div className="p-4 bg-gray-50 border border-gray-200 rounded-xl space-y-2">
            <span className="text-xs font-bold text-purple-700 uppercase tracking-wide">Model A: Category Classifier</span>
            <h3 className="text-sm font-bold text-gray-900">TF-IDF + LinearSVC</h3>
            <p className="text-xs text-gray-600">
              Classifies product titles and ingredients into 11 canonical project categories. Evaluated on grouped train/test splits (92.75% Top-1 Precision) ensuring zero brand contamination.
            </p>
          </div>

          <div className="p-4 bg-gray-50 border border-gray-200 rounded-xl space-y-2">
            <span className="text-xs font-bold text-purple-700 uppercase tracking-wide">Model B: Similarity & Alternatives</span>
            <h3 className="text-sm font-bold text-gray-900">Multi-Feature Cosine Matcher</h3>
            <p className="text-xs text-gray-600">
              Computes pairwise culinary similarity while enforcing a strict <strong>Category Coherence Gate</strong>. Excludes near-duplicates via GS1 manufacturer prefix matching and name stemming.
            </p>
          </div>
        </div>
      </section>

      <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-900 flex items-start space-x-3">
        <AlertTriangle className="w-5 h-5 text-amber-700 flex-shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold block mb-0.5">Academic & Educational Disclaimer:</span>
          The Smart Shopping Assistant is an academic research application. Nutritional scores, confidence ratings, and healthier alternatives are generated algorithmically for informational guidance and do not constitute clinical dietary or medical advice.
        </div>
      </div>
    </div>
  );
};
export default MethodologyPage;
