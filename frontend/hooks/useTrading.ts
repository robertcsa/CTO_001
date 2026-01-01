// Trading data hooks
'use client';

import { useState, useEffect, useCallback } from 'react';
import { apiClient, startPolling } from '@/utils/api';
import { Signal, Order, PortfolioSummary } from '@/types/api';
import toast from 'react-hot-toast';

export const useSignals = (botId: string, limit: number = 50) => {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchSignals = useCallback(async () => {
    if (!botId) return;
    
    try {
      setLoading(true);
      const data = await apiClient.get<{ signals: Signal[] }>(
        `/trading/signals?bot_id=${botId}&limit=${limit}`
      );
      setSignals(data.signals);
    } catch (error) {
      console.error('Failed to fetch signals:', error);
    } finally {
      setLoading(false);
    }
  }, [botId, limit]);

  useEffect(() => {
    fetchSignals();
    
    // Set up polling for real-time updates
    const stopPolling = startPolling(fetchSignals, 5000); // Poll every 5 seconds
    
    return stopPolling;
  }, [fetchSignals]);

  return {
    signals,
    loading,
    refreshSignals: fetchSignals,
  };
};

export const useOrders = (botId: string, limit: number = 50) => {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchOrders = useCallback(async () => {
    if (!botId) return;
    
    try {
      setLoading(true);
      const data = await apiClient.get<{ orders: Order[] }>(
        `/trading/orders?bot_id=${botId}&limit=${limit}`
      );
      setOrders(data.orders);
    } catch (error) {
      console.error('Failed to fetch orders:', error);
    } finally {
      setLoading(false);
    }
  }, [botId, limit]);

  useEffect(() => {
    fetchOrders();
    
    // Set up polling for real-time updates
    const stopPolling = startPolling(fetchOrders, 5000); // Poll every 5 seconds
    
    return stopPolling;
  }, [fetchOrders]);

  const cancelOrder = async (orderId: string): Promise<boolean> => {
    try {
      await apiClient.post(`/trading/orders/${orderId}/cancel`);
      // Remove cancelled order from list
      setOrders(prev => prev.filter(order => order.id !== orderId));
      toast.success('Order cancelled successfully');
      return true;
    } catch (error: any) {
      console.error('Failed to cancel order:', error);
      toast.error(error.error?.message || 'Failed to cancel order');
      return false;
    }
  };

  return {
    orders,
    loading,
    refreshOrders: fetchOrders,
    cancelOrder,
  };
};

export const usePortfolio = (botId: string) => {
  const [portfolio, setPortfolio] = useState<PortfolioSummary | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchPortfolio = useCallback(async () => {
    if (!botId) return;
    
    try {
      setLoading(true);
      const data = await apiClient.get<{ summary: PortfolioSummary }>(
        `/trading/portfolio/${botId}`
      );
      setPortfolio(data.summary);
    } catch (error) {
      console.error('Failed to fetch portfolio:', error);
    } finally {
      setLoading(false);
    }
  }, [botId]);

  useEffect(() => {
    fetchPortfolio();
    
    // Set up polling for real-time updates
    const stopPolling = startPolling(fetchPortfolio, 10000); // Poll every 10 seconds
    
    return stopPolling;
  }, [fetchPortfolio]);

  return {
    portfolio,
    loading,
    refreshPortfolio: fetchPortfolio,
  };
};

export const usePosition = (botId: string) => {
  const [position, setPosition] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const fetchPosition = useCallback(async () => {
    if (!botId) return;
    
    try {
      setLoading(true);
      const data = await apiClient.get(`/trading/position/${botId}`);
      setPosition(data);
    } catch (error) {
      console.error('Failed to fetch position:', error);
    } finally {
      setLoading(false);
    }
  }, [botId]);

  useEffect(() => {
    fetchPosition();
    
    // Set up polling for real-time updates
    const stopPolling = startPolling(fetchPosition, 3000); // Poll every 3 seconds
    
    return stopPolling;
  }, [fetchPosition]);

  return {
    position,
    loading,
    refreshPosition: fetchPosition,
  };
};