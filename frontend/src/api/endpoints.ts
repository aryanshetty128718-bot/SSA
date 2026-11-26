import { api } from './client';
import type {
  ProductSummary,
  ProductAnalysis,
  AlternativeItem,
  ComparisonResult,
  User,
  SearchHistoryItem,
  SavedProductItem,
  AdminStats,
  AuditLogItem,
} from '../types';

export const endpoints = {
  // Products & Analysis
  getProductByBarcode: async (barcode: string): Promise<any> => {
    const res = await api.get(`/products/barcode/${barcode.trim()}`);
    const data = res.data;
    // Normalize return so callers using either res.id or res.product.id work flawlessly
    if (data && !data.product) {
      return { ...data, product: data, cached: true };
    }
    return data;
  },

  searchProductsByName: async (query: string, page = 1, limit = 20): Promise<{ query: string; total: number; results: ProductSummary[] }> => {
    const res = await api.get('/products/search', { params: { q: query, page, limit } });
    const data = res.data;
    if (Array.isArray(data)) {
      return { query, total: data.length, results: data };
    }
    return data;
  },

  getProductAnalysis: async (productId: string): Promise<ProductAnalysis> => {
    try {
      const res = await api.get(`/products/${productId}/analysis`);
      return res.data;
    } catch {
      const res = await api.get(`/analysis/${productId}`);
      return res.data;
    }
  },

  getCategories: async (): Promise<Array<{ id: number; name: string; slug: string; product_type: string }>> => {
    try {
      const res = await api.get('/products/categories');
      return res.data;
    } catch {
      const res = await api.get('/categories');
      return res.data;
    }
  },

  submitManualEntry: async (payload: any): Promise<any> => {
    const res = await api.post('/products/manual-entry', payload);
    return res.data;
  },

  // Healthier Alternatives
  getAlternatives: async (productId: string, limit = 5): Promise<{ query_product_id: string; recommendations: AlternativeItem[]; timestamp: string }> => {
    try {
      const res = await api.get(`/recommendations/${productId}`, { params: { limit } });
      return res.data;
    } catch (err: any) {
      if (err.response?.status === 404) {
        // Fallback to alternatives by barcode route
        const res = await api.get(`/recommendations/barcode/${productId}`, { params: { limit } });
        return res.data;
      }
      throw err;
    }
  },

  // Comparison
  compareProducts: async (productIds: string[]): Promise<any> => {
    const res = await api.post('/compare', { product_ids: productIds, barcodes: productIds });
    const data = res.data;
    if (data) {
      const products = (data.products || []).map((p: any) => ({
        ...p,
        product_id: p.id || p.product_id,
        product_name: p.name || p.product_name,
        overall_project_score: p.overall_score ?? p.overall_project_score,
        nutrition: p.nutrition || {
          energy_kcal: p.nutrients?.energy_kcal,
          sugars_g: p.nutrients?.sugars_g,
          saturated_fat_g: p.nutrients?.saturated_fat_g,
          sodium_mg: p.nutrients?.sodium_mg,
          salt_g: p.nutrients?.salt_g,
          fiber_g: p.nutrients?.fiber_g,
          proteins_g: p.nutrients?.proteins_g,
        }
      }));

      const differences = (data.comparison_matrix || data.differences || []).map((m: any) => {
        const values: Record<string, number | null> = {};
        products.forEach((p: any) => {
          values[p.product_id] = m.values?.[p.barcode] ?? m.values?.[p.product_id] ?? null;
        });
        const bestProd = products.find((p: any) => p.barcode === m.best_barcode || p.product_id === m.best_product_id);
        return {
          parameter: m.parameter,
          label: m.display_name || m.label,
          unit: m.unit,
          values,
          best_product_id: bestProd ? bestProd.product_id : m.best_product_id,
        };
      });

      return {
        products,
        differences,
        summary: typeof data.summary_verdict === 'string' ? data.summary_verdict : (data.summary_verdict?.recommendation_statement || data.summary || ''),
        raw: data
      };
    }
    return data;
  },

  // Auth
  register: async (payload: { email: string; full_name: string; password: string }): Promise<User> => {
    const res = await api.post('/auth/register', payload);
    return res.data;
  },

  login: async (payload: { email: string; password: string }): Promise<{ access_token: string; token_type: string; user: User }> => {
    const res = await api.post('/auth/login', payload);
    return res.data;
  },

  getMe: async (): Promise<User> => {
    const res = await api.get('/auth/me');
    return res.data;
  },

  // User History & Saved Products
  getHistory: async (page = 1, limit = 20): Promise<SearchHistoryItem[]> => {
    const res = await api.get('/users/history', { params: { page, limit } });
    return res.data;
  },

  deleteHistoryItem: async (historyId: string): Promise<void> => {
    await api.delete(`/users/history/${historyId}`);
  },

  getSavedProducts: async (): Promise<SavedProductItem[]> => {
    const res = await api.get('/users/saved-products');
    return res.data;
  },

  saveProduct: async (productId: string, notes?: string): Promise<SavedProductItem> => {
    const res = await api.post('/users/saved-products', { product_id: productId, notes });
    return res.data;
  },

  removeSavedProduct: async (productId: string): Promise<void> => {
    await api.delete(`/users/saved-products/${productId}`);
  },

  // Admin Endpoints
  getAdminStats: async (): Promise<AdminStats> => {
    const res = await api.get('/admin/stats');
    return res.data;
  },

  getAuditLogs: async (page = 1, limit = 50): Promise<AuditLogItem[]> => {
    const res = await api.get('/admin/audit-logs', { params: { page, limit } });
    return res.data;
  },

  adminCreateProduct: async (data: any): Promise<any> => {
    const res = await api.post('/admin/products', data);
    return res.data;
  },

  adminUpdateProduct: async (productId: string, data: any): Promise<any> => {
    const res = await api.put(`/admin/products/${productId}`, data);
    return res.data;
  },

  adminDeleteProduct: async (productId: string): Promise<void> => {
    await api.delete(`/admin/products/${productId}`);
  },

  getScoringCriteria: async (): Promise<any> => {
    const res = await api.get('/admin/scoring-criteria');
    return res.data;
  },

  updateScoringCriteria: async (data: any): Promise<any> => {
    const res = await api.put('/admin/scoring-criteria', data);
    return res.data;
  },

  getRescoringStatus: async (): Promise<any> => {
    const res = await api.get('/admin/rescore/status');
    return res.data;
  },

  startRescoring: async (target_version = '1.2.0', description = ''): Promise<any> => {
    const res = await api.post('/admin/rescore/start', null, { params: { target_version, description } });
    return res.data;
  },

  adminGetCategories: async (): Promise<any[]> => {
    const res = await api.get('/admin/categories');
    return res.data;
  },

  adminCreateCategory: async (data: any): Promise<any> => {
    const res = await api.post('/admin/categories', data);
    return res.data;
  },

  adminUpdateCategory: async (categoryId: number, data: any): Promise<any> => {
    const res = await api.put(`/admin/categories/${categoryId}`, data);
    return res.data;
  },
};
