import type {
  ConfigAccount,
  ConfigAgent,
  ConfigModel,
  ConfigResolvedAccount,
  ConfigResolvedModel,
  PromptLanguage,
  SystemConfig,
} from "@/types";

import {
  ACCOUNT_RESERVED_KEYS,
  MODEL_RESERVED_KEYS,
  ACCOUNT_TYPES,
} from "./constants";
import type {
  AccountFormState,
  AgentAdvancedOrdersState,
  AgentCustomPromptsState,
  AgentDraft,
  AgentRiskManagementState,
  ModelDraft,
  ModelFormState,
  NewAccountContext,
  NewAgentContext,
  NewModelOverrides,
} from "./types";

export const deepClone = <T,>(value: T): T => JSON.parse(JSON.stringify(value));

export const stringifyLooseValue = (value: unknown): string => {
  if (value === null || value === undefined) {
    return "";
  }
  if (typeof value === "object") {
    try {
      return JSON.stringify(value);
    } catch (error) {
      console.warn("Failed to stringify value", error);
      return String(value);
    }
  }
  return String(value);
};

export const parseLooseValue = (value: string): unknown => {
  const trimmed = value.trim();
  if (trimmed === "") {
    return "";
  }

  const lower = trimmed.toLowerCase();
  if (lower === "true") return true;
  if (lower === "false") return false;

  if (/^-?\d+(\.\d+)?$/.test(trimmed)) {
    return trimmed.includes(".") ? parseFloat(trimmed) : parseInt(trimmed, 10);
  }

  if (
    (trimmed.startsWith("{") && trimmed.endsWith("}")) ||
    (trimmed.startsWith("[") && trimmed.endsWith("]"))
  ) {
    try {
      return JSON.parse(trimmed);
    } catch {
      // fall back to string
    }
  }

  return trimmed;
};

export const sortByKey = <T extends { key: string }>(pairs: T[]): T[] =>
  [...pairs].sort((a, b) => {
    const keyA = a.key || "";
    const keyB = b.key || "";
    if (!keyA && keyB) return 1;
    if (!keyB && keyA) return -1;
    return keyA.localeCompare(keyB);
  });

export const applyResolved = <T = unknown>(raw: T, resolved: any): T => {
  if (resolved === undefined || resolved === null) {
    return raw;
  }
  if (Array.isArray(raw) && Array.isArray(resolved)) {
    return resolved.map((value, index) => applyResolved(raw[index], value)) as unknown as T;
  }
  if (typeof raw === "object" && raw !== null && typeof resolved === "object" && resolved !== null) {
    const result: Record<string, unknown> = { ...(raw as Record<string, unknown>) };
    Object.keys(resolved).forEach((key) => {
      result[key] = applyResolved(result[key], (resolved as Record<string, unknown>)[key]);
    });
    return result as T;
  }
  return resolved as T;
};

export const createDefaultRiskManagement = (): AgentRiskManagementState => ({
  max_positions: 3,
  max_leverage: 10,
  max_position_size_pct: 30,
  max_total_position_pct: 80,
  max_single_trade_pct: 50,
  max_single_trade_with_positions_pct: 30,
  max_daily_loss_pct: 15,
  stop_loss_pct: 3,
  take_profit_pct: 10,
});

export const createDefaultAdvancedOrders = (): AgentAdvancedOrdersState => ({
  enable_take_profit: true,
  take_profit_pct: 5,
  enable_stop_loss: true,
  stop_loss_pct: 2,
});

export const createDefaultCustomPrompts = (): AgentCustomPromptsState => ({
  enabled: false,
  trading_philosophy: "",
  entry_preferences: "",
  position_management: "",
  market_preferences: "",
  additional_rules: "",
});

export const DEFAULT_AGENT_SYMBOLS = [
  "BTCUSDT",
  "ETHUSDT",
  "SOLUSDT",
  "BNBUSDT",
  "DOGEUSDT",
  "XRPUSDT",
];

export const normalizeModelLocation = (raw?: string | null): "china" | "international" => {
  return raw && raw.trim().toLowerCase() === "china" ? "china" : "international";
};

export const normalizeAccountsConfig = (
  accounts: ConfigAccount[] | undefined | null,
  accountsResolved: ConfigResolvedAccount[] | undefined | null,
): AccountFormState[] => {
  return (accounts ?? []).map((raw, index) => {
    const account = deepClone(raw) as ConfigAccount;
    const resolvedRecord = (accountsResolved ?? [])[index] ?? {};
    const id = (account.id ?? "").trim() || `account-${(index + 1).toString().padStart(2, "0")}`;
    const name = (account.name ?? "").trim() || id;
    const dexType = (account.dex_type ?? ACCOUNT_TYPES[0]).trim() || ACCOUNT_TYPES[0];

    const testnet = Boolean(account.testnet);
    const hedgeMode = Boolean(account.hedge_mode);

    const extraFields: AccountFormState["extraFields"] = [];
    Object.entries(account).forEach(([key, value]) => {
      if (ACCOUNT_RESERVED_KEYS.has(key)) {
        return;
      }
      const rawValue = stringifyLooseValue(value);
      const resolvedSource =
        typeof resolvedRecord === "object" && resolvedRecord !== null
          ? (resolvedRecord as Record<string, unknown>)[key]
          : undefined;
      const displayValue =
        resolvedSource !== undefined ? stringifyLooseValue(resolvedSource) : rawValue;
      extraFields.push({
        key,
        rawValue,
        displayValue,
        locked: true,
      });
    });

    return {
      id,
      name,
      dex_type: dexType,
      testnet,
      hedge_mode: hedgeMode,
      extraFields: sortByKey(extraFields),
    };
  });
};

export const normalizeModelsConfig = (
  models: ConfigModel[] | undefined | null,
  modelsResolved: ConfigResolvedModel[] | undefined | null,
): ModelFormState[] => {
  return (models ?? []).map((raw, index) => {
    const model = deepClone(raw) as ConfigModel;
    const resolvedRecord = (modelsResolved ?? [])[index] ?? {};
    const resolvedMerged = applyResolved(model, resolvedRecord) as ConfigModel;
    const id = (model.id ?? "").trim() || `model-${(index + 1).toString().padStart(2, "0")}`;
    const provider = (resolvedMerged.provider ?? model.provider ?? "").trim();
    const modelName = (resolvedMerged.model ?? model.model ?? "").trim();

    const temperature =
      typeof resolvedMerged.temperature === "number" && !Number.isNaN(resolvedMerged.temperature)
        ? resolvedMerged.temperature
        : model.temperature === null
          ? null
          : model.temperature !== undefined
            ? Number(model.temperature)
            : undefined;
    const maxTokens =
      typeof resolvedMerged.max_tokens === "number" && !Number.isNaN(resolvedMerged.max_tokens)
        ? resolvedMerged.max_tokens
        : model.max_tokens === null
          ? null
          : model.max_tokens !== undefined
            ? Number(model.max_tokens)
            : undefined;

    const extraFields: ModelFormState["extraFields"] = [];
    Object.entries(model).forEach(([key, value]) => {
      if (MODEL_RESERVED_KEYS.has(key as keyof ConfigModel)) {
        return;
      }
      const resolvedSource =
        typeof resolvedRecord === "object" && resolvedRecord !== null
          ? (resolvedRecord as Record<string, unknown>)[key]
          : undefined;
      const fallbackValue = stringifyLooseValue(value);
      extraFields.push({
        key,
        rawValue: fallbackValue,
        displayValue:
          resolvedSource !== undefined ? stringifyLooseValue(resolvedSource) : fallbackValue,
        locked: true,
      });
    });

    const rawApiKey = typeof model.api_key === "string" ? model.api_key : "";
    const resolvedApiKey =
      typeof resolvedMerged.api_key === "string" ? resolvedMerged.api_key : rawApiKey;
    const rawLocation = typeof model.location === "string" ? model.location : "";
    const resolvedLocation =
      typeof resolvedMerged.location === "string" ? resolvedMerged.location : rawLocation;

    return {
      id,
      provider,
      model: modelName,
      temperature: Number.isFinite(temperature as number) ? (temperature as number) : undefined,
      max_tokens: Number.isFinite(maxTokens as number) ? (maxTokens as number) : undefined,
      api_key: rawApiKey,
      api_key_display: resolvedApiKey,
      location: rawLocation,
      location_display: resolvedLocation,
      extraFields: sortByKey(extraFields),
    };
  });
};

export const normalizeAgentsConfig = (
  agents: ConfigAgent[] | undefined | null,
  system: SystemConfig,
  _agentsResolved?: ConfigAgent[] | undefined | null,
): ConfigAgent[] => {
  const fallbackLanguage = (system?.prompt_language ?? "en") as PromptLanguage;

  return (agents ?? []).map((raw) => {
    const agent = deepClone(raw) as ConfigAgent;
    agent.id = (agent.id ?? "").trim() || `agent-${Math.random().toString(36).slice(2, 8)}`;
    agent.name = (agent.name ?? "").trim() || agent.id;
    agent.enabled = Boolean(agent.enabled);
    agent.account_id = (agent.account_id ?? "").trim();
    agent.model_id = (agent.model_id ?? "").trim();

    const strategy = agent.strategy ? deepClone(agent.strategy) : ({} as ConfigAgent["strategy"]);

    strategy.initial_balance = Number(strategy.initial_balance ?? 10000);
    strategy.scan_interval_minutes = Number(strategy.scan_interval_minutes ?? system.scan_interval_minutes ?? 3);
    strategy.max_account_usage_pct = Number(strategy.max_account_usage_pct ?? 100);
    const normalizedLang = (strategy.prompt_language ?? fallbackLanguage).toLowerCase();
    strategy.prompt_language = (normalizedLang.startsWith("zh") ? "zh" : "en") as PromptLanguage;

    const rawDefaultCoins = (strategy as Record<string, unknown>).default_coins;
    const coinsSource = Array.isArray(rawDefaultCoins)
      ? rawDefaultCoins
      : typeof rawDefaultCoins === "string"
        ? rawDefaultCoins.split(",")
        : [];
    strategy.default_coins = (coinsSource as Array<string | number>)
      .map((coin) => String(coin).trim().toUpperCase())
      .filter(Boolean);

    strategy.trading_style = (strategy.trading_style ?? "balanced") as string;

    const risk: AgentRiskManagementState = {
      ...createDefaultRiskManagement(),
      ...(strategy.risk_management ?? {}),
    };
    Object.keys(risk).forEach((key) => {
      risk[key as keyof AgentRiskManagementState] = Number(risk[key as keyof AgentRiskManagementState]);
    });
    strategy.risk_management = risk;

    const advanced: AgentAdvancedOrdersState = {
      ...createDefaultAdvancedOrders(),
      ...(strategy.advanced_orders ?? {}),
    };
    advanced.enable_take_profit = Boolean(advanced.enable_take_profit);
    advanced.enable_stop_loss = Boolean(advanced.enable_stop_loss);
    advanced.take_profit_pct = Number(advanced.take_profit_pct);
    advanced.stop_loss_pct = Number(advanced.stop_loss_pct);
    strategy.advanced_orders = advanced;

    const prompts: AgentCustomPromptsState = {
      ...createDefaultCustomPrompts(),
      ...(strategy.custom_prompts ?? {}),
    };
    prompts.enabled = Boolean(prompts.enabled);
    strategy.custom_prompts = prompts;

    agent.strategy = strategy;
    return agent;
  });
};

export const sanitizeAccountsForSave = (accounts: AccountFormState[]): ConfigAccount[] => {
  return accounts.map((form) => {
    const payload: ConfigAccount = {
      id: form.id.trim(),
      name: form.name.trim() || form.id.trim(),
      dex_type: form.dex_type.trim() || ACCOUNT_TYPES[0],
      testnet: Boolean(form.testnet),
      hedge_mode: Boolean(form.hedge_mode),
    };

    form.extraFields.forEach(({ key, rawValue }) => {
      const trimmedKey = key.trim();
      if (!trimmedKey || ACCOUNT_RESERVED_KEYS.has(trimmedKey)) {
        return;
      }
      payload[trimmedKey] = parseLooseValue(rawValue);
    });

    return payload;
  });
};

export const sanitizeModelsForSave = (models: ModelFormState[]): ConfigModel[] => {
  return models.map((form) => {
    const payload: ConfigModel = {
      id: form.id.trim(),
      provider: form.provider.trim(),
      model: form.model.trim(),
    };

    if (form.temperature !== undefined && form.temperature !== null && !Number.isNaN(form.temperature)) {
      payload.temperature = Number(form.temperature);
    } else if (form.temperature === null) {
      payload.temperature = null;
    }

    if (form.max_tokens !== undefined && form.max_tokens !== null && !Number.isNaN(form.max_tokens)) {
      payload.max_tokens = Number(form.max_tokens);
    } else if (form.max_tokens === null) {
      payload.max_tokens = null;
    }

    if (form.api_key?.trim()) {
      payload.api_key = form.api_key.trim();
    }
    if (form.location?.trim()) {
      payload.location = form.location.trim();
    }

    form.extraFields.forEach(({ key, rawValue }) => {
      const trimmedKey = key.trim();
      if (!trimmedKey || MODEL_RESERVED_KEYS.has(trimmedKey as keyof ConfigModel)) {
        return;
      }
      payload[trimmedKey] = parseLooseValue(rawValue);
    });

    return payload;
  });
};

export const sanitizeAgentsForSave = (
  agents: ConfigAgent[],
  fallbackLanguage: PromptLanguage,
): ConfigAgent[] => {
  return agents.map((raw) => {
    const agent = deepClone(raw) as ConfigAgent;
    agent.id = agent.id.trim();
    agent.name = agent.name.trim() || agent.id;
    agent.account_id = agent.account_id.trim();
    agent.model_id = agent.model_id.trim();

    const strategy = agent.strategy;
    strategy.initial_balance = Number(strategy.initial_balance);
    strategy.scan_interval_minutes = Number(strategy.scan_interval_minutes);
    strategy.max_account_usage_pct = Number(strategy.max_account_usage_pct);
    const normalizedLang = (strategy.prompt_language ?? fallbackLanguage).toLowerCase();
    strategy.prompt_language = (normalizedLang.startsWith("zh") ? "zh" : "en") as PromptLanguage;
    strategy.default_coins = strategy.default_coins.map((coin) => coin.trim().toUpperCase()).filter(Boolean);
    strategy.trading_style = (strategy.trading_style ?? "balanced").trim() || "balanced";

    const sanitizedRisk: AgentRiskManagementState = {} as AgentRiskManagementState;
    Object.entries(strategy.risk_management ?? {}).forEach(([key, value]) => {
      sanitizedRisk[key as keyof AgentRiskManagementState] = Number(value);
    });
    strategy.risk_management = {
      ...createDefaultRiskManagement(),
      ...sanitizedRisk,
    };

    const sanitizedAdvanced: AgentAdvancedOrdersState = {
      ...createDefaultAdvancedOrders(),
    };
    if (strategy.advanced_orders) {
      Object.entries(strategy.advanced_orders).forEach(([key, value]) => {
        if (key === "enable_take_profit" || key === "enable_stop_loss") {
          sanitizedAdvanced[key as keyof AgentAdvancedOrdersState] = Boolean(value);
        } else {
          sanitizedAdvanced[key as keyof AgentAdvancedOrdersState] = Number(value) as boolean | number;
        }
      });
    }
    strategy.advanced_orders = sanitizedAdvanced;

    const sanitizedPrompts: AgentCustomPromptsState = {
      ...createDefaultCustomPrompts(),
      ...(strategy.custom_prompts ?? {}),
    };
    sanitizedPrompts.enabled = Boolean(sanitizedPrompts.enabled);
    strategy.custom_prompts = sanitizedPrompts;

    agent.strategy = strategy;
    return agent;
  });
};

export const validateAccounts = (accounts: AccountFormState[], language: string): string | null => {
  if (accounts.length === 0) {
    return language === "zh" ? "至少需要保留一个账户配置。" : "At least one account is required.";
  }

  const ids = new Set<string>();
  for (const account of accounts) {
    const trimmedId = account.id.trim();
    if (!trimmedId) {
      return language === "zh" ? "账户 ID 不能为空。" : "Account ID cannot be empty.";
    }
    if (ids.has(trimmedId)) {
      return language === "zh" ? `账户 ID 重复：${trimmedId}` : `Duplicate account ID: ${trimmedId}`;
    }
    ids.add(trimmedId);

    if (!account.name.trim()) {
      return language === "zh" ? `账户 ${trimmedId} 缺少名称。` : `Account ${trimmedId} must have a name.`;
    }
    if (!account.dex_type.trim()) {
      return language === "zh" ? `账户 ${trimmedId} 缺少 DEX 类型。` : `Account ${trimmedId} must specify dex_type.`;
    }

    const extraKeys = new Set<string>();
    for (const { key } of account.extraFields) {
      const trimmedKey = key.trim();
      if (!trimmedKey) {
        return language === "zh" ? `账户 ${trimmedId} 存在空的字段名。` : `Account ${trimmedId} has an empty field name.`;
      }
      if (ACCOUNT_RESERVED_KEYS.has(trimmedKey)) {
        return language === "zh"
          ? `账户 ${trimmedId} 的字段 ${trimmedKey} 与预留字段冲突。`
          : `Account ${trimmedId} field ${trimmedKey} conflicts with reserved keys.`;
      }
      if (extraKeys.has(trimmedKey)) {
        return language === "zh"
          ? `账户 ${trimmedId} 的字段 ${trimmedKey} 重复。`
          : `Account ${trimmedId} has duplicate field ${trimmedKey}.`;
      }
      extraKeys.add(trimmedKey);
    }
  }

  return null;
};

export const validateModels = (models: ModelFormState[], language: string): string | null => {
  if (models.length === 0) {
    return language === "zh" ? "至少需要保留一个模型配置。" : "At least one model is required.";
  }

  const ids = new Set<string>();
  for (const model of models) {
    const trimmedId = model.id.trim();
    if (!trimmedId) {
      return language === "zh" ? "模型 ID 不能为空。" : "Model ID cannot be empty.";
    }
    if (ids.has(trimmedId)) {
      return language === "zh" ? `模型 ID 重复：${trimmedId}` : `Duplicate model ID: ${trimmedId}`;
    }
    ids.add(trimmedId);

    if (!model.provider.trim()) {
      return language === "zh" ? `模型 ${trimmedId} 缺少提供方。` : `Model ${trimmedId} must have a provider.`;
    }
    if (!model.model.trim()) {
      return language === "zh" ? `模型 ${trimmedId} 缺少模型名称。` : `Model ${trimmedId} must specify a model name.`;
    }

    const extraKeys = new Set<string>();
    for (const { key } of model.extraFields) {
      const trimmedKey = key.trim();
      if (!trimmedKey) {
        return language === "zh" ? `模型 ${trimmedId} 存在空的字段名。` : `Model ${trimmedId} has an empty field name.`;
      }
      if (MODEL_RESERVED_KEYS.has(trimmedKey as keyof ConfigModel)) {
        return language === "zh"
          ? `模型 ${trimmedId} 的字段 ${trimmedKey} 与预留字段冲突。`
          : `Model ${trimmedId} field ${trimmedKey} conflicts with reserved keys.`;
      }
      if (extraKeys.has(trimmedKey)) {
        return language === "zh"
          ? `模型 ${trimmedId} 的字段 ${trimmedKey} 重复。`
          : `Model ${trimmedId} has duplicate field ${trimmedKey}.`;
      }
      extraKeys.add(trimmedKey);
    }
  }

  return null;
};

export const validateAgents = (
  agents: ConfigAgent[],
  accounts: AccountFormState[],
  models: ModelFormState[],
  language: string,
): string | null => {
  if (agents.length === 0) {
    return language === "zh" ? "至少需要保留一个智能体配置。" : "At least one agent configuration is required.";
  }

  const ids = new Set<string>();
  const accountIds = new Set(accounts.map((account) => account.id.trim()));
  const modelIds = new Set(models.map((model) => model.id.trim()));

  for (const agent of agents) {
    const trimmedId = agent.id.trim();
    if (!trimmedId) {
      return language === "zh" ? "智能体 ID 不能为空。" : "Agent ID cannot be empty.";
    }
    if (ids.has(trimmedId)) {
      return language === "zh"
        ? `智能体 ID 重复：${trimmedId}`
        : `Duplicate agent ID detected: ${trimmedId}`;
    }
    ids.add(trimmedId);

    if (!agent.name.trim()) {
      return language === "zh" ? `智能体 ${trimmedId} 缺少名称。` : `Agent ${trimmedId} must have a name.`;
    }
    if (!agent.account_id.trim()) {
      return language === "zh"
        ? `智能体 ${trimmedId} 缺少账户绑定。`
        : `Agent ${trimmedId} must specify an account ID.`;
    }
    if (!agent.model_id.trim()) {
      return language === "zh"
        ? `智能体 ${trimmedId} 缺少模型绑定。`
        : `Agent ${trimmedId} must specify a model ID.`;
    }
    if (!accountIds.has(agent.account_id.trim())) {
      return language === "zh"
        ? `智能体 ${trimmedId} 绑定的账户不存在，请先在账户设置中添加或修改。`
        : `Agent ${trimmedId} references a missing account. Please add or update the account first.`;
    }
    if (!modelIds.has(agent.model_id.trim())) {
      return language === "zh"
        ? `智能体 ${trimmedId} 绑定的模型不存在，请先在模型设置中添加或修改。`
        : `Agent ${trimmedId} references a missing model. Please add or update the model first.`;
    }
  }

  return null;
};

const sanitizeModelPrefix = (provider: string): string => {
  const normalized = provider.trim().toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
  return normalized || "model";
};

export const generateModelId = (existingIds: Set<string>, prefix = "model"): string => {
  const base = sanitizeModelPrefix(prefix);
  let index = existingIds.size + 1;
  let candidate = `${base}-${index.toString().padStart(2, "0")}`;
  while (existingIds.has(candidate)) {
    index += 1;
    candidate = `${base}-${index.toString().padStart(2, "0")}`;
  }
  return candidate;
};

export const generateAgentId = (existingIds: Set<string>): string => {
  let index = existingIds.size + 1;
  let candidate = `agent-${index.toString().padStart(2, "0")}`;
  while (existingIds.has(candidate)) {
    index += 1;
    candidate = `agent-${index.toString().padStart(2, "0")}`;
  }
  return candidate;
};

export const generateAccountId = (existingIds: Set<string>): string => {
  let index = existingIds.size + 1;
  let candidate = `account-${index.toString().padStart(2, "0")}`;
  while (existingIds.has(candidate)) {
    index += 1;
    candidate = `account-${index.toString().padStart(2, "0")}`;
  }
  return candidate;
};

export const createNewAgentConfig = ({ existingAgents, system, language }: NewAgentContext): ConfigAgent => {
  const existingIds = new Set(existingAgents.map((agent) => agent.id));
  const id = generateAgentId(existingIds);
  const displayIndex = existingAgents.length + 1;

  const defaultPromptLanguage = (system?.prompt_language ?? "en") as PromptLanguage;
  const defaultScanInterval = system?.scan_interval_minutes ?? 3;

  const name = language === "zh" ? `新智能体 ${displayIndex}` : `New Agent ${displayIndex}`;

  return {
    id,
    name,
    enabled: false,
    account_id: "",
    model_id: "",
    strategy: {
      initial_balance: 10000,
      scan_interval_minutes: defaultScanInterval,
      max_account_usage_pct: 100,
      prompt_language: defaultPromptLanguage,
      default_coins: [...DEFAULT_AGENT_SYMBOLS],
      trading_style: "balanced",
      risk_management: createDefaultRiskManagement(),
      advanced_orders: createDefaultAdvancedOrders(),
      custom_prompts: createDefaultCustomPrompts(),
    },
  };
};

export const createNewAccountConfig = ({ existingAccounts, language }: NewAccountContext): AccountFormState => {
  const existingIds = new Set(existingAccounts.map((account) => account.id));
  const id = generateAccountId(existingIds);
  const displayIndex = existingAccounts.length + 1;
  const name = language === "zh" ? `账户 ${displayIndex}` : `Account ${displayIndex}`;

  return {
    id,
    name,
    dex_type: ACCOUNT_TYPES[0],
    testnet: false,
    hedge_mode: false,
    extraFields: [],
  };
};

export const createNewModelConfig = (
  existingModels: ModelFormState[],
  overrides: NewModelOverrides,
): ModelFormState => {
  const existingIds = new Set(existingModels.map((model) => model.id));
  const requestedId = overrides.id.trim();
  const id = requestedId || generateModelId(existingIds, overrides.provider);

  const parseNumericInput = (input: string, fallback: number): number => {
    if (!input.trim()) return fallback;
    const parsed = Number(input);
    return Number.isNaN(parsed) ? fallback : parsed;
  };

  const temperature = parseNumericInput(overrides.temperature, 0.15);
  const maxTokens = parseNumericInput(overrides.max_tokens, 4000);

  const apiKeyValue = overrides.api_key.trim();
  const locationNormalized = overrides.location.trim().toLowerCase();
  const locationValue = locationNormalized === "china" ? "china" : "international";

  return {
    id,
    provider: overrides.provider,
    model: overrides.model,
    temperature,
    max_tokens: maxTokens,
    api_key: apiKeyValue,
    api_key_display: apiKeyValue,
    location: locationValue,
    location_display: locationValue,
    extraFields: [],
  };
};

export const hasAdminChanges = (username: string, password: string, confirmPassword: string): boolean => {
  if (!username.trim()) {
    return false;
  }
  if (password.trim() !== "" || confirmPassword.trim() !== "") {
    return true;
  }
  return false;
};

export const sanitizeAgentDraft = (
  draft: AgentDraft,
  accounts: AccountFormState[],
  models: ModelFormState[],
  language: string,
): { error: string | null; payload?: AgentDraft } => {
  const trimmedId = draft.id.trim();
  const trimmedName = draft.name.trim();

  if (!trimmedId) {
    return {
      error: language === "zh" ? "智能体 ID 不能为空。" : "Agent ID cannot be empty.",
    };
  }
  if (!trimmedName) {
    return {
      error: language === "zh" ? "显示名称不能为空。" : "Display name cannot be empty.",
    };
  }
  if (!draft.account_id) {
    return {
      error: language === "zh" ? "请选择一个绑定账户。" : "Please select an account.",
    };
  }
  if (!draft.model_id) {
    return {
      error: language === "zh" ? "请选择一个绑定模型。" : "Please select a model.",
    };
  }

  const accountSet = new Set(accounts.map((account) => account.id));
  const modelSet = new Set(models.map((model) => model.id));

  if (!accountSet.has(draft.account_id)) {
    return {
      error: language === "zh" ? "绑定账户不存在。" : "Selected account does not exist.",
    };
  }
  if (!modelSet.has(draft.model_id)) {
    return {
      error: language === "zh" ? "绑定模型不存在。" : "Selected model does not exist.",
    };
  }

  return {
    error: null,
    payload: {
      id: trimmedId,
      name: trimmedName,
      account_id: draft.account_id,
      model_id: draft.model_id,
      enabled: draft.enabled,
      strategy: deepClone(draft.strategy),
    },
  };
};

export const sanitizeModelDraft = (
  draft: ModelDraft,
  modelsForm: ModelFormState[],
  language: string,
): { error: string | null; payload?: ModelDraft } => {
  const trimmedId = draft.id.trim();
  if (!trimmedId) {
    return {
      error: language === "zh" ? "请填写模型 ID" : "Please provide a model ID",
    };
  }
  if (modelsForm.some((model) => model.id === trimmedId)) {
    return {
      error: language === "zh" ? "模型 ID 已存在，请换一个" : "Model ID already exists. Please choose another.",
    };
  }
  const trimmedApiKey = draft.api_key.trim();
  if (!trimmedApiKey) {
    return {
      error: language === "zh" ? "API Key 为必填项" : "API key is required",
    };
  }
  return {
    error: null,
    payload: {
      ...draft,
      id: trimmedId,
      api_key: trimmedApiKey,
    },
  };
};

