// Create/Edit Bot Modal Component
'use client';

import { useState, useEffect } from 'react';
import { Bot, BotCreate, AssetType, StrategyId } from '@/types/api';
import { useBots } from '@/hooks/useBots';
import { XMarkIcon } from '@heroicons/react/24/outline';

interface CreateBotModalProps {
  bot?: Bot | null;
  onClose: () => void;
}

const ASSET_TYPES = [
  { value: AssetType.CRYPTO, label: 'Cryptocurrency' },
  { value: AssetType.FOREX, label: 'Forex' },
  { value: AssetType.STOCKS, label: 'Stocks' },
];

const TIMEFRAMES = [
  { value: '1m', label: '1 Minute' },
  { value: '5m', label: '5 Minutes' },
  { value: '15m', label: '15 Minutes' },
  { value: '30m', label: '30 Minutes' },
  { value: '1h', label: '1 Hour' },
  { value: '4h', label: '4 Hours' },
  { value: '1d', label: '1 Day' },
  { value: '1w', label: '1 Week' },
];

const STRATEGIES = [
  { value: StrategyId.BLUE_SKY, label: 'Blue Sky (Breakout)' },
];

const COMMON_SYMBOLS = {
  [AssetType.CRYPTO]: ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'DOTUSDT', 'LINKUSDT', 'XRPUSDT'],
  [AssetType.FOREX]: ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD', 'USDCHF'],
  [AssetType.STOCKS]: ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'META'],
};

export default function CreateBotModal({ bot, onClose }: CreateBotModalProps) {
  const { createBot, updateBot } = useBots();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    asset_type: AssetType.CRYPTO,
    symbol: '',
    timeframe: '1h',
    strategy_id: StrategyId.BLUE_SKY,
    interval_seconds: 60,
    params: {
      lookback: 20,
      min_confidence: 0.6,
    },
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (bot) {
      setFormData({
        name: bot.name,
        asset_type: bot.asset_type,
        symbol: bot.symbol,
        timeframe: bot.timeframe,
        strategy_id: bot.strategy_id,
        interval_seconds: bot.interval_seconds,
        params: bot.params || {
          lookback: 20,
          min_confidence: 0.6,
        },
      });
    }
  }, [bot]);

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }

    if (!formData.symbol.trim()) {
      newErrors.symbol = 'Symbol is required';
    }

    if (formData.interval_seconds < 30) {
      newErrors.interval_seconds = 'Interval must be at least 30 seconds';
    }

    if (formData.params.lookback < 5 || formData.params.lookback > 100) {
      newErrors.lookback = 'Lookback must be between 5 and 100';
    }

    if (formData.params.min_confidence < 0.1 || formData.params.min_confidence > 1.0) {
      newErrors.min_confidence = 'Min confidence must be between 0.1 and 1.0';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setLoading(true);
    try {
      const botData: BotCreate = {
        name: formData.name,
        asset_type: formData.asset_type,
        symbol: formData.symbol.toUpperCase(),
        timeframe: formData.timeframe,
        strategy_id: formData.strategy_id,
        interval_seconds: formData.interval_seconds,
        params: formData.params,
      };

      if (bot) {
        await updateBot(bot.id, botData);
      } else {
        await createBot(botData);
      }
      
      onClose();
    } catch (error) {
      console.error('Failed to save bot:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const handleParamChange = (param: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      params: { ...prev.params, [param]: value }
    }));
    
    // Clear error when user starts typing
    if (errors[param]) {
      setErrors(prev => ({ ...prev, [param]: '' }));
    }
  };

  const availableSymbols = COMMON_SYMBOLS[formData.asset_type] || [];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-xl font-semibold text-gray-900">
            {bot ? 'Edit Bot' : 'Create New Bot'}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Bot Name *
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  errors.name ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="My Trading Bot"
              />
              {errors.name && <p className="text-red-500 text-sm mt-1">{errors.name}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Asset Type *
              </label>
              <select
                value={formData.asset_type}
                onChange={(e) => handleInputChange('asset_type', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {ASSET_TYPES.map(type => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Symbol *
              </label>
              <div className="relative">
                <input
                  type="text"
                  value={formData.symbol}
                  onChange={(e) => handleInputChange('symbol', e.target.value)}
                  className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    errors.symbol ? 'border-red-500' : 'border-gray-300'
                  }`}
                  placeholder="BTCUSDT"
                />
                <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
                  <select
                    value=""
                    onChange={(e) => e.target.value && handleInputChange('symbol', e.target.value)}
                    className="text-sm border-0 bg-transparent text-gray-500 focus:outline-none"
                  >
                    <option value="">Common</option>
                    {availableSymbols.map(symbol => (
                      <option key={symbol} value={symbol}>
                        {symbol}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              {errors.symbol && <p className="text-red-500 text-sm mt-1">{errors.symbol}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Timeframe *
              </label>
              <select
                value={formData.timeframe}
                onChange={(e) => handleInputChange('timeframe', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {TIMEFRAMES.map(tf => (
                  <option key={tf.value} value={tf.value}>
                    {tf.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Strategy *
              </label>
              <select
                value={formData.strategy_id}
                onChange={(e) => handleInputChange('strategy_id', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {STRATEGIES.map(strategy => (
                  <option key={strategy.value} value={strategy.value}>
                    {strategy.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Interval (seconds) *
              </label>
              <input
                type="number"
                min="30"
                max="86400"
                value={formData.interval_seconds}
                onChange={(e) => handleInputChange('interval_seconds', parseInt(e.target.value))}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  errors.interval_seconds ? 'border-red-500' : 'border-gray-300'
                }`}
              />
              {errors.interval_seconds && <p className="text-red-500 text-sm mt-1">{errors.interval_seconds}</p>}
            </div>
          </div>

          <div className="border-t pt-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Strategy Parameters</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Lookback Period
                </label>
                <input
                  type="number"
                  min="5"
                  max="100"
                  value={formData.params.lookback}
                  onChange={(e) => handleParamChange('lookback', parseInt(e.target.value))}
                  className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    errors.lookback ? 'border-red-500' : 'border-gray-300'
                  }`}
                />
                <p className="text-gray-500 text-sm mt-1">
                  Number of previous candles to check for breakout
                </p>
                {errors.lookback && <p className="text-red-500 text-sm mt-1">{errors.lookback}</p>}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Minimum Confidence
                </label>
                <input
                  type="number"
                  min="0.1"
                  max="1.0"
                  step="0.1"
                  value={formData.params.min_confidence}
                  onChange={(e) => handleParamChange('min_confidence', parseFloat(e.target.value))}
                  className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    errors.min_confidence ? 'border-red-500' : 'border-gray-300'
                  }`}
                />
                <p className="text-gray-500 text-sm mt-1">
                  Minimum confidence threshold for buy signals (0.1 - 1.0)
                </p>
                {errors.min_confidence && <p className="text-red-500 text-sm mt-1">{errors.min_confidence}</p>}
              </div>
            </div>
          </div>

          <div className="flex gap-3 pt-6 border-t">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Saving...' : (bot ? 'Update Bot' : 'Create Bot')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}