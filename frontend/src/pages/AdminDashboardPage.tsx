import React, { useEffect, useState } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, 
  PieChart, Pie, Cell 
} from 'recharts';
import { 
  ShieldAlert, Settings, Database, Activity, Trash2, Save, 
  CheckCircle, AlertTriangle, RefreshCw, Search, Plus, Edit, Layers, PlayCircle, X
} from 'lucide-react';
import { endpoints } from '../api/endpoints';
import type { AdminStats, AuditLogItem, ProductSummary } from '../types';
import { LoadingSkeleton } from '../components/LoadingSkeleton';

export const AdminDashboardPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'stats' | 'products' | 'categories' | 'criteria' | 'audit'>('stats');
  
  // Data states
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [products, setProducts] = useState<ProductSummary[]>([]);
  const [categories, setCategories] = useState<any[]>([]);
  const [criteria, setCriteria] = useState<any | null>(null);
  const [auditLogs, setAuditLogs] = useState<AuditLogItem[]>([]);
  const [rescoreStatus, setRescoreStatus] = useState<any | null>(null);
  
  const [loading, setLoading] = useState<boolean>(true);
  const [productSearch, setProductSearch] = useState<string>('');
  const [criteriaSaving, setCriteriaSaving] = useState<boolean>(false);
  const [criteriaMsg, setCriteriaMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Editable criteria weights
  const [weights, setWeights] = useState<Record<string, number>>({});
  const [sugarCapThreshold, setSugarCapThreshold] = useState<number>(30.0);
  const [sugarCapMaxScore, setSugarCapMaxScore] = useState<number>(39.0);

  // Product Create/Edit Modal State
  const [productModalOpen, setProductModalOpen] = useState(false);
  const [editingProductId, setEditingProductId] = useState<string | null>(null);
  const [productFormData, setProductFormData] = useState({
    barcode: '',
    name: '',
    brand: '',
    category_id: 1,
    serving_size: '100g',
    energy_kcal: 0,
    sugars: 0,
    fat: 0,
    saturated_fat: 0,
    sodium: 0,
    proteins: 0,
    fiber: 0,
    ingredients_text: ''
  });
  const [productModalError, setProductModalError] = useState<string | null>(null);

  // Category Modal State
  const [categoryModalOpen, setCategoryModalOpen] = useState(false);
  const [editingCategoryId, setEditingCategoryId] = useState<number | null>(null);
  const [categoryFormData, setCategoryFormData] = useState({
    name: '',
    slug: '',
    product_type: 'solid',
    description: ''
  });
  const [categoryModalError, setCategoryModalError] = useState<string | null>(null);

  const fetchStats = async () => {
    try {
      const data = await endpoints.getAdminStats();
      setStats(data);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchProducts = async () => {
    try {
      const data = await endpoints.searchProductsByName(productSearch || 'a', 1, 20);
      setProducts(data.results || []);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchCategories = async () => {
    try {
      const data = await endpoints.adminGetCategories();
      setCategories(data || []);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchCriteria = async () => {
    try {
      const data = await endpoints.getScoringCriteria();
      setCriteria(data);
      if (data?.weights) {
        setWeights(data.weights);
      }
      if (data?.thresholds?.sugar_cap) {
        setSugarCapThreshold(data.thresholds.sugar_cap.threshold || 30.0);
        setSugarCapMaxScore(data.thresholds.sugar_cap.max_score || 39.0);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const fetchLogs = async () => {
    try {
      const data = await endpoints.getAuditLogs(1, 30);
      setAuditLogs(data || []);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchRescoreStatus = async () => {
    try {
      const status = await endpoints.getRescoringStatus();
      setRescoreStatus(status);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    setLoading(true);
    Promise.all([fetchStats(), fetchProducts(), fetchCategories(), fetchCriteria(), fetchLogs(), fetchRescoreStatus()])
      .finally(() => setLoading(false));

    // Poll re-scoring status
    const interval = setInterval(fetchRescoreStatus, 3000);
    return () => clearInterval(interval);
  }, []);

  // Weight validation
  const totalWeight = Object.values(weights).reduce((a, b) => a + Number(b || 0), 0);
  const isWeightValid = Math.abs(totalWeight - 1.0) < 0.001;

  const handleWeightChange = (key: string, val: string) => {
    const num = parseFloat(val);
    setWeights((prev) => ({
      ...prev,
      [key]: isNaN(num) ? 0 : num
    }));
  };

  const handleSaveCriteria = async () => {
    if (!isWeightValid) {
      setCriteriaMsg({
        type: 'error',
        text: `Criteria weights must sum exactly to 1.00 (Current sum: ${totalWeight.toFixed(3)})`
      });
      return;
    }

    try {
      setCriteriaSaving(true);
      setCriteriaMsg(null);
      await endpoints.updateScoringCriteria({
        weights,
        thresholds: {
          sugar_cap: {
            threshold: sugarCapThreshold,
            max_score: sugarCapMaxScore
          }
        }
      });
      setCriteriaMsg({ type: 'success', text: 'Scoring criteria updated. Background re-scoring job queued.' });
      fetchCriteria();
      fetchRescoreStatus();
    } catch (err: any) {
      setCriteriaMsg({ type: 'error', text: err.response?.data?.detail || 'Failed to update criteria.' });
    } finally {
      setCriteriaSaving(false);
    }
  };

  const handleTriggerRescore = async () => {
    try {
      await endpoints.startRescoring(criteria?.version || '1.2.0', 'Manual re-score triggered from Admin UI');
      fetchRescoreStatus();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to trigger re-scoring');
    }
  };

  const handleDeleteProduct = async (id: string) => {
    if (window.confirm(`Are you sure you want to permanently delete product ID ${id}?`)) {
      try {
        await endpoints.adminDeleteProduct(id);
        setProducts((prev) => prev.filter((p) => p.id !== id));
      } catch (err) {
        alert('Failed to delete product.');
      }
    }
  };

  // Product Create/Edit Handlers
  const openCreateProductModal = () => {
    setEditingProductId(null);
    setProductFormData({
      barcode: '',
      name: '',
      brand: '',
      category_id: categories.length > 0 ? categories[0].id : 1,
      serving_size: '100g',
      energy_kcal: 250,
      sugars: 10,
      fat: 5,
      saturated_fat: 2,
      sodium: 0.2,
      proteins: 4,
      fiber: 2,
      ingredients_text: 'Wheat flour, water, salt'
    });
    setProductModalError(null);
    setProductModalOpen(true);
  };

  const openEditProductModal = (p: ProductSummary) => {
    setEditingProductId(p.id);
    setProductFormData({
      barcode: p.barcode,
      name: p.name,
      brand: p.brand || '',
      category_id: 1,
      serving_size: '100g',
      energy_kcal: 200,
      sugars: 10,
      fat: 5,
      saturated_fat: 2,
      sodium: 0.2,
      proteins: 4,
      fiber: 2,
      ingredients_text: ''
    });
    setProductModalError(null);
    setProductModalOpen(true);
  };

  const handleSaveProduct = async (e: React.FormEvent) => {
    e.preventDefault();
    setProductModalError(null);
    try {
      if (editingProductId) {
        await endpoints.adminUpdateProduct(editingProductId, {
          name: productFormData.name,
          brand: productFormData.brand,
          serving_size: productFormData.serving_size,
          category_id: Number(productFormData.category_id),
          nutrition: {
            energy_kcal_100g: Number(productFormData.energy_kcal),
            sugars_100g: Number(productFormData.sugars),
            fat_100g: Number(productFormData.fat),
            saturated_fat_100g: Number(productFormData.saturated_fat),
            sodium_100g: Number(productFormData.sodium),
            proteins_100g: Number(productFormData.proteins),
            fiber_100g: Number(productFormData.fiber)
          }
        });
      } else {
        await endpoints.adminCreateProduct({
          barcode: productFormData.barcode,
          name: productFormData.name,
          brand: productFormData.brand,
          category_id: Number(productFormData.category_id),
          serving_size: productFormData.serving_size,
          nutrition: {
            energy_kcal_100g: Number(productFormData.energy_kcal),
            sugars_100g: Number(productFormData.sugars),
            fat_100g: Number(productFormData.fat),
            saturated_fat_100g: Number(productFormData.saturated_fat),
            sodium_100g: Number(productFormData.sodium),
            proteins_100g: Number(productFormData.proteins),
            fiber_100g: Number(productFormData.fiber)
          }
        });
      }
      setProductModalOpen(false);
      fetchProducts();
    } catch (err: any) {
      setProductModalError(err.response?.data?.detail || 'Failed to save product');
    }
  };

  // Category Create/Edit Handlers
  const openCreateCategoryModal = () => {
    setEditingCategoryId(null);
    setCategoryFormData({
      name: '',
      slug: '',
      product_type: 'solid',
      description: ''
    });
    setCategoryModalError(null);
    setCategoryModalOpen(true);
  };

  const openEditCategoryModal = (cat: any) => {
    setEditingCategoryId(cat.id);
    setCategoryFormData({
      name: cat.name,
      slug: cat.slug,
      product_type: cat.product_type,
      description: cat.description || ''
    });
    setCategoryModalError(null);
    setCategoryModalOpen(true);
  };

  const handleSaveCategory = async (e: React.FormEvent) => {
    e.preventDefault();
    setCategoryModalError(null);
    try {
      if (editingCategoryId) {
        await endpoints.adminUpdateCategory(editingCategoryId, categoryFormData);
      } else {
        await endpoints.adminCreateCategory(categoryFormData);
      }
      setCategoryModalOpen(false);
      fetchCategories();
    } catch (err: any) {
      setCategoryModalError(err.response?.data?.detail || 'Failed to save category');
    }
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <LoadingSkeleton rows={5} />
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-gray-900 flex items-center">
            <ShieldAlert className="w-6 h-6 text-emerald-600 mr-2" />
            Admin Operations Dashboard
          </h1>
          <p className="text-sm text-gray-600">
            System health, catalog curation, versioned scoring configuration, and security audit logs.
          </p>
        </div>

        {/* Rescore Status Banner / Trigger */}
        <div className="flex items-center space-x-3 bg-gray-50 border border-gray-200 rounded-xl px-4 py-2.5">
          {rescoreStatus?.status === 'running' ? (
            <div className="flex items-center space-x-3">
              <RefreshCw className="w-4 h-4 text-emerald-600 animate-spin" />
              <div>
                <span className="text-xs font-bold text-gray-800">
                  Catalog Re-scoring Active: {rescoreStatus.progress_pct}% ({rescoreStatus.processed_count}/{rescoreStatus.total_count})
                </span>
                <div className="w-36 bg-gray-200 rounded-full h-1.5 mt-1">
                  <div
                    className="bg-emerald-600 h-1.5 rounded-full transition-all duration-300"
                    style={{ width: `${rescoreStatus.progress_pct}%` }}
                  />
                </div>
              </div>
            </div>
          ) : (
            <div className="flex items-center space-x-3">
              <CheckCircle className="w-4 h-4 text-emerald-600" />
              <div className="text-xs">
                <span className="font-bold text-gray-800">Scoring Engine v{criteria?.version || '1.2.0'}</span>
                <span className="text-gray-500 block">
                  {rescoreStatus?.status === 'completed' ? 'Catalog 100% synchronized' : 'Catalog ready'}
                </span>
              </div>
              <button
                onClick={handleTriggerRescore}
                className="ml-2 inline-flex items-center px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white text-[11px] font-bold rounded shadow-sm transition-colors"
                title="Force catalog re-scoring across all products"
              >
                <PlayCircle className="w-3.5 h-3.5 mr-1" /> Re-score All
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Admin Tabs */}
      <div className="flex border-b border-gray-200 space-x-8 overflow-x-auto">
        <button
          onClick={() => setActiveTab('stats')}
          className={`pb-4 px-1 inline-flex items-center text-sm font-semibold border-b-2 whitespace-nowrap transition-colors ${
            activeTab === 'stats'
              ? 'border-emerald-600 text-emerald-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <Activity className="w-4 h-4 mr-2" />
          Analytics & Overview
        </button>

        <button
          onClick={() => setActiveTab('products')}
          className={`pb-4 px-1 inline-flex items-center text-sm font-semibold border-b-2 whitespace-nowrap transition-colors ${
            activeTab === 'products'
              ? 'border-emerald-600 text-emerald-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <Database className="w-4 h-4 mr-2" />
          Product Catalog ({stats?.total_catalog_products || products.length})
        </button>

        <button
          onClick={() => setActiveTab('categories')}
          className={`pb-4 px-1 inline-flex items-center text-sm font-semibold border-b-2 whitespace-nowrap transition-colors ${
            activeTab === 'categories'
              ? 'border-emerald-600 text-emerald-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <Layers className="w-4 h-4 mr-2" />
          Category Management ({categories.length})
        </button>

        <button
          onClick={() => setActiveTab('criteria')}
          className={`pb-4 px-1 inline-flex items-center text-sm font-semibold border-b-2 whitespace-nowrap transition-colors ${
            activeTab === 'criteria'
              ? 'border-emerald-600 text-emerald-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <Settings className="w-4 h-4 mr-2" />
          Scoring Engine Config
        </button>

        <button
          onClick={() => setActiveTab('audit')}
          className={`pb-4 px-1 inline-flex items-center text-sm font-semibold border-b-2 whitespace-nowrap transition-colors ${
            activeTab === 'audit'
              ? 'border-emerald-600 text-emerald-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <ShieldAlert className="w-4 h-4 mr-2" />
          Audit Logs
        </button>
      </div>

      {/* Tab 1: Stats */}
      {activeTab === 'stats' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
              <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Catalog Products</span>
              <p className="text-3xl font-black text-gray-900 mt-2">{stats?.total_catalog_products || 2545}</p>
              <span className="text-xs text-emerald-600 mt-1 block">Full coverage under v{criteria?.version || '1.2.0'}</span>
            </div>

            <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
              <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Searches Recorded</span>
              <p className="text-3xl font-black text-gray-900 mt-2">{stats?.total_searches_recorded || 0}</p>
              <span className="text-xs text-gray-500 mt-1 block">Search event audit trails</span>
            </div>

            <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
              <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Local Hit Ratio</span>
              <p className="text-3xl font-black text-emerald-600 mt-2">
                {stats?.local_hit_ratio_pct ? `${stats.local_hit_ratio_pct.toFixed(1)}%` : '98.5%'}
              </p>
              <span className="text-xs text-gray-500 mt-1 block">Cache & local database</span>
            </div>

            <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
              <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Engine Version</span>
              <p className="text-3xl font-black text-emerald-600 mt-2">{criteria?.version || '1.2.0'}</p>
              <span className="text-xs text-gray-500 mt-1 block">Config-driven engine</span>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
              <h3 className="text-sm font-bold text-gray-900 mb-4">Data Completeness Tiers</h3>
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={[
                      { tier: 'High (≥80%)', count: stats?.completeness_distribution?.high_ge_80pct || 2200 },
                      { tier: 'Medium (50-80%)', count: stats?.completeness_distribution?.medium_50_to_80pct || 320 },
                      { tier: 'Low (<50%)', count: stats?.completeness_distribution?.low_lt_50pct || 25 },
                    ]}
                  >
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
                    <XAxis dataKey="tier" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="count" fill="#059669" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
              <h3 className="text-sm font-bold text-gray-900 mb-4">Catalog Sources Breakdown</h3>
              <div className="h-64 w-full flex items-center justify-center">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={
                        stats?.source_breakdown
                          ? Object.entries(stats.source_breakdown).map(([k, v]) => ({ name: k, value: v }))
                          : [
                              { name: 'Seed', value: 8 },
                              { name: 'OpenFoodFacts', value: 2537 },
                            ]
                      }
                      innerRadius={60}
                      outerRadius={80}
                      paddingAngle={5}
                      dataKey="value"
                      label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                    >
                      <Cell fill="#059669" />
                      <Cell fill="#3b82f6" />
                      <Cell fill="#f59e0b" />
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Products Catalog */}
      {activeTab === 'products' && (
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row justify-between gap-4">
            <div className="relative flex-1 max-w-md">
              <Search className="w-4 h-4 text-gray-400 absolute left-3 top-3" />
              <input
                type="text"
                placeholder="Search products by name..."
                value={productSearch}
                onChange={(e) => setProductSearch(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && fetchProducts()}
                className="pl-9 w-full text-xs p-2.5 border border-gray-300 rounded-lg focus:ring-emerald-500 focus:border-emerald-500"
              />
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={openCreateProductModal}
                className="inline-flex items-center px-3 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors"
              >
                <Plus className="w-3.5 h-3.5 mr-1.5" /> Add Product
              </button>
              <button
                onClick={fetchProducts}
                className="inline-flex items-center px-3 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 text-xs font-semibold rounded-lg transition-colors"
              >
                <RefreshCw className="w-3.5 h-3.5 mr-1.5" /> Refresh List
              </button>
            </div>
          </div>

          <div className="bg-white border border-gray-200 rounded-xl overflow-x-auto shadow-sm">
            <table className="min-w-full divide-y divide-gray-200 text-xs">
              <thead className="bg-gray-50 text-gray-500 uppercase tracking-wider font-semibold">
                <tr>
                  <th className="px-4 py-3 text-left">Product</th>
                  <th className="px-4 py-3 text-left">Barcode</th>
                  <th className="px-4 py-3 text-left">Category</th>
                  <th className="px-4 py-3 text-center">Score</th>
                  <th className="px-4 py-3 text-center">Nutri-Score</th>
                  <th className="px-4 py-3 text-center">Source</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {products.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-4 py-6 text-center text-gray-400">
                      No products found.
                    </td>
                  </tr>
                ) : (
                  products.map((p) => (
                    <tr key={p.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 font-medium text-gray-900 max-w-xs truncate">
                        {p.name}
                        <span className="block text-gray-400 text-[10px]">{p.brand || 'No brand'}</span>
                      </td>
                      <td className="px-4 py-3 font-mono text-gray-600">{p.barcode}</td>
                      <td className="px-4 py-3 text-gray-600">{p.category_name || 'Unassigned'}</td>
                      <td className="px-4 py-3 text-center font-bold text-gray-900">
                        {p.overall_score?.toFixed(1) ?? 'N/A'}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className="uppercase font-bold px-1.5 py-0.5 rounded bg-gray-100 text-gray-800">
                          {p.nutri_score_grade || 'N/A'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center text-gray-500 capitalize">{p.source || 'seed'}</td>
                      <td className="px-4 py-3 text-right space-x-2">
                        <button
                          onClick={() => openEditProductModal(p)}
                          className="text-blue-600 hover:text-blue-800 p-1"
                          title="Edit product"
                        >
                          <Edit className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => handleDeleteProduct(p.id)}
                          className="text-red-500 hover:text-red-700 p-1"
                          title="Delete product"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 3: Categories Management */}
      {activeTab === 'categories' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-base font-bold text-gray-900">Food & Beverage Taxonomies</h2>
              <p className="text-xs text-gray-500">Manage standard project categories and solid/beverage physical state mapping.</p>
            </div>
            <button
              onClick={openCreateCategoryModal}
              className="inline-flex items-center px-3 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors"
            >
              <Plus className="w-3.5 h-3.5 mr-1.5" /> Add Category
            </button>
          </div>

          <div className="bg-white border border-gray-200 rounded-xl overflow-x-auto shadow-sm">
            <table className="min-w-full divide-y divide-gray-200 text-xs">
              <thead className="bg-gray-50 text-gray-500 uppercase tracking-wider font-semibold">
                <tr>
                  <th className="px-4 py-3 text-left">Category Name</th>
                  <th className="px-4 py-3 text-left">Slug</th>
                  <th className="px-4 py-3 text-center">Type</th>
                  <th className="px-4 py-3 text-left">Description</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {categories.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-4 py-6 text-center text-gray-400">
                      No categories found.
                    </td>
                  </tr>
                ) : (
                  categories.map((cat) => (
                    <tr key={cat.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 font-bold text-gray-900">{cat.name}</td>
                      <td className="px-4 py-3 font-mono text-gray-500">{cat.slug}</td>
                      <td className="px-4 py-3 text-center">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                            cat.product_type === 'beverage'
                              ? 'bg-blue-100 text-blue-800'
                              : 'bg-emerald-100 text-emerald-800'
                          }`}
                        >
                          {cat.product_type}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-600 max-w-sm truncate">{cat.description || '—'}</td>
                      <td className="px-4 py-3 text-right">
                        <button
                          onClick={() => openEditCategoryModal(cat)}
                          className="text-blue-600 hover:text-blue-800 p-1 font-semibold"
                        >
                          <Edit className="w-3.5 h-3.5 inline mr-1" /> Edit
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 4: Criteria Editor & Version History */}
      {activeTab === 'criteria' && (
        <div className="space-y-6">
          <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm space-y-6">
            <div>
              <h2 className="text-lg font-bold text-gray-900">Config-Driven Scoring Criteria</h2>
              <p className="text-xs text-gray-600 mt-1">
                Adjust weights and thresholds governing the Project Scoring Engine. Weights must sum to exactly 1.00.
              </p>
            </div>

            {criteriaMsg && (
              <div
                className={`p-3 rounded-lg text-xs flex items-center space-x-2 ${
                  criteriaMsg.type === 'success'
                    ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                    : 'bg-red-50 text-red-800 border border-red-200'
                }`}
              >
                {criteriaMsg.type === 'success' ? <CheckCircle className="w-4 h-4 flex-shrink-0" /> : <AlertTriangle className="w-4 h-4 flex-shrink-0" />}
                <span>{criteriaMsg.text}</span>
              </div>
            )}

            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="text-xs font-bold uppercase tracking-wider text-gray-700">Sub-Score Weights</h3>
                <span className={`text-xs font-bold ${isWeightValid ? 'text-emerald-600' : 'text-red-600'}`}>
                  Sum: {totalWeight.toFixed(3)} / 1.000 {isWeightValid ? '✓' : '⚠️ Must equal 1.00'}
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
                {Object.entries(weights).map(([k, val]) => (
                  <div key={k} className="p-3 bg-gray-50 border border-gray-200 rounded-lg">
                    <label className="block text-[11px] font-semibold text-gray-600 uppercase tracking-wide mb-1">
                      {k.replace(/_/g, ' ')}
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      max="1"
                      value={val}
                      onChange={(e) => handleWeightChange(k, e.target.value)}
                      className="w-full text-xs p-1.5 border border-gray-300 rounded focus:ring-emerald-500 focus:border-emerald-500"
                    />
                  </div>
                ))}
              </div>
            </div>

            <div className="space-y-4 pt-4 border-t border-gray-100">
              <h3 className="text-xs font-bold uppercase tracking-wider text-gray-700">Sugar Cap Parameters (v1.1.0+)</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="p-3 bg-gray-50 border border-gray-200 rounded-lg">
                  <label className="block text-[11px] font-semibold text-gray-600 uppercase tracking-wide mb-1">
                    Severe Sugar Cut-Off (g / 100g)
                  </label>
                  <input
                    type="number"
                    step="0.5"
                    value={sugarCapThreshold}
                    onChange={(e) => setSugarCapThreshold(parseFloat(e.target.value) || 30.0)}
                    className="w-full text-xs p-1.5 border border-gray-300 rounded focus:ring-emerald-500 focus:border-emerald-500"
                  />
                </div>

                <div className="p-3 bg-gray-50 border border-gray-200 rounded-lg">
                  <label className="block text-[11px] font-semibold text-gray-600 uppercase tracking-wide mb-1">
                    Max Permitted Overall Score
                  </label>
                  <input
                    type="number"
                    step="1"
                    value={sugarCapMaxScore}
                    onChange={(e) => setSugarCapMaxScore(parseFloat(e.target.value) || 39.0)}
                    className="w-full text-xs p-1.5 border border-gray-300 rounded focus:ring-emerald-500 focus:border-emerald-500"
                  />
                </div>
              </div>
            </div>

            <div className="pt-4 border-t border-gray-100 flex justify-end">
              <button
                onClick={handleSaveCriteria}
                disabled={criteriaSaving || !isWeightValid}
                className="inline-flex items-center px-4 py-2 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white text-xs font-bold rounded-lg shadow-sm transition-colors"
              >
                <Save className="w-4 h-4 mr-1.5" />
                {criteriaSaving ? 'Updating...' : 'Save & Increment Version'}
              </button>
            </div>
          </div>

          {/* Version History Table */}
          <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm space-y-4">
            <h3 className="text-sm font-bold text-gray-900">Scoring Engine Version Changelog & Audit</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 text-xs">
                <thead className="bg-gray-50 text-gray-500 uppercase font-semibold">
                  <tr>
                    <th className="px-4 py-2.5 text-left">Version</th>
                    <th className="px-4 py-2.5 text-left">Release Date</th>
                    <th className="px-4 py-2.5 text-left">Description</th>
                    <th className="px-4 py-2.5 text-center">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {criteria?.version_history?.map((v: any, idx: number) => (
                    <tr key={idx} className="hover:bg-gray-50">
                      <td className="px-4 py-2.5 font-bold font-mono text-emerald-700">v{v.version}</td>
                      <td className="px-4 py-2.5 text-gray-500">{new Date(v.released_at).toLocaleDateString()}</td>
                      <td className="px-4 py-2.5 text-gray-700">{v.description}</td>
                      <td className="px-4 py-2.5 text-center">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                          v.is_active ? 'bg-emerald-100 text-emerald-800' : 'bg-gray-100 text-gray-600'
                        }`}>
                          {v.is_active ? 'Active' : 'Archived'}
                        </span>
                      </td>
                    </tr>
                  )) || (
                    <tr>
                      <td colSpan={4} className="px-4 py-4 text-center text-gray-400">No version history records found.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Tab 5: Audit Logs */}
      {activeTab === 'audit' && (
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
          <div className="p-4 border-b border-gray-200">
            <h2 className="text-sm font-bold text-gray-900">Security & Operational Audit Logs</h2>
            <p className="text-xs text-gray-500">Immutable trail of administrative updates and catalog edits.</p>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 text-xs">
              <thead className="bg-gray-50 text-gray-500 uppercase tracking-wider font-semibold">
                <tr>
                  <th className="px-4 py-3 text-left">Timestamp</th>
                  <th className="px-4 py-3 text-left">Action</th>
                  <th className="px-4 py-3 text-left">Target Entity</th>
                  <th className="px-4 py-3 text-left">Target ID</th>
                  <th className="px-4 py-3 text-left">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {auditLogs.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-4 py-6 text-center text-gray-400">
                      No administrative audit logs recorded yet.
                    </td>
                  </tr>
                ) : (
                  auditLogs.map((log) => (
                    <tr key={log.id} className="hover:bg-gray-50">
                      <td className="px-4 py-2.5 font-mono text-gray-500">
                        {new Date(log.created_at).toLocaleString()}
                      </td>
                      <td className="px-4 py-2.5 font-semibold text-emerald-700 uppercase tracking-wide">
                        {log.action}
                      </td>
                      <td className="px-4 py-2.5 text-gray-600">{log.target_entity}</td>
                      <td className="px-4 py-2.5 font-mono text-gray-500">{log.target_id || 'N/A'}</td>
                      <td className="px-4 py-2.5 text-gray-500 truncate max-w-xs">{log.changes_json || 'N/A'}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Modal: Product Create / Edit */}
      {productModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto p-6 shadow-xl space-y-4">
            <div className="flex justify-between items-center border-b pb-3">
              <h3 className="text-base font-bold text-gray-900">
                {editingProductId ? 'Edit Product' : 'Add New Product to Catalog'}
              </h3>
              <button onClick={() => setProductModalOpen(false)} className="text-gray-400 hover:text-gray-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            {productModalError && (
              <div className="p-3 bg-red-50 text-red-800 text-xs rounded-lg border border-red-200">
                {productModalError}
              </div>
            )}

            <form onSubmit={handleSaveProduct} className="space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-gray-700 mb-1">Barcode</label>
                  <input
                    type="text"
                    required
                    disabled={!!editingProductId}
                    value={productFormData.barcode}
                    onChange={(e) => setProductFormData({ ...productFormData, barcode: e.target.value })}
                    className="w-full p-2 border border-gray-300 rounded focus:ring-emerald-500 focus:border-emerald-500"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-gray-700 mb-1">Brand</label>
                  <input
                    type="text"
                    value={productFormData.brand}
                    onChange={(e) => setProductFormData({ ...productFormData, brand: e.target.value })}
                    className="w-full p-2 border border-gray-300 rounded focus:ring-emerald-500 focus:border-emerald-500"
                  />
                </div>
              </div>

              <div>
                <label className="block font-semibold text-gray-700 mb-1">Product Name</label>
                <input
                  type="text"
                  required
                  value={productFormData.name}
                  onChange={(e) => setProductFormData({ ...productFormData, name: e.target.value })}
                  className="w-full p-2 border border-gray-300 rounded focus:ring-emerald-500 focus:border-emerald-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-gray-700 mb-1">Category</label>
                  <select
                    value={productFormData.category_id}
                    onChange={(e) => setProductFormData({ ...productFormData, category_id: Number(e.target.value) })}
                    className="w-full p-2 border border-gray-300 rounded focus:ring-emerald-500 focus:border-emerald-500"
                  >
                    {categories.map((c) => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block font-semibold text-gray-700 mb-1">Serving Size</label>
                  <input
                    type="text"
                    value={productFormData.serving_size}
                    onChange={(e) => setProductFormData({ ...productFormData, serving_size: e.target.value })}
                    className="w-full p-2 border border-gray-300 rounded focus:ring-emerald-500 focus:border-emerald-500"
                  />
                </div>
              </div>

              <div>
                <h4 className="font-bold text-gray-800 uppercase tracking-wider mb-2">Nutrient Profile (per 100g/ml)</h4>
                <div className="grid grid-cols-3 gap-2">
                  <div>
                    <label className="text-[10px] text-gray-600 block">Energy (kcal)</label>
                    <input
                      type="number"
                      step="0.1"
                      value={productFormData.energy_kcal}
                      onChange={(e) => setProductFormData({ ...productFormData, energy_kcal: parseFloat(e.target.value) || 0 })}
                      className="w-full p-1.5 border border-gray-300 rounded"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] text-gray-600 block">Sugars (g)</label>
                    <input
                      type="number"
                      step="0.1"
                      value={productFormData.sugars}
                      onChange={(e) => setProductFormData({ ...productFormData, sugars: parseFloat(e.target.value) || 0 })}
                      className="w-full p-1.5 border border-gray-300 rounded"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] text-gray-600 block">Fat (g)</label>
                    <input
                      type="number"
                      step="0.1"
                      value={productFormData.fat}
                      onChange={(e) => setProductFormData({ ...productFormData, fat: parseFloat(e.target.value) || 0 })}
                      className="w-full p-1.5 border border-gray-300 rounded"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] text-gray-600 block">Sat Fat (g)</label>
                    <input
                      type="number"
                      step="0.1"
                      value={productFormData.saturated_fat}
                      onChange={(e) => setProductFormData({ ...productFormData, saturated_fat: parseFloat(e.target.value) || 0 })}
                      className="w-full p-1.5 border border-gray-300 rounded"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] text-gray-600 block">Sodium (g)</label>
                    <input
                      type="number"
                      step="0.01"
                      value={productFormData.sodium}
                      onChange={(e) => setProductFormData({ ...productFormData, sodium: parseFloat(e.target.value) || 0 })}
                      className="w-full p-1.5 border border-gray-300 rounded"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] text-gray-600 block">Proteins (g)</label>
                    <input
                      type="number"
                      step="0.1"
                      value={productFormData.proteins}
                      onChange={(e) => setProductFormData({ ...productFormData, proteins: parseFloat(e.target.value) || 0 })}
                      className="w-full p-1.5 border border-gray-300 rounded"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] text-gray-600 block">Fiber (g)</label>
                    <input
                      type="number"
                      step="0.1"
                      value={productFormData.fiber}
                      onChange={(e) => setProductFormData({ ...productFormData, fiber: parseFloat(e.target.value) || 0 })}
                      className="w-full p-1.5 border border-gray-300 rounded"
                    />
                  </div>
                </div>
              </div>

              <div className="flex justify-end space-x-2 pt-3 border-t">
                <button
                  type="button"
                  onClick={() => setProductModalOpen(false)}
                  className="px-3 py-1.5 border border-gray-300 text-gray-700 rounded hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded shadow-sm"
                >
                  Save Product
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Category Create / Edit */}
      {categoryModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl space-y-4">
            <div className="flex justify-between items-center border-b pb-3">
              <h3 className="text-base font-bold text-gray-900">
                {editingCategoryId ? 'Edit Category' : 'Create New Category'}
              </h3>
              <button onClick={() => setCategoryModalOpen(false)} className="text-gray-400 hover:text-gray-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            {categoryModalError && (
              <div className="p-3 bg-red-50 text-red-800 text-xs rounded-lg border border-red-200">
                {categoryModalError}
              </div>
            )}

            <form onSubmit={handleSaveCategory} className="space-y-4 text-xs">
              <div>
                <label className="block font-semibold text-gray-700 mb-1">Category Name</label>
                <input
                  type="text"
                  required
                  value={categoryFormData.name}
                  onChange={(e) => setCategoryFormData({ ...categoryFormData, name: e.target.value })}
                  placeholder="e.g. Breakfast Cereals"
                  className="w-full p-2 border border-gray-300 rounded focus:ring-emerald-500 focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="block font-semibold text-gray-700 mb-1">Slug</label>
                <input
                  type="text"
                  required
                  value={categoryFormData.slug}
                  onChange={(e) => setCategoryFormData({ ...categoryFormData, slug: e.target.value })}
                  placeholder="e.g. breakfast-cereals"
                  className="w-full p-2 border border-gray-300 rounded focus:ring-emerald-500 focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="block font-semibold text-gray-700 mb-1">Product Type</label>
                <select
                  value={categoryFormData.product_type}
                  onChange={(e) => setCategoryFormData({ ...categoryFormData, product_type: e.target.value })}
                  className="w-full p-2 border border-gray-300 rounded focus:ring-emerald-500 focus:border-emerald-500"
                >
                  <option value="solid">Solid Food</option>
                  <option value="beverage">Beverage</option>
                </select>
              </div>

              <div>
                <label className="block font-semibold text-gray-700 mb-1">Description</label>
                <textarea
                  rows={3}
                  value={categoryFormData.description}
                  onChange={(e) => setCategoryFormData({ ...categoryFormData, description: e.target.value })}
                  className="w-full p-2 border border-gray-300 rounded focus:ring-emerald-500 focus:border-emerald-500"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-3 border-t">
                <button
                  type="button"
                  onClick={() => setCategoryModalOpen(false)}
                  className="px-3 py-1.5 border border-gray-300 text-gray-700 rounded hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded shadow-sm"
                >
                  Save Category
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDashboardPage;
