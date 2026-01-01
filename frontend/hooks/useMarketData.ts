// Market data hooks
'use client';

import { useState, useEffect, useCallback } from 'react';
import { apiClient } from '@/utils/api';
import { MarketCandle, Indicator } from '@/types/api';
import toast from 'react-hot-toast';

export const useMarketData = (symbol: string, timeframe: string) => {
  const [candles, setCandles] = useState<MarketCandle[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchCandles = useCallback(async () => {
    if (!symbol || !timeframe) return;
    
    try {
      setLoading(true);
      const data = await apiClient.get<{ candles: MarketCandle[] }>(
        `/market/candles?symbol=${symbol}&timeframe=${timeframe}&limit=100`
      );
      setCandles(data.candles);
    } catch (error) {
      console.error('Failed to fetch candles:', error);
      toast.error('Failed to load market data');
    } finally {
      setLoading(false);
    }
  }, [symbol, timeframe]);

  useEffect(() => {
    fetchCandles();
  }, [fetchCandles]);

  const refreshData = async () => {
    try {
      await apiClient.post('/market/refresh', {
        symbol,
        timeframe,
        limit: 100
      });
      await fetchCandles();
      toast.success('Market data refreshed');
    } catch (error: any) {
      console.error('Failed to refresh data:', error);
      toast.error('Failed to refresh market data');
    }
  };

  return {
    candles,
    loading,
    refreshData,
  };
};

export const useIndicators = (botId: string, limit: number = 50) => {
  const [indicators, setIndicators] = useState<Indicator[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchIndicators = useCallback(async () => {
    if (!botId) return;
    
    try {
      setLoading(true);
      const data = await apiClient.get<Indicator[]>(
        `/market/indicators?bot_id=${botId}&limit=${limit}`
      );
      setIndicators(data);
    } catch (error) {
      console.error('Failed to fetch indicators:', error);
    } finally {
      setLoading(false);
    }
  }, [botId, limit]);

  useEffect(() => {
    fetchIndicators();
  }, [fetchIndicators]);

  return {
    indicators,
    loading,
    refreshIndicators: fetchIndicators,
  };
};