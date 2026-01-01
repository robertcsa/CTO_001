// Bot Detail Page Component
'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useBot } from '@/hooks/useBots';
import { useSignals, useOrders, usePortfolio } from '@/hooks/useTrading';
import { useMarketData, useIndicators } from '@/hooks/useMarketData';
import { formatRelativeTime, getSignalColor, getPnlColor } from '@/utils/api';
import { 
  ArrowLeftIcon, 
  ChartBarIcon, 
  SignalIcon,
  ShoppingCartIcon,
  CurrencyDollarIcon,
  PlayIcon,
  PauseIcon,
  StopIcon
} from '@heroicons/react/24/outline';
import CandleChart from '@/components/CandleChart';
import SignalsTable from '@/components/SignalsTable';
import OrdersTable from '@/components/OrdersTable';

export default function BotDetailPage() {
  const params = useParams();
  const router = useRouter();
  const botId = params.id as string;
  
  const { bot, loading: botLoading, refreshBot } = useBot(botId);
  const { signals, loading: signalsLoading } = useSignals(botId, 20);
  const { orders, loading: ordersLoading } = useOrders(botId, 20);
  const { portfolio, loading: portfolioLoading } = usePortfolio(botId);
  const { candles, loading: candlesLoading, refreshData } = useMarketData(
    bot?.symbol || '',
    bot?.timeframe || ''
  );
  const { indicators, loading: indicatorsLoading } = useIndicators(botId, 10);
  
  const [activeTab, setActiveTab] = useState<'overview' | 'chart' | 'signals' | 'orders' | 'portfolio'>('overview');
  const [actionLoading, setActionLoading] = useState(false);

  const { startBot, stopBot, pauseBot, resumeBot } = useBots();

  const handleStart = async () => {
    setActionLoading('start');
    // Implementation would call startBot
    setActionLoading(null);
  };

  const handleStop = async () => {
    setActionLoading('stop');
    // Implementation would call stopBot
    setActionLoading(null);
  };

  const handlePause = async () => {
    setActionLoading('pause');
    // Implementation would call pauseBot
    setActionLoading(null);
  };

  if (botLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!bot) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900">Bot not found</h1>
          <p className="mt-2 text-gray-600">The bot you're looking for doesn't exist.</p>
          <button
            onClick={() => router.push('/bots')}
            className="mt-4 inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <ArrowLeftIcon className="w-4 h-4" />
            Back to Bots
          </button>
        </div>
      </div>
    );
  }

  const tabs = [
    { id: 'overview', name: 'Overview', icon: ChartBarIcon },
    { id: 'chart', name: 'Chart', icon: ChartBarIcon },
    { id: 'signals', name: 'Signals', icon: SignalIcon },
    { id: 'orders', name: 'Orders', icon: ShoppingCartIcon },
    { id: 'portfolio', name: 'Portfolio', icon: CurrencyDollarIcon },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="flex items-center gap-4 mb-8">
        <button
          onClick={() => router.push('/bots')}
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <ArrowLeftIcon className="w-5 h-5" />
        </button>
        <div className="flex-1">
          <h1 className="text-3xl font-bold text-gray-900">{bot.name}</h1>
          <p className="text-gray-600 mt-1">
            {bot.symbol} • {bot.timeframe} • {bot.strategy_id.replace('_', ' ').toUpperCase()}
          </p>
        </div>
        <div className="flex gap-2">
          {bot.state === 'stopped' && (
            <button
              onClick={handleStart}
              disabled={actionLoading === 'start'}
              className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
            >
              <PlayIcon className="w-4 h-4" />
              {actionLoading === 'start' ? 'Starting...' : 'Start'}
            </button>
          )}
          
          {bot.state === 'running' && (
            <>
              <button
                onClick={handlePause}
                disabled={actionLoading === 'pause'}
                className="flex items-center gap-2 px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 disabled:opacity-50"
              >
                <PauseIcon className="w-4 h-4" />
                {actionLoading === 'pause' ? 'Pausing...' : 'Pause'}
              </button>
              <button
                onClick={handleStop}
                disabled={actionLoading === 'stop'}
                className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
              >
                <StopIcon className="w-4 h-4" />
                {actionLoading === 'stop' ? 'Stopping...' : 'Stop'}
              </button>
            </>
          )}
        </div>
      </div>

      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Status</p>
              <p className="text-2xl font-semibold text-gray-900 capitalize">{bot.state}</p>
            </div>
            <div className={`w-3 h-3 rounded-full ${
              bot.state === 'running' ? 'bg-green-500' : 
              bot.state === 'stopped' ? 'bg-gray-400' : 
              bot.state === 'error' ? 'bg-red-500' : 'bg-yellow-500'
            }`}></div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-sm font-medium text-gray-600">Last Run</p>
          <p className="text-2xl font-semibold text-gray-900">
            {bot.last_run_at ? formatRelativeTime(bot.last_run_at) : 'Never'}
          </p>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-sm font-medium text-gray-600">Signals Today</p>
          <p className="text-2xl font-semibold text-gray-900">
            {signals.filter(s => new Date(s.timestamp).toDateString() === new Date().toDateString()).length}
          </p>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-sm font-medium text-gray-600">Total P&L</p>
          <p className={`text-2xl font-semibold ${getPnlColor(portfolio?.total_pnl || 0)}`}>
            {portfolio ? `${portfolio.total_pnl >= 0 ? '+' : ''}${portfolio.total_pnl.toFixed(2)}` : '$0.00'}
          </p>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-gray-200 mb-8">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center gap-2 py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Icon className="w-4 h-4" />
                {tab.name}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="min-h-[600px]">
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className="space-y-6">
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Bot Configuration</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Asset Type:</span>
                    <span className="font-medium">{bot.asset_type.toUpperCase()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Symbol:</span>
                    <span className="font-medium">{bot.symbol}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Timeframe:</span>
                    <span className="font-medium">{bot.timeframe}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Strategy:</span>
                    <span className="font-medium">{bot.strategy_id.replace('_', ' ').toUpperCase()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Interval:</span>
                    <span className="font-medium">{bot.interval_seconds}s</span>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Strategy Parameters</h3>
                <div className="space-y-3">
                  {bot.params && Object.entries(bot.params).map(([key, value]) => (
                    <div key={key} className="flex justify-between">
                      <span className="text-gray-600 capitalize">{key.replace('_', ' ')}:</span>
                      <span className="font-medium">{String(value)}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="space-y-6">
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Signals</h3>
                <div className="space-y-3">
                  {signals.slice(0, 5).map((signal) => (
                    <div key={signal.id} className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getSignalColor(signal.signal_type)}`}>
                          {signal.signal_type}
                        </span>
                        <span className="text-sm text-gray-600">
                          {formatRelativeTime(signal.timestamp)}
                        </span>
                      </div>
                      <span className="text-sm font-medium">
                        {(signal.confidence * 100).toFixed(1)}%
                      </span>
                    </div>
                  ))}
                  {signals.length === 0 && (
                    <p className="text-gray-500 text-center py-4">No signals yet</p>
                  )}
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Orders</h3>
                <div className="space-y-3">
                  {orders.slice(0, 5).map((order) => (
                    <div key={order.id} className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                          order.side === 'BUY' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}>
                          {order.side}
                        </span>
                        <span className="text-sm text-gray-600">
                          {formatRelativeTime(order.created_at)}
                        </span>
                      </div>
                      <span className={`text-sm font-medium ${getPnlColor(order.pnl)}`}>
                        {order.pnl >= 0 ? '+' : ''}{order.pnl.toFixed(2)}
                      </span>
                    </div>
                  ))}
                  {orders.length === 0 && (
                    <p className="text-gray-500 text-center py-4">No orders yet</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'chart' && (
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Price Chart</h3>
              <button
                onClick={refreshData}
                className="px-3 py-1.5 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
              >
                Refresh Data
              </button>
            </div>
            <CandleChart candles={candles} indicators={indicators} />
          </div>
        )}

        {activeTab === 'signals' && (
          <div className="bg-white rounded-lg shadow p-6">
            <SignalsTable signals={signals} loading={signalsLoading} />
          </div>
        )}

        {activeTab === 'orders' && (
          <div className="bg-white rounded-lg shadow p-6">
            <OrdersTable orders={orders} loading={ordersLoading} />
          </div>
        )}

        {activeTab === 'portfolio' && (
          <div className="space-y-6">
            {portfolio && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Total Value</h3>
                  <p className="text-3xl font-bold text-gray-900">
                    ${portfolio.total_value.toFixed(2)}
                  </p>
                </div>
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Total P&L</h3>
                  <p className={`text-3xl font-bold ${getPnlColor(portfolio.total_pnl)}`}>
                    {portfolio.total_pnl >= 0 ? '+' : ''}${portfolio.total_pnl.toFixed(2)}
                  </p>
                  <p className="text-sm text-gray-600 mt-1">
                    ({portfolio.pnl_percentage >= 0 ? '+' : ''}{portfolio.pnl_percentage.toFixed(2)}%)
                  </p>
                </div>
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Available Balance</h3>
                  <p className="text-3xl font-bold text-gray-900">
                    ${portfolio.available_balance.toFixed(2)}
                  </p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}