// ============================================
// FaceFind Frontend - Auth Context
// ============================================
import { createContext, useContext, useState, useEffect } from 'react';
import { getAdminProfile } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [admin, setAdmin] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    const token = localStorage.getItem('facefind_token');
    if (!token) {
      setLoading(false);
      return;
    }
    try {
      const res = await getAdminProfile();
      setAdmin(res.data);
    } catch {
      localStorage.removeItem('facefind_token');
      setAdmin(null);
    }
    setLoading(false);
  };

  const login = (token, adminData) => {
    localStorage.setItem('facefind_token', token);
    setAdmin(adminData);
  };

  const logout = () => {
    localStorage.removeItem('facefind_token');
    setAdmin(null);
  };

  return (
    <AuthContext.Provider value={{ admin, loading, login, logout, checkAuth }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
