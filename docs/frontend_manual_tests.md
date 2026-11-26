# Frontend Manual Testing Checklist & Responsive Verification

**Project:** Smart Shopping Assistant (SSA) — MCA Web Application  
**Target Viewports:** 
- Mobile: `390px` width (iPhone 12/13/14 portrait)
- Desktop: `1280px+` width (Standard display)

---

## 12-Point Manual Test Verification Matrix

| # | Test Scenario | Steps | Expected Outcome | Desktop (1280px) | Mobile (390px) | Status |
|---|---|---|---|:---:|:---:|:---:|
| **1** | **Homepage Barcode Search (Valid)** | Enter `3017620422003` into the search bar and press Enter or click Analyze. | Validated instantly via client-side GS1 GTIN check digit; navigates to `/products/3017620422003`. | Card layout & autocomplete | Stacked input & full-width button | **PASS** |
| **2** | **Homepage Barcode Search (Invalid Check Digit)** | Enter `3017620422004` (corrupted check digit). | Client-side validator halts navigation and shows explicit error: `Invalid check digit (4). Expected 3.` | Inline red alert banner | Inline red alert banner | **PASS** |
| **3** | **Homepage Text Search & Quick Tags** | Type `cola` or click quick category tag `Soft Drinks`. | Toggles name-based search, queries `/api/v1/products/search`, and displays matching product cards. | 4-column responsive grid | 1-column vertically scrollable | **PASS** |
| **4** | **Product Analysis Page (Solid)** | Load `/products/3017620422003` (Nutella). | Score gauge displays `23.5` (Avoid / Discretionary). Nutri-Score badge displays `E` (Official Reference Standard). Radar chart shows 8 parameters. Sugar cap warning visible. | 2-column layout (Summary left, Tabs right) | 1-column vertical stack with sticky tab bar | **PASS** |
| **5** | **Product Analysis Page (Beverage)** | Load `/products/5449000000996` (Coca-Cola Original). | Score gauge displays `21.2`. Beverage sugar priority (40% weight) clearly documented in effective weights breakdown. High sugar con is highlighted in red. | Radar/Bar toggles render smoothly | Horizontal scroll on radar chart container | **PASS** |
| **6** | **Product Analysis Page (Incomplete)** | Load product with missing laboratory nutrients (e.g. `Artisan Fruit Bar`). | Nutri-Score badge renders `Not Computable` with missing inputs list. Overall score confidence badge reflects partial data confidence. | Warning box with missing fields list | Warning box with missing fields list | **PASS** |
| **7** | **Healthier Alternatives Recommendation** | From Nutella page, click "Find Healthier Alternatives" (`/alternatives/3017620422003`). | Displays category-coherent spreads (e.g. Peanut Butter, Almond Butter, Hazelnut Dark Spread). Chewing gum and mints are 100% excluded. Delta chips show +/- sugar & fat differences. | 3-column card grid | 1-column card stack | **PASS** |
| **8** | **Multi-Product Comparison (2 to 4 Products)** | Select Nutella and 2 healthier spreads, click "Compare Selected" (`/compare?ids=...`). | Side-by-side comparison matrix renders with best value in each row highlighted in emerald green. Recharts profile chart compares values visually. | Multi-column table with fixed header | Horizontally scrollable table with touch swipe | **PASS** |
| **9** | **Authentication Flow (Register & Login)** | 1. Register with new credentials (password validation enforces $\ge 8$ chars + digit).<br>2. Sign in at `/login`. | JWT stored in `localStorage`; navigation bar switches to show user initials and dashboard links. | Profile dropdown / avatar | Collapsible hamburger drawer | **PASS** |
| **10** | **User Dashboard (History & Saved Items)** | Navigate to `/dashboard` while logged in. | Lists recent search queries and saved bookmarks. Allows editing personal comparison notes and deleting history rows. | 2-column saved card grid | 1-column saved card grid | **PASS** |
| **11** | **Admin Dashboard & Scoring Config** | Log in with admin credentials and navigate to `/admin`. Non-admin access redirected. | 1. Stats overview with distribution charts.<br>2. Catalog table with search and delete.<br>3. Scoring criteria editor validates $\sum w_i = 1.00$ before saving.<br>4. Audit log stream. | Multi-tab admin interface | Tab navigation with horizontal scroll | **PASS** |
| **12** | **Methodology Documentation** | Navigate to `/methodology`. | Explains 0–100 Project Score, Nutri-Score 2023 algorithm, Model A/B ML pipeline, and includes prominent medical/academic disclaimers. | Clean readable article layout | Fluid responsive prose typography | **PASS** |

---

## Responsive Breakpoint Observations & Fixes

1. **Mobile Drawer (390px):**
   - Implemented responsive mobile drawer menu in `Navbar.tsx` using Lucide `Menu` / `X` toggles.
   - All interactive touch targets (buttons, search inputs, chips) adhere to $\ge 44\text{px}$ minimum height.
2. **Recharts SVG Containers:**
   - Wrapped all `RadarChart` and `BarChart` components in responsive `<div>` wrappers with explicit min-heights and fluid aspect ratios to prevent SVG overflow on narrow mobile viewports.
3. **Data Tables:**
   - Both `NutritionTable.tsx` and `ComparisonTable.tsx` include outer `overflow-x-auto` wrappers to guarantee horizontal swipe navigation without breaking layout containers on small devices.
