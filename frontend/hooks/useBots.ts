// Bot management hooks
'use client';

import { useState, useEffect, useCallback } from 'react';
import { apiClient, startPolling } from '@/utils/api';
import { Bot, BotStatus, BotCreate, BotUpdate } from '@/types/api';
import toast from 'react-hot-toast';

export const useBots = () => {
  const [bots, setBots] = useState<Bot[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchBots = useCallback(async () => {
    try {
      setLoading(true);
      const data = await apiClient.get<Bot[]>('/bots');
      setBots(data);
    } catch (error) {
      console.error('Failed to fetch bots:', error);
      toast.error('Failed to load bots');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchBots();
  }, [fetchBots]);

  const createBot = async (botData: BotCreate): Promise<Bot | null> => {
    try {
      const newBot = await apiClient.post<Bot>('/bots', botData);
      setBots(prev => [newBot, ...prev]);
      toast.success('Bot created successfully');
      return newBot;
    } catch (error: any) {
      console.error('Failed to create bot:', error);
      toast.error(error.error?.message || 'Failed to create bot');
      return null;
    }
  };

  const updateBot = async (botId: string, botData: BotUpdate): Promise<Bot | null> => {
    try {
      const updatedBot = await apiClient.put<Bot>(`/bots/${botId}`, botData);
      setBots(prev => prev.map(bot => bot.id === botId ? updatedBot : bot));
      toast.success('Bot updated successfully');
      return updatedBot;
    } catch (error: any) {
      console.error('Failed to update bot:', error);
      toast.error(error.error?.message || 'Failed to update bot');
      return null;
    }
  };

  const deleteBot = async (botId: string): Promise<boolean> => {
    try {
      await apiClient.delete(`/bots/${botId}`);
      setBots(prev => prev.filter(bot => bot.id !== botId));
      toast.success('Bot deleted successfully');
      return true;
    } catch (error: any) {
      console.error('Failed to delete bot:', error);
      toast.error(error.error?.message || 'Failed to delete bot');
      return false;
    }
  };

  const startBot = async (botId: string): Promise<boolean> => {
    try {
      await apiClient.post(`/bots/${botId}/start`);
      // Update bot state
      setBots(prev => prev.map(bot => 
        bot.id === botId ? { ...bot, state: 'running' } : bot
      ));
      toast.success('Bot started successfully');
      return true;
    } catch (error: any) {
      console.error('Failed to start bot:', error);
      toast.error(error.error?.message || 'Failed to start bot');
      return false;
    }
  };

  const stopBot = async (botId: string): Promise<boolean> => {
    try {
      await apiClient.post(`/bots/${botId}/stop`);
      // Update bot state
      setBots(prev => prev.map(bot => 
        bot.id === botId ? { ...bot, state: 'stopped' } : bot
      ));
      toast.success('Bot stopped successfully');
      return true;
    } catch (error: any) {
      console.error('Failed to stop bot:', error);
      toast.error(error.error?.message || 'Failed to stop bot');
      return false;
    }
  };

  const pauseBot = async (botId: string): Promise<boolean> => {
    try {
      await apiClient.post(`/bots/${botId}/pause`);
      setBots(prev => prev.map(bot => 
        bot.id === botId ? { ...bot, state: 'paused' } : bot
      ));
      toast.success('Bot paused successfully');
      return true;
    } catch (error: any) {
      console.error('Failed to pause bot:', error);
      toast.error(error.error?.message || 'Failed to pause bot');
      return false;
    }
  };

  const resumeBot = async (botId: string): Promise<boolean> => {
    try {
      await apiClient.post(`/bots/${botId}/resume`);
      setBots(prev => prev.map(bot => 
        bot.id === botId ? { ...bot, state: 'running' } : bot
      ));
      toast.success('Bot resumed successfully');
      return true;
    } catch (error: any) {
      console.error('Failed to resume bot:', error);
      toast.error(error.error?.message || 'Failed to resume bot');
      return false;
    }
  };

  const getBotStatus = async (botId: string): Promise<BotStatus | null> => {
    try {
      return await apiClient.get<BotStatus>(`/bots/${botId}/status`);
    } catch (error) {
      console.error('Failed to get bot status:', error);
      return null;
    }
  };

  return {
    bots,
    loading,
    fetchBots,
    createBot,
    updateBot,
    deleteBot,
    startBot,
    stopBot,
    pauseBot,
    resumeBot,
    getBotStatus,
  };
};

export const useBot = (botId: string) => {
  const [bot, setBot] = useState<Bot | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchBot = useCallback(async () => {
    if (!botId) return;
    
    try {
      setLoading(true);
      const data = await apiClient.get<Bot>(`/bots/${botId}`);
      setBot(data);
    } catch (error) {
      console.error('Failed to fetch bot:', error);
      toast.error('Failed to load bot');
    } finally {
      setLoading(false);
    }
  }, [botId]);

  useEffect(() => {
    fetchBot();
  }, [fetchBot]);

  const refreshBot = () => {
    fetchBot();
  };

  return {
    bot,
    loading,
    refreshBot,
  };
};