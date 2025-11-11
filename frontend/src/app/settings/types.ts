import type { ConfigAgent, PromptLanguage, SystemConfig } from "@/types";

export type SettingsTab = "general" | "accounts" | "models" | "agents" | "prompts";

export interface AdminFormState {
  username: string;
  password: string;
  confirmPassword: string;
}

export type AgentRiskManagementState = ConfigAgent["strategy"]["risk_management"];
export type AgentAdvancedOrdersState = ConfigAgent["strategy"]["advanced_orders"];
export type AgentCustomPromptsState = ConfigAgent["strategy"]["custom_prompts"];
export type AgentStrategyState = ConfigAgent["strategy"];

export interface AccountExtraField {
  key: string;
  rawValue: string;
  displayValue: string;
  locked: boolean;
}

export interface ModelExtraField {
  key: string;
  rawValue: string;
  displayValue: string;
  locked: boolean;
}

export interface AccountFormState {
  id: string;
  name: string;
  dex_type: string;
  testnet: boolean;
  hedge_mode: boolean;
  extraFields: AccountExtraField[];
}

export interface ModelFormState {
  id: string;
  provider: string;
  model: string;
  temperature?: number | null;
  max_tokens?: number | null;
  api_key?: string;
  api_key_display?: string;
  location?: string;
  location_display?: string;
  extraFields: ModelExtraField[];
}

export type AccountFilter = string;
export type AgentFilter = string;
export type ModelFilter = string;

export type AccountTypeSpecificKey = "user" | "signer" | "private_key" | "api_secret" | "account_id";

export interface AccountDraft {
  id: string;
  name: string;
  dex_type: string;
  testnet: boolean;
  hedge_mode: boolean;
  user: string;
  signer: string;
  private_key: string;
  api_secret: string;
  account_id: string;
}

export interface AgentDraft {
  id: string;
  name: string;
  account_id: string;
  model_id: string;
  enabled: boolean;
  strategy: AgentStrategyState;
}

export interface ModelDraft {
  id: string;
  provider: string;
  model: string;
  temperature: string;
  max_tokens: string;
  api_key: string;
  location: string;
}

export interface NewAgentContext {
  existingAgents: ConfigAgent[];
  system: SystemConfig | null;
  language: string;
}

export interface NewAccountContext {
  existingAccounts: AccountFormState[];
  language: string;
}

export interface NewModelOverrides {
  id: string;
  provider: string;
  model: string;
  temperature: string;
  max_tokens: string;
  api_key: string;
  location: string;
}

export type PromptLanguageOption = PromptLanguage;

