// Bots Page Component
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useBots } from '@/hooks/useBots';
import { Bot, BotCreate } from '@/types/api';
import BotCard from '@/components/BotCard';
import CreateBotModal from '@/components/CreateBotModal';
import { PlusIcon } from '@heroicons/react/24/outline';

export default function BotsPage() {
  const { bots, loading } = useBots();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingBot, setEditingBot] = useState<Bot | null>(null);
  const router = useRouter();

  const handleCreateBot = () => {
    setEditingBot(null);
    setShowCreateModal(true);
  };

  const handleEditBot = (bot: Bot) => {
    setEditingBot(bot);
    setShowCreateModal(true);
  };

  const handleBotClick = (bot: Bot) => {
    router.push(`/bots/${bot.id}`);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Trading Bots</h1>
          <p className="mt-2 text-gray-600">
            Manage and monitor your automated trading strategies
          </p>
        </div>
        <button
          onClick={handleCreateBot}
          className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <PlusIcon className="w-5 h-5" />
          Create Bot
        </button>
      </div>

      {bots.length === 0 ? (
        <div className="text-center py-12">
          <div className="mx-auto w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mb-4">
            <PlusIcon className="w-12 h-12 text-gray-400" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No bots yet</h3>
          <p className="text-gray-600 mb-6">
            Get started by creating your first trading bot
          </p>
          <button
            onClick={handleCreateBot}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <PlusIcon className="w-5 h-5" />
            Create Your First Bot
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {bots.map((bot) => (
            <div
              key={bot.id}
              className="cursor-pointer"
              onClick={() => handleBotClick(bot)}
            >
              <BotCard 
                bot={bot} 
                onEdit={handleEditBot}
              />
            </div>
          ))}
        </div>
      )}

      {showCreateModal && (
        <CreateBotModal
          bot={editingBot}
          onClose={() => setShowCreateModal(false)}
        />
      )}
    </div>
  );
}