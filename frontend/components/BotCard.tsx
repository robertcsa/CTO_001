// Bot Card Component
'use client';

import { useState } from 'react';
import { Bot, BotState } from '@/types/api';
import { formatRelativeTime, getStateColor } from '@/utils/api';
import { PlayIcon, PauseIcon, StopIcon, TrashIcon, CogIcon } from '@heroicons/react/24/outline';
import { useBots } from '@/hooks/useBots';
import toast from 'react-hot-toast';

interface BotCardProps {
  bot: Bot;
  onEdit?: (bot: Bot) => void;
}

export default function BotCard({ bot, onEdit }: BotCardProps) {
  const { startBot, stopBot, pauseBot, resumeBot, deleteBot } = useBots();
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const handleStart = async () => {
    setActionLoading('start');
    const success = await startBot(bot.id);
    setActionLoading(null);
    if (!success) {
      toast.error('Failed to start bot');
    }
  };

  const handleStop = async () => {
    setActionLoading('stop');
    const success = await stopBot(bot.id);
    setActionLoading(null);
    if (!success) {
      toast.error('Failed to stop bot');
    }
  };

  const handlePause = async () => {
    setActionLoading('pause');
    const success = await pauseBot(bot.id);
    setActionLoading(null);
    if (!success) {
      toast.error('Failed to pause bot');
    }
  };

  const handleResume = async () => {
    setActionLoading('resume');
    const success = await resumeBot(bot.id);
    setActionLoading(null);
    if (!success) {
      toast.error('Failed to resume bot');
    }
  };

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this bot?')) return;
    
    setActionLoading('delete');
    const success = await deleteBot(bot.id);
    setActionLoading(null);
    if (!success) {
      toast.error('Failed to delete bot');
    }
  };

  const handleEdit = () => {
    if (onEdit) {
      onEdit(bot);
    }
  };

  const isLoading = (action: string) => actionLoading === action;

  return (
    <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{bot.name}</h3>
          <p className="text-sm text-gray-600">
            {bot.symbol} • {bot.timeframe} • {bot.strategy_id.replace('_', ' ').toUpperCase()}
          </p>
        </div>
        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStateColor(bot.state)}`}>
          {bot.state.toUpperCase()}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
        <div>
          <span className="text-gray-500">Asset Type:</span>
          <p className="font-medium">{bot.asset_type.toUpperCase()}</p>
        </div>
        <div>
          <span className="text-gray-500">Interval:</span>
          <p className="font-medium">{bot.interval_seconds}s</p>
        </div>
        {bot.last_run_at && (
          <div className="col-span-2">
            <span className="text-gray-500">Last Run:</span>
            <p className="font-medium">{formatRelativeTime(bot.last_run_at)}</p>
          </div>
        )}
      </div>

      {bot.params && Object.keys(bot.params).length > 0 && (
        <div className="mb-4">
          <span className="text-gray-500 text-sm">Parameters:</span>
          <div className="flex flex-wrap gap-2 mt-1">
            {Object.entries(bot.params).map(([key, value]) => (
              <span key={key} className="bg-gray-100 px-2 py-1 rounded text-xs">
                {key}: {String(value)}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="flex gap-2">
        {bot.state === BotState.STOPPED && (
          <button
            onClick={handleStart}
            disabled={isLoading('start')}
            className="flex items-center gap-1 px-3 py-1.5 bg-green-600 text-white text-sm rounded hover:bg-green-700 disabled:opacity-50"
          >
            <PlayIcon className="w-4 h-4" />
            {isLoading('start') ? 'Starting...' : 'Start'}
          </button>
        )}

        {bot.state === BotState.RUNNING && (
          <>
            <button
              onClick={handlePause}
              disabled={isLoading('pause')}
              className="flex items-center gap-1 px-3 py-1.5 bg-yellow-600 text-white text-sm rounded hover:bg-yellow-700 disabled:opacity-50"
            >
              <PauseIcon className="w-4 h-4" />
              {isLoading('pause') ? 'Pausing...' : 'Pause'}
            </button>
            <button
              onClick={handleStop}
              disabled={isLoading('stop')}
              className="flex items-center gap-1 px-3 py-1.5 bg-red-600 text-white text-sm rounded hover:bg-red-700 disabled:opacity-50"
            >
              <StopIcon className="w-4 h-4" />
              {isLoading('stop') ? 'Stopping...' : 'Stop'}
            </button>
          </>
        )}

        {bot.state === BotState.PAUSED && (
          <button
            onClick={handleResume}
            disabled={isLoading('resume')}
            className="flex items-center gap-1 px-3 py-1.5 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:opacity-50"
          >
            <PlayIcon className="w-4 h-4" />
            {isLoading('resume') ? 'Resuming...' : 'Resume'}
          </button>
        )}

        <button
          onClick={handleEdit}
          className="flex items-center gap-1 px-3 py-1.5 bg-gray-600 text-white text-sm rounded hover:bg-gray-700"
        >
          <CogIcon className="w-4 h-4" />
          Edit
        </button>

        <button
          onClick={handleDelete}
          disabled={isLoading('delete')}
          className="flex items-center gap-1 px-3 py-1.5 bg-red-600 text-white text-sm rounded hover:bg-red-700 disabled:opacity-50"
        >
          <TrashIcon className="w-4 h-4" />
          {isLoading('delete') ? 'Deleting...' : 'Delete'}
        </button>
      </div>
    </div>
  );
}