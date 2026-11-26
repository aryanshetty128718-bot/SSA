import React, { useState, useEffect } from 'react';
import { endpoints } from '../api/endpoints';
import { AlertCircle, PlusCircle, CheckCircle } from 'lucide-react';

interface ManualEntryFormProps {
  barcode: string;
  onSuccess: (product: any) => void;
  onCancel?: () => void;
}

export const ManualEntryForm: React.FC<ManualEntryFormProps> = ({
  barcode,
  onSuccess,
  onCancel,
}) => {
  const [categories, setCategories] = useState<Array<{ id: number; name: string }>>([]);
  const [name, setName] = useState('');
  const [brand, setBrand] = useState('');
  const [categoryId, setCategoryId] = useState<number | ''>('');
  const [servingBasis, setServingBasis] = useState<'per 100g' | 'per 100ml'>('per 100g');
  const [servingSize, setServingSize] = useState('');
  
  // Nutrients
  const [energyKcal, setEnergyKcal] = useState<string>('');
  const [carbs, setCarbs] = useState<string>('');
  const [sugars, setSugars] = useState<string>('');
  const [fat, setFat] = useState<string>('');
  const [satFat, setSatFat] = useState<string>('');
  const [fiber, setFiber] = useState<string>('');
  const [protein, setProtein] = useState<string>('');
  const [salt, setSalt] = useState<string>('');
  const [ingredientsText, setIngredientsText] = useState('');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    endpoints.getCategories().then((data) => {
      setCategories(data);
      if (data.length > 0) {
        setCategoryId(data[0].id);
      }
    }).catch(() => {});
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!name.trim()) {
      setError('Product name is required.');
      return;
    }
    if (!categoryId) {
      setError('Please select a category.');
      return;
    }

    const nCarbs = carbs ? parseFloat(carbs) : null;
    const nSugars = sugars ? parseFloat(sugars) : null;
    if (nSugars !== null && nCarbs !== null && nSugars > nCarbs) {
      setError(`Sugars (${nSugars}g) cannot exceed total carbohydrates (${nCarbs}g).`);
      return;
    }

    const nFat = fat ? parseFloat(fat) : null;
    const nSatFat = satFat ? parseFloat(satFat) : null;
    if (nSatFat !== null && nFat !== null && nSatFat > nFat) {
      setError(`Saturated fat (${nSatFat}g) cannot exceed total fat (${nFat}g).`);
      return;
    }

    const payload = {
      barcode: barcode.trim(),
      name: name.trim(),
      brand: brand.trim() || undefined,
      category_id: Number(categoryId),
      serving_basis: servingBasis,
      serving_size: servingSize.trim() || undefined,
      energy_kcal: energyKcal ? parseFloat(energyKcal) : null,
      carbohydrates_g: nCarbs,
      sugars_g: nSugars,
      fat_g: nFat,
      saturated_fat_g: nSatFat,
      fiber_g: fiber ? parseFloat(fiber) : null,
      proteins_g: protein ? parseFloat(protein) : null,
      salt_g: salt ? parseFloat(salt) : null,
      ingredients_text: ingredientsText.trim() || undefined,
    };

    setLoading(true);
    try {
      const res = await endpoints.submitManualEntry(payload);
      onSuccess(res);
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : (detail?.[0]?.msg || 'Validation failed. Please verify input ranges.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-3xl p-6 sm:p-8 shadow-md max-w-2xl mx-auto space-y-6">
      <div className="flex items-start justify-between border-b border-slate-100 pb-4">
        <div>
          <span className="text-xs font-bold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full uppercase tracking-wider">
            Catalogue Fallback
          </span>
          <h2 className="text-xl sm:text-2xl font-black text-slate-900 mt-1">
            Manual Nutrition Label Entry
          </h2>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Barcode <span className="font-mono font-bold text-slate-800">{barcode}</span> was not found in global databases. Enter the package nutrition declaration below.
          </p>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-xs">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Basic identity */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">
              Product Name *
            </label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Traditional Rolled Oats"
              className="w-full text-sm border border-slate-300 rounded-xl px-3 py-2 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">
              Brand / Manufacturer
            </label>
            <input
              type="text"
              value={brand}
              onChange={(e) => setBrand(e.target.value)}
              placeholder="e.g. Nature Best"
              className="w-full text-sm border border-slate-300 rounded-xl px-3 py-2 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
            />
          </div>
        </div>

        {/* Category & Basis */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="sm:col-span-2">
            <label className="block text-xs font-bold text-slate-700 mb-1">
              Category *
            </label>
            <select
              required
              value={categoryId}
              onChange={(e) => setCategoryId(Number(e.target.value))}
              className="w-full text-sm border border-slate-300 rounded-xl px-3 py-2 bg-white focus:ring-2 focus:ring-emerald-500 focus:outline-none"
            >
              {categories.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">
              Basis
            </label>
            <select
              value={servingBasis}
              onChange={(e) => setServingBasis(e.target.value as any)}
              className="w-full text-sm border border-slate-300 rounded-xl px-3 py-2 bg-white focus:ring-2 focus:ring-emerald-500 focus:outline-none"
            >
              <option value="per 100g">Per 100 g (Solids)</option>
              <option value="per 100ml">Per 100 ml (Beverages)</option>
            </select>
          </div>
        </div>

        {/* Nutrition values grid */}
        <div className="space-y-2 pt-2">
          <h3 className="text-xs font-bold text-slate-600 uppercase tracking-wide">
            Nutrition Declaration ({servingBasis}) — Optional fields will stay NULL
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div>
              <label className="block text-[11px] font-semibold text-slate-500 mb-0.5">Energy (kcal)</label>
              <input
                type="number"
                step="0.1"
                min="0"
                value={energyKcal}
                onChange={(e) => setEnergyKcal(e.target.value)}
                placeholder="kcal"
                className="w-full text-xs border border-slate-300 rounded-lg px-2.5 py-1.5 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-[11px] font-semibold text-slate-500 mb-0.5">Carbohydrates (g)</label>
              <input
                type="number"
                step="0.1"
                min="0"
                value={carbs}
                onChange={(e) => setCarbs(e.target.value)}
                placeholder="g"
                className="w-full text-xs border border-slate-300 rounded-lg px-2.5 py-1.5 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-[11px] font-semibold text-slate-500 mb-0.5">Sugars (g)</label>
              <input
                type="number"
                step="0.1"
                min="0"
                value={sugars}
                onChange={(e) => setSugars(e.target.value)}
                placeholder="g"
                className="w-full text-xs border border-slate-300 rounded-lg px-2.5 py-1.5 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-[11px] font-semibold text-slate-500 mb-0.5">Total Fat (g)</label>
              <input
                type="number"
                step="0.1"
                min="0"
                value={fat}
                onChange={(e) => setFat(e.target.value)}
                placeholder="g"
                className="w-full text-xs border border-slate-300 rounded-lg px-2.5 py-1.5 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-[11px] font-semibold text-slate-500 mb-0.5">Saturated Fat (g)</label>
              <input
                type="number"
                step="0.1"
                min="0"
                value={satFat}
                onChange={(e) => setSatFat(e.target.value)}
                placeholder="g"
                className="w-full text-xs border border-slate-300 rounded-lg px-2.5 py-1.5 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-[11px] font-semibold text-slate-500 mb-0.5">Dietary Fiber (g)</label>
              <input
                type="number"
                step="0.1"
                min="0"
                value={fiber}
                onChange={(e) => setFiber(e.target.value)}
                placeholder="g"
                className="w-full text-xs border border-slate-300 rounded-lg px-2.5 py-1.5 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-[11px] font-semibold text-slate-500 mb-0.5">Proteins (g)</label>
              <input
                type="number"
                step="0.1"
                min="0"
                value={protein}
                onChange={(e) => setProtein(e.target.value)}
                placeholder="g"
                className="w-full text-xs border border-slate-300 rounded-lg px-2.5 py-1.5 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-[11px] font-semibold text-slate-500 mb-0.5">Salt (g)</label>
              <input
                type="number"
                step="0.01"
                min="0"
                value={salt}
                onChange={(e) => setSalt(e.target.value)}
                placeholder="g"
                className="w-full text-xs border border-slate-300 rounded-lg px-2.5 py-1.5 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
              />
            </div>
          </div>
        </div>

        {/* Ingredients text */}
        <div>
          <label className="block text-xs font-bold text-slate-700 mb-1">
            Ingredients (comma-separated)
          </label>
          <textarea
            rows={2}
            value={ingredientsText}
            onChange={(e) => setIngredientsText(e.target.value)}
            placeholder="e.g. Rolled oats, sunflower seeds, honey, sea salt"
            className="w-full text-xs border border-slate-300 rounded-xl px-3 py-2 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
          />
        </div>

        <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 border border-slate-300 hover:bg-slate-50 text-slate-700 font-semibold text-xs rounded-xl transition"
            >
              Cancel
            </button>
          )}
          <button
            type="submit"
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-6 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-xl shadow-xs transition disabled:opacity-50"
          >
            <PlusCircle className="w-4 h-4" />
            {loading ? 'Submitting & Scoring...' : 'Save & Analyze Product'}
          </button>
        </div>
      </form>
    </div>
  );
};