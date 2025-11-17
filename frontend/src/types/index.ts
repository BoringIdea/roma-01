/**
 * TypeScript type definitions for ROMA-01 Trading Platform
 */

export interface Agent {
  id: string;
  name: string;
  is_running: boolean;
  cycle_count: number;
  runtime_minutes: number;
  // Multi-DEX support fields
  dex_type?: "aster" | "hyperliquid";
  account_id?: string;
  model_id?: string;
  model_provider?: string;
  model_config_id?: string;
  llm_model?: string;
}

export interface AgentStatus {
  agent_id: string;
  name: string;
  is_running: boolean;
  cycle_count: number;
  runtime_minutes: number;
  // Multi-DEX support fields
  dex_type?: "aster" | "hyperliquid";
  account_id?: string;
  model_id?: string;
  model_provider?: string;
  model_config_id?: string;
  llm_model?: string;
}

export interface Account {
  total_wallet_balance: number;
  available_balance: number;
  total_unrealized_profit: number;
  adjusted_total_balance?: number;
  gross_total_balance?: number;
  net_deposits?: number;
  external_cash_flow?: number;
  initial_balance?: number;
}

export interface Position {
  symbol: string;
  side: "long" | "short";
  position_amt: number;
  entry_price: number;
  mark_price: number;
  unrealized_profit: number;
  leverage: number;
  liquidation_price: number;
}

export interface Performance {
  total_trades: number;
  wins: number;
  losses: number;
  win_rate: number;
  avg_profit: number;
  avg_loss: number;
  profit_factor: number;
  sharpe_ratio: number;
  max_drawdown: number;
  total_pnl: number;
  best_trade?: {
    symbol: string;
    pnl: number;
  };
  worst_trade?: {
    symbol: string;
    pnl: number;
  };
}

export interface Decision {
  timestamp: string;
  cycle_number: number;
  chain_of_thought: string;
  decisions: Array<{
    action: string;
    symbol?: string;
    leverage?: number;
    position_size_usd?: number;
    stop_loss?: number;
    take_profit?: number;
    reasoning: string;
  }>;
  account_state: Account;
  positions: Position[];
}

export interface EquityPoint {
  timestamp: string;
  cycle: number;
  equity: number;
  adjusted_equity?: number;
  gross_equity?: number;
  pnl: number;
  unrealized_pnl?: number;
  net_deposits?: number;
  external_cash_flow?: number;
}

export interface Trade {
  symbol: string;
  side: "long" | "short";
  entry_price: number;
  close_price: number;
  quantity: number;
  leverage: number;
  open_time: string;
  close_time: string;
  pnl_pct: number;
  pnl_usdt: number;
  commission?: number;
}

export type LogLevel = "DEBUG" | "INFO" | "WARNING" | "ERROR";
export type PromptLanguage = "en" | "zh";

export interface SystemConfig {
  scan_interval_minutes: number;
  max_concurrent_agents: number;
  log_level: LogLevel;
  prompt_language: PromptLanguage;
}

export interface AdminConfig {
  username: string;
  has_password: boolean;
  updated_at?: string | null;
}

export interface AuthConfig {
  admin: AdminConfig;
}

export interface ConfigVersion {
  updated_at?: string | null;
}

export interface ConfigResponse {
  system: SystemConfig;
  auth: AuthConfig;
  agents: ConfigAgent[];
  accounts: ConfigAccount[];
  models: ConfigModel[];
  accounts_resolved: ConfigResolvedAccount[];
  models_resolved: ConfigResolvedModel[];
  agents_resolved: ConfigAgent[];
  version: ConfigVersion;
}

export interface AdminUpdatePayload {
  username: string;
  password?: string | null;
}

export interface ConfigUpdatePayload {
  system?: SystemConfig;
  admin?: AdminUpdatePayload;
  agents?: ConfigAgent[];
  accounts?: ConfigAccount[];
  models?: ConfigModel[];
}

export interface ConfigAgentRiskManagement {
  max_positions: number;
  max_leverage: number;
  max_position_size_pct: number;
  max_total_position_pct: number;
  max_single_trade_pct: number;
  max_single_trade_with_positions_pct: number;
  max_daily_loss_pct: number;
  stop_loss_pct: number;
  take_profit_pct: number;
  [key: string]: number;
}

export interface ConfigAgentAdvancedOrders {
  enable_take_profit: boolean;
  take_profit_pct: number;
  enable_stop_loss: boolean;
  stop_loss_pct: number;
  [key: string]: boolean | number;
}

export interface ConfigAgentCustomPrompts {
  enabled: boolean;
  trading_philosophy: string;
  entry_preferences: string;
  position_management: string;
  market_preferences: string;
  additional_rules: string;
  [key: string]: boolean | string;
}

export interface ConfigAgentStrategy {
  initial_balance: number;
  scan_interval_minutes: number;
  max_account_usage_pct: number;
  prompt_language?: PromptLanguage;
  default_coins: string[];
  trading_style?: string;
  risk_management: ConfigAgentRiskManagement;
  advanced_orders: ConfigAgentAdvancedOrders;
  custom_prompts: ConfigAgentCustomPrompts;
  [key: string]: unknown;
}

export interface ConfigAgent {
  id: string;
  name: string;
  enabled: boolean;
  account_id: string;
  model_id: string;
  dex_type?: string;
  description?: string;
  strategy: ConfigAgentStrategy;
  [key: string]: unknown;
}

export interface ConfigAccount {
  id: string;
  name: string;
  dex_type: string;
  testnet?: boolean;
  hedge_mode?: boolean;
  [key: string]: unknown;
}

export interface ConfigModel {
  id: string;
  provider: string;
  model: string;
  temperature?: number | null;
  max_tokens?: number | null;
  [key: string]: unknown;
}

export interface ConfigResolvedAccount {
  [key: string]: unknown;
}

export interface ConfigResolvedModel {
  [key: string]: unknown;
}

