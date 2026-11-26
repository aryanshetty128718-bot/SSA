import React, { createContext, useContext, useState, useEffect } from 'react';
import type { User } from '../types';
import { endpoints } from '../api/endpoints';

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, fullName: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
  isAdmin: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => {
    const saved = localStorage.getItem('ssa_auth_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState<string | null>(() => {
    return localStorage.getItem('ssa_auth_token');
  });
  const [loading, setLoading] = useState<boolean>(true);

  // Validate token on mount
  useEffect(() => {
    const initAuth = async () => {
      if (token) {
        try {
          const profile = await endpoints.getMe();
          setUser(profile);
          localStorage.setItem('ssa_auth_user', JSON.stringify(profile));
        } catch {
          logout();
        }
      }
      setLoading(false);
    };

    initAuth();

    const handleLogoutEvent = () => logout();
    window.addEventListener('auth-logout', handleLogoutEvent);
    return () => window.removeEventListener('auth-logout', handleLogoutEvent);
  }, []);

  const login = async (email: string, password: string) => {
    const res = await endpoints.login({ email, password });
    setToken(res.access_token);
    setUser(res.user);
    localStorage.setItem('ssa_auth_token', res.access_token);
    localStorage.setItem('ssa_auth_user', JSON.stringify(res.user));
  };

  const register = async (email: string, fullName: string, password: string) => {
    await endpoints.register({ email, full_name: fullName, password });
    // Auto-login after registration
    await login(email, password);
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('ssa_auth_token');
    localStorage.removeItem('ssa_auth_user');
  };

  const isAuthenticated = !!token && !!user;
  const isAdmin = user?.role === 'admin';

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        login,
        register,
        logout,
        isAuthenticated,
        isAdmin,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
