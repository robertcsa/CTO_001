// Authentication hooks
'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient, setAuthToken, getAuthToken, removeAuthToken } from '@/utils/api';
import { User } from '@/types/api';
import toast from 'react-hot-toast';

export const useAuth = () => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [token, setTokenState] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    const initAuth = async () => {
      const savedToken = getAuthToken();
      if (savedToken) {
        apiClient.setToken(savedToken);
        setTokenState(savedToken);
        
        try {
          const userData = await apiClient.get<User>('/auth/me');
          setUser(userData);
        } catch (error) {
          console.error('Failed to get user info:', error);
          removeAuthToken();
          setTokenState(null);
        }
      }
      setLoading(false);
    };

    initAuth();
  }, []);

  const login = async (email: string, password: string): Promise<boolean> => {
    try {
      setLoading(true);
      const response = await apiClient.post<{ access_token: string; token_type: string; expires_in: number }>(
        '/auth/login-json',
        { email, password }
      );

      setAuthToken(response.access_token);
      setTokenState(response.access_token);
      
      const userData = await apiClient.get<User>('/auth/me');
      setUser(userData);
      
      toast.success('Login successful!');
      return true;
    } catch (error: any) {
      console.error('Login error:', error);
      toast.error(error.error?.message || 'Login failed');
      return false;
    } finally {
      setLoading(false);
    }
  };

  const register = async (email: string, password: string): Promise<boolean> => {
    try {
      setLoading(true);
      await apiClient.post('/auth/register', { email, password });
      
      toast.success('Registration successful! Please login.');
      return true;
    } catch (error: any) {
      console.error('Registration error:', error);
      toast.error(error.error?.message || 'Registration failed');
      return false;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    removeAuthToken();
    setTokenState(null);
    setUser(null);
    router.push('/login');
    toast.success('Logged out successfully');
  };

  return {
    user,
    token,
    loading,
    login,
    register,
    logout,
    isAuthenticated: !!user,
  };
};