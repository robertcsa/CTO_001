// Trading Bot API Types

export interface User {
  id: string;
  email: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  updated_at: string;
}

export interface Bot {
  id: string;
  user_id: string;
  name: string;
  asset_type: AssetType;
  symbol: string;
  timeframe: string;
  strategy_id: StrategyId;
  state: BotState;
  scheduler_job_id?: string;
  interval_seconds: number;
  params?: Record<string, any>;
  last_run_at?: string;
  created_at: string;
  updated_at: string;
}

export interface BotCreate {
  name: string;
  asset_type: AssetType;
  symbol: string;
  timeframe: string;
  strategy_id: StrategyId;
  interval_seconds: number;
  params?: Record<string, any>;
}

export interface BotUpdate {
  name?: string;
  asset_type?: AssetType;
  symbol?: string;
  timeframe?: string;
  strategy_id?: StrategyId;
  interval_seconds?: number;
  params?: Record<string, any>;
}

export interface BotStatus {
  id: string;
  name: string;
  state: BotState;
  last_run_at?: string;
  is_running: boolean;
  can_start: boolean;
  can_stop: boolean;
}

export interface MarketCandle {
  id: string;
  symbol: string;
  timeframe: string;
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface Indicator {
  id: string;
  bot_id: string;
  timestamp: string;
  indicator_type: string;
  value: Record<string, any>;
  created_at: string;
}

export interface Signal {
  id: string;
  bot_id: string;
  timestamp: string;
  signal_type: SignalType;
  confidence: number;
  reason?: string;
  inputs_hash: string;
  meta?: Record<string, any>;
  created_at: string;
}

export interface Order {
  id: string;
  bot_id: string;
  signal_id?: string;
  side: OrderSide;
  quantity: number;
  price: number;
  status: OrderStatus;
  position_state: PositionState;
  entry_price?: number;
  exit_price?: number;
  pnl: number;
  created_at: string;
  updated_at: string;
  meta?: Record<string, any>;
}

export interface PortfolioSummary {
  balance: number;
  total_pnl: number;
  open_positions_value: number;
  total_value: number;
  pnl_percentage: number;
  available_balance: number;
  margin_used: number;
}

export interface ApiResponse<T> {
  data: T;
  message?: string;
  status: string;
}

export interface ApiError {
  error: {
    type: string;
    message: string;
    status_code: number;
  };
}

// Enums
export enum AssetType {
  CRYPTO = 'crypto',
  FOREX = 'forex',
  STOCKS = 'stocks'
}

export enum StrategyId {
  BLUE_SKY = 'blue_sky'
}

export enum BotState {
  STOPPED = 'stopped',
  RUNNING = 'running',
  ERROR = 'error',
  PAUSED = 'paused'
}

export enum SignalType {
  BUY = 'BUY',
  SELL = 'SELL',
  HOLD = 'HOLD'
}

export enum OrderSide {
  BUY = 'BUY',
  SELL = 'SELL'
}

export enum OrderStatus {
  OPEN = 'open',
  CLOSED = 'closed',
  CANCELLED = 'cancelled'
}

export enum PositionState {
  NONE = 'none',
  LONG = 'long',
  SHORT = 'short'
}