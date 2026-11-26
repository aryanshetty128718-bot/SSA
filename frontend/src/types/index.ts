export interface ProductSummary {
  id: string;
  barcode: string;
  name: string;
  brand?: string;
  category_id?: number;
  category_name?: string;
  image_url?: string;
  product_type?: string;
  overall_score?: number;
  nutri_score_grade?: string;
  nova_group?: number;
  data_completeness_score?: number;
  source?: string;
}

export interface NutritionInfo {
  energy_kcal?: number;
  energy_kj?: number;
  sugars_g?: number;
  saturated_fat_g?: number;
  sodium_mg?: number;
  salt_g?: number;
  fiber_g?: number;
  proteins_g?: number;
  fat_g?: number;
  carbohydrates_g?: number;
}

export interface ProConItem {
  parameter: string;
  title: string;
  evidence: string;
}

export interface OfficialReference {
  standard_name: string;
  grade?: string;
  points?: number;
  status: 'computed' | 'not_computable';
  missing_inputs?: string[];
  reference_documentation?: string;
}

export interface ProductAnalysis {
  product_id: string;
  barcode: string;
  product_name: string;
  product_type: 'solid' | 'beverage';
  brand?: string;
  image_url?: string;
  overall_project_score?: number;
  score_band?: string;
  badge_color?: string;
  confidence_score?: number;
  confidence_level?: string;
  missing_parameters?: string[];
  sub_scores?: Record<string, number | null>;
  effective_weights?: Record<string, number>;
  parameter_explanations?: Record<string, string>;
  pros?: ProConItem[];
  cons?: ProConItem[];
  official_reference?: OfficialReference;
  calculated_at?: string;
  scoring_engine_version?: string;
  source?: string;
  nutrition?: NutritionInfo;
  ingredients?: Array<{
    canonical_name: string;
    ins_number?: string;
    is_additive: boolean;
    is_whole_grain?: boolean;
    position_order?: number;
  }>;
}

export interface AlternativeItem {
  id: string;
  barcode: string;
  name: string;
  brand?: string;
  image_url?: string;
  project_category: string;
  tier?: string;
  tier_badge?: string;
  overall_score: number;
  source?: string;
  score_band: string;
  nutri_score_grade?: string;
  score_improvement: number;
  similarity_score: number;
  ingredient_similarity?: number;
  nutrient_similarity?: number;
  parameter_deltas?: Record<string, number>;
  explanation: string;
  trade_offs?: string[];
  trade_off_flags?: string[];
  nutrition?: NutritionInfo;
}

export interface ComparisonResult {
  products: ProductAnalysis[];
  differences: Array<{
    parameter: string;
    label: string;
    unit: string;
    values: Record<string, number | null>;
    best_product_id?: string;
  }>;
  summary: string;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: 'user' | 'admin';
  is_active: boolean;
  created_at?: string;
}

export interface SearchHistoryItem {
  id: string;
  query_term: string;
  query_type: string;
  searched_at: string;
  product_id?: string;
}

export interface SavedProductItem {
  id: string;
  product_id: string;
  notes?: string;
  saved_at: string;
  product?: ProductSummary;
}

export interface AdminStats {
  total_catalog_products: number;
  total_searches_recorded: number;
  total_recommendation_links: number;
  local_hit_ratio_pct: number;
  source_breakdown: Record<string, number>;
  completeness_distribution: {
    high_ge_80pct: number;
    medium_50_to_80pct: number;
    low_lt_50pct: number;
  };
  top_searched_terms: Array<{ term: string; count: number }>;
}

export interface AuditLogItem {
  id: string;
  admin_user_id?: string;
  action: string;
  target_entity: string;
  target_id?: string;
  changes_json?: string;
  created_at: string;
}
