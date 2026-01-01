// Frontend utilities

import { ApiResponse, ApiError } from '@/types/api';

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export class ApiClient {
  private baseURL: string;
  private token?: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  setToken(token: string) {
    this.token = token;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        error: {
          type: 'NetworkError',
          message: 'Network request failed',
          status_code: response.status
        }
      }));
      
      throw error;
    }

    return response.json();
  }

  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  async post<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async put<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }
}

export const apiClient = new ApiClient();

// Authentication helpers
export const setAuthToken = (token: string) => {
  if (typeof window !== 'undefined') {
    localStorage.setItem('auth_token', token);
    apiClient.setToken(token);
  }
};

export const getAuthToken = (): string | null => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('auth_token');
  }
  return null;
};

export const removeAuthToken = () => {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('auth_token');
    apiClient.setToken('');
  }
};

// Format helpers
export const formatPrice = (price: number, decimals: number = 2): string => {
  return price.toFixed(decimals);
};

export const formatPercentage = (value: number, decimals: number = 2): string => {
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(decimals)}%`;
};

export const formatDateTime = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleString();
};

export const formatRelativeTime = (dateString: string): string => {
  const date = new Date(dateString);
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (diffInSeconds < 60) {
    return `${diffInSeconds}s ago`;
  } else if (diffInSeconds < 3600) {
    return `${Math.floor(diffInSeconds / 60)}m ago`;
  } else if (diffInSeconds < 86400) {
    return `${Math.floor(diffInSeconds / 3600)}h ago`;
  } else {
    return `${Math.floor(diffInSeconds / 86400)}d ago`;
  }
};

// Validation helpers
export const isValidEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

export const isValidSymbol = (symbol: string): boolean => {
  const symbolRegex = /^[A-Z]{2,10}$/;
  return symbolRegex.test(symbol.toUpperCase());
};

export const isValidTimeframe = (timeframe: string): boolean => {
  const validTimeframes = ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w'];
  return validTimeframes.includes(timeframe);
};

// Color helpers
export const getSignalColor = (signalType: string): string => {
  switch (signalType) {
    case 'BUY':
      return 'text-green-600 bg-green-100';
    case 'SELL':
      return 'text-red-600 bg-red-100';
    case 'HOLD':
      return 'text-yellow-600 bg-yellow-100';
    default:
      return 'text-gray-600 bg-gray-100';
  }
};

export const getStateColor = (state: string): string => {
  switch (state) {
    case 'running':
      return 'text-green-600 bg-green-100';
    case 'stopped':
      return 'text-gray-600 bg-gray-100';
    case 'error':
      return 'text-red-600 bg-red-100';
    case 'paused':
      return 'text-yellow-600 bg-yellow-100';
    default:
      return 'text-gray-600 bg-gray-100';
  }
};

export const getPnlColor = (pnl: number): string => {
  if (pnl > 0) {
    return 'text-green-600';
  } else if (pnl < 0) {
    return 'text-red-600';
  } else {
    return 'text-gray-600';
  }
};

// Debounce hook
export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  delay: number
): ((...args: Parameters<T>) => void) => {
  let timeoutId: NodeJS.Timeout;
  
  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func.apply(null, args), delay);
  };
};

// Polling helper
export const startPolling = (
  callback: () => void,
  interval: number = 5000
): (() => void) => {
  const intervalId = setInterval(callback, interval);
  
  return () => {
    clearInterval(intervalId);
  };
};