import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Barcode, AlertCircle, Loader2 } from 'lucide-react';
import { validateBarcode } from '../utils/barcode';

interface SearchBarProps {
  onSearchByName?: (query: string) => void;
  className?: string;
  defaultMode?: 'barcode' | 'name';
}

export const SearchBar: React.FC<SearchBarProps> = ({
  onSearchByName,
  className = '',
  defaultMode = 'barcode',
}) => {
  const [mode, setMode] = useState<'barcode' | 'name'>(defaultMode);
  const [inputVal, setInputVal] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const query = inputVal.trim();
    if (!query) return;

    if (mode === 'barcode') {
      const validation = validateBarcode(query);
      if (!validation.valid) {
        setError(validation.error || 'Invalid barcode');
        return;
      }
      setError(null);
      setLoading(true);
      // Navigate to analysis page directly
      navigate(`/products/${query}`);
    } else {
      setError(null);
      if (onSearchByName) {
        onSearchByName(query);
      } else {
        navigate(`/search?q=${encodeURIComponent(query)}`);
      }
    }
  };

  return (
    <div className={`w-full max-w-2xl mx-auto ${className}`}>
      {/* Mode toggle */}
      <div className="flex gap-2 mb-2">
        <button
          type="button"
          onClick={() => { setMode('barcode'); setError(null); }}
          className={`flex items-center gap-1.5 px-3 py-1 text-xs font-semibold rounded-lg transition ${
            mode === 'barcode'
              ? 'bg-emerald-600 text-white shadow-xs'
              : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
          }`}
        >
          <Barcode className="w-3.5 h-3.5" /> Barcode Search
        </button>
        <button
          type="button"
          onClick={() => { setMode('name'); setError(null); }}
          className={`flex items-center gap-1.5 px-3 py-1 text-xs font-semibold rounded-lg transition ${
            mode === 'name'
              ? 'bg-emerald-600 text-white shadow-xs'
              : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
          }`}
        >
          <Search className="w-3.5 h-3.5" /> Product Name Search
        </button>
      </div>

      {/* Input form */}
      <form onSubmit={handleSearch} className="relative flex items-center">
        <div className="absolute left-4 text-slate-400">
          {mode === 'barcode' ? <Barcode className="w-5 h-5" /> : <Search className="w-5 h-5" />}
        </div>
        <input
          type="text"
          value={inputVal}
          onChange={(e) => {
            setInputVal(e.target.value);
            if (error) setError(null);
          }}
          placeholder={
            mode === 'barcode'
              ? 'Scan or enter barcode (e.g. 3017620422003 for Nutella)...'
              : 'Search food by name (e.g. oats, cola, dark chocolate)...'
          }
          className="w-full pl-12 pr-28 py-3.5 bg-white border border-slate-300 rounded-xl text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent shadow-sm text-sm"
        />
        <button
          type="submit"
          disabled={loading || !inputVal.trim()}
          className="absolute right-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-300 text-white text-xs font-bold rounded-lg transition flex items-center gap-1.5"
        >
          {loading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
          Search
        </button>
      </form>

      {/* Error message */}
      {error && (
        <div className="mt-2 text-xs text-rose-600 flex items-center gap-1.5 font-medium">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
};
