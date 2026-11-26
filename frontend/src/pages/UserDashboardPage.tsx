import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { History, Bookmark, Trash2, ExternalLink, Calendar, Tag, ArrowRight } from 'lucide-react';
import { endpoints } from '../api/endpoints';
import type { SearchHistoryItem, SavedProductItem } from '../types';
import { LoadingSkeleton } from '../components/LoadingSkeleton';
import { EmptyState } from '../components/EmptyState';
import { NutriScoreBadge } from '../components/NutriScoreBadge';

export const UserDashboardPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'history' | 'saved'>('history');
  const [history, setHistory] = useState<SearchHistoryItem[]>([]);
  const [saved, setSaved] = useState<SavedProductItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [editingNotesId, setEditingNotesId] = useState<string | null>(null);
  const [tempNotes, setTempNotes] = useState<string>('');

  const loadData = async () => {
    try {
      setLoading(true);
      const [histData, savedData] = await Promise.all([
        endpoints.getHistory(1, 30),
        endpoints.getSavedProducts()
      ]);
      setHistory(histData || []);
      setSaved(savedData || []);
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleDeleteHistory = async (id: string) => {
    try {
      await endpoints.deleteHistoryItem(id);
      setHistory((prev) => prev.filter((item) => item.id !== id));
    } catch (err) {
      console.error('Failed to delete history item:', err);
    }
  };

  const handleRemoveSaved = async (productId: string) => {
    try {
      await endpoints.removeSavedProduct(productId);
      setSaved((prev) => prev.filter((item) => item.product_id !== productId));
    } catch (err) {
      console.error('Failed to remove saved product:', err);
    }
  };

  const handleSaveNotes = async (savedId: string, productId: string) => {
    try {
      await endpoints.saveProduct(productId, tempNotes);
      setSaved((prev) => prev.map((item) => (item.id === savedId ? { ...item, notes: tempNotes } : item)));
      setEditingNotesId(null);
    } catch (err) {
      console.error('Failed to update notes:', err);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <div>
        <h1 className="text-2xl font-black text-gray-900">User Dashboard</h1>
        <p className="text-sm text-gray-600">
          Manage your scan history, saved items, and personalized dietary comparison notes.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-200 space-x-8">
        <button
          onClick={() => setActiveTab('history')}
          className={`pb-4 px-1 inline-flex items-center text-sm font-semibold border-b-2 transition-colors ${
            activeTab === 'history'
              ? 'border-emerald-600 text-emerald-600'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
          }`}
        >
          <History className="w-4 h-4 mr-2" />
          Scan History ({history.length})
        </button>

        <button
          onClick={() => setActiveTab('saved')}
          className={`pb-4 px-1 inline-flex items-center text-sm font-semibold border-b-2 transition-colors ${
            activeTab === 'saved'
              ? 'border-emerald-600 text-emerald-600'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
          }`}
        >
          <Bookmark className="w-4 h-4 mr-2" />
          Saved Products ({saved.length})
        </button>
      </div>

      {loading ? (
        <LoadingSkeleton rows={4} />
      ) : activeTab === 'history' ? (
        /* Scan History Tab */
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <span className="text-xs text-gray-500">
              Showing recent product scans and searches
            </span>
          </div>

          {history.length === 0 ? (
            <EmptyState
              title="No Scan History Yet"
              description="Products you search for or scan will appear here for easy reference."
              actionText="Search a Product"
              onAction={() => (window.location.href = '/')}
            />
          ) : (
            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm divide-y divide-gray-100">
              {history.map((item) => (
                <div key={item.id} className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-gray-50 transition-colors">
                  <div className="flex items-center space-x-4">
                    <div className="w-10 h-10 bg-gray-50 border border-gray-100 rounded-lg flex items-center justify-center p-1.5 flex-shrink-0">
                      <Tag className="w-5 h-5 text-gray-400" />
                    </div>
                    <div>
                      <span className="font-bold text-gray-900 text-sm">
                        Query: {item.query_term}
                      </span>
                      <p className="text-xs text-gray-500">
                        Type: {item.query_type}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-4 justify-between sm:justify-end">
                    <span className="text-xs text-gray-400 flex items-center">
                      <Calendar className="w-3 h-3 mr-1" />
                      {new Date(item.searched_at).toLocaleDateString()}
                    </span>
                    <button
                      onClick={() => handleDeleteHistory(item.id)}
                      className="p-1 text-gray-400 hover:text-red-600 transition-colors"
                      title="Delete record"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ) : (
        /* Saved Products Tab */
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <span className="text-xs text-gray-500">
              Bookmarked products and healthier replacements
            </span>
          </div>

          {saved.length === 0 ? (
            <EmptyState
              title="No Saved Products"
              description="Save products during analysis to compare them later or keep notes."
              actionText="Explore Products"
              onAction={() => (window.location.href = '/')}
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {saved.map((item) => {
                const prod = item.product;
                return (
                  <div key={item.id} className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm space-y-4">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center space-x-3">
                        <div className="w-14 h-14 bg-gray-50 border border-gray-100 rounded-lg flex items-center justify-center p-2 flex-shrink-0">
                          {prod?.image_url ? (
                            <img src={prod.image_url} alt={prod.name} className="max-h-full max-w-full object-contain" />
                          ) : (
                            <Tag className="w-6 h-6 text-gray-400" />
                          )}
                        </div>
                        <div>
                          <Link
                            to={`/products/${prod?.barcode || item.product_id}`}
                            className="font-bold text-gray-900 hover:text-emerald-700 text-sm line-clamp-1"
                          >
                            {prod?.name || `Product #${item.product_id}`}
                          </Link>
                          <p className="text-xs text-gray-500">{prod?.brand || 'Unknown Brand'}</p>
                          {prod?.nutri_score_grade && (
                            <div className="mt-1">
                              <NutriScoreBadge grade={prod.nutri_score_grade} size="sm" />
                            </div>
                          )}
                        </div>
                      </div>

                      <button
                        onClick={() => handleRemoveSaved(item.product_id)}
                        className="text-gray-400 hover:text-red-600 transition-colors p-1"
                        title="Remove from saved"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>

                    {/* Notes Section */}
                    <div className="pt-3 border-t border-gray-100">
                      <div className="flex justify-between items-center mb-1">
                        <span className="text-xs font-semibold text-gray-700 uppercase tracking-wide">Personal Notes</span>
                        {editingNotesId !== item.id && (
                          <button
                            onClick={() => {
                              setEditingNotesId(item.id);
                              setTempNotes(item.notes || '');
                            }}
                            className="text-xs text-emerald-600 hover:text-emerald-700 font-medium"
                          >
                            {item.notes ? 'Edit' : 'Add Note'}
                          </button>
                        )}
                      </div>

                      {editingNotesId === item.id ? (
                        <div className="space-y-2">
                          <textarea
                            rows={2}
                            value={tempNotes}
                            onChange={(e) => setTempNotes(e.target.value)}
                            placeholder="e.g., Preferred over brand X because of lower sodium..."
                            className="w-full text-xs p-2 border border-gray-300 rounded-lg focus:ring-emerald-500 focus:border-emerald-500"
                          />
                          <div className="flex justify-end space-x-2">
                            <button
                              onClick={() => setEditingNotesId(null)}
                              className="px-2 py-1 text-xs text-gray-600 hover:bg-gray-100 rounded"
                            >
                              Cancel
                            </button>
                            <button
                              onClick={() => handleSaveNotes(item.id, item.product_id)}
                              className="px-2.5 py-1 text-xs bg-emerald-600 text-white rounded font-medium hover:bg-emerald-700"
                            >
                              Save
                            </button>
                          </div>
                        </div>
                      ) : (
                        <p className="text-xs text-gray-600 italic">
                          {item.notes || 'No notes added yet.'}
                        </p>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
export default UserDashboardPage;
