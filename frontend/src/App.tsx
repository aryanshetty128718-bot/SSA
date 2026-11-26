import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { Navbar } from './components/Navbar';
import { ProtectedRoute } from './components/ProtectedRoute';
import { AdminRoute } from './components/AdminRoute';

// Pages
import { HomePage } from './pages/HomePage';
import { ProductAnalysisPage } from './pages/ProductAnalysisPage';
import { AlternativesPage } from './pages/AlternativesPage';
import { ComparisonPage } from './pages/ComparisonPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import { UserDashboardPage } from './pages/UserDashboardPage';
import { AdminDashboardPage } from './pages/AdminDashboardPage';
import { MethodologyPage } from './pages/MethodologyPage';

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <Router>
        <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900 font-sans antialiased">
          <Navbar />
          <main className="flex-1">
            <Routes>
              {/* Public Routes */}
              <Route path="/" element={<HomePage />} />
              <Route path="/products/:barcode" element={<ProductAnalysisPage />} />
              <Route path="/product/:barcode" element={<ProductAnalysisPage />} />
              <Route path="/alternatives" element={<AlternativesPage />} />
              <Route path="/alternatives/:barcode" element={<AlternativesPage />} />
              <Route path="/compare" element={<ComparisonPage />} />
              <Route path="/methodology" element={<MethodologyPage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />

              {/* Protected User Routes */}
              <Route element={<ProtectedRoute />}>
                <Route path="/dashboard" element={<UserDashboardPage />} />
              </Route>

              {/* Protected Admin Routes */}
              <Route element={<AdminRoute />}>
                <Route path="/admin" element={<AdminDashboardPage />} />
              </Route>

              {/* Catch-all redirect */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>

          {/* Footer */}
          <footer className="bg-white border-t border-slate-200 py-6 text-center text-xs text-slate-500">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-2">
              <p>
                Smart Shopping Assistant • Academic MCA Food & Beverage Analysis System
              </p>
              <p className="text-[11px] text-slate-400">
                Nutri-Score is an official reference mark governed by Santé publique France. 0–100 scores represent our project-defined scoring methodology.
              </p>
            </div>
          </footer>
        </div>
      </Router>
    </AuthProvider>
  );
};
export default App;
