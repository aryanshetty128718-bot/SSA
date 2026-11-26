/**
 * API Client with Axios.
 * 
 * SECURITY ARCHITECTURE & TOKEN STORAGE TRADE-OFF:
 * JWT access tokens are stored in browser localStorage for statutory client-side
 * authentication across tab sessions and single-page routing without server-session state.
 * Trade-Off Analysis:
 * - Advantage: Completely stateless API, simple cross-origin decoupling, resilient to CSRF.
 * - XSS Risk Consideration: LocalStorage is accessible by JavaScript in the same origin.
 *   Mitigation in SSA: All untrusted product texts and crowdsourced OFF inputs are rendered
 *   using React DOM JSX text bindings (auto-escaped, no dangerouslySetInnerHTML used anywhere),
 *   Content Security Policy headers are enforced by FastAPI, and token lifetime is restricted.
 */
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Request interceptor: attach Authorization header if token exists in localStorage
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('ssa_auth_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: handle 401 Unauthorized globally
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Clear token and fire auth-state event
      localStorage.removeItem('ssa_auth_token');
      localStorage.removeItem('ssa_auth_user');
      window.dispatchEvent(new Event('auth-logout'));
    }
    return Promise.reject(error);
  }
);
