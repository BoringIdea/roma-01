import type { ConfigModel, SystemConfig } from "@/types";
import type { AccountTypeSpecificKey } from "@/app/settings/types";

export const LOG_LEVEL_OPTIONS: Array<SystemConfig["log_level"]> = ["DEBUG", "INFO", "WARNING", "ERROR"];

export const PROMPT_LANGUAGE_OPTIONS: Array<SystemConfig["prompt_language"]> = ["en", "zh"];

export const MODEL_FILTER_ALL = "__all__";
export const ACCOUNT_FILTER_ALL = "__all__";
export const AGENT_FILTER_ALL = "__all__";

export const ACCOUNT_TYPES = ["aster", "hyperliquid"] as const;

export const ACCOUNT_TYPE_REQUIRED_FIELDS: Record<
  (typeof ACCOUNT_TYPES)[number],
  Array<{
    key: AccountTypeSpecificKey;
    labelZh: string;
    labelEn: string;
    placeholderZh?: string;
    placeholderEn?: string;
  }>
> = {
  aster: [
    {
      key: "user",
      labelZh: "主账号地址",
      labelEn: "User (Root Address)",
      placeholderZh: "例如：0xabc...",
      placeholderEn: "e.g. 0xabc...",
    },
    {
      key: "signer",
      labelZh: "API 账户地址",
      labelEn: "Signer (API Signer Address)",
      placeholderZh: "例如：0xabc...",
      placeholderEn: "e.g. 0xabc...",
    },
    {
      key: "private_key",
      labelZh: "API 账户私钥",
      labelEn: "API Private Key",
      placeholderZh: "可使用环境变量 \${ASTER_PRIVATE_KEY}",
      placeholderEn: "Use env placeholder \${ASTER_PRIVATE_KEY}",
    },
  ],
  hyperliquid: [
    {
      key: "api_secret",
      labelZh: "API 账户密钥",
      labelEn: "API Account Secret Key",
      placeholderZh: "可使用环境变量 \${HL_SECRET_KEY}",
      placeholderEn: "Use env placeholder \${HL_SECRET_KEY}",
    },
    {
      key: "account_id",
      labelZh: "账户地址",
      labelEn: "Account Address",
      placeholderZh: "例如：0xabc...",
      placeholderEn: "e.g. 0xabc...",
    },
  ],
};

export const MODEL_LOCATION_OPTIONS = [
  // Use english label for location options
  { value: "international", labelZh: "International", labelEn: "International" },
  { value: "china", labelZh: "China", labelEn: "China" },
];

export const MODEL_TEMPLATES: Array<{
  templateId: string;
  labelZh: string;
  labelEn: string;
  provider: string;
  model: string;
  temperature?: number;
  max_tokens?: number;
  extra?: {
    location?: "china" | "international";
    [key: string]: unknown;
  };
}> = [
  {
    templateId: "deepseek-v3.1",
    labelZh: "DeepSeek Chat V3.1",
    labelEn: "DeepSeek Chat V3.1",
    provider: "deepseek",
    model: "deepseek-chat",
    temperature: 0.15,
    max_tokens: 4000,
  },
  {
    templateId: "qwen3-max",
    labelZh: "Qwen3 Max",
    labelEn: "Qwen3 Max",
    provider: "qwen",
    model: "qwen-max",
    temperature: 0.15,
    max_tokens: 4000,
    extra: {
      location: "china",
    },
  },
  {
    templateId: "claude-sonnet-4.5",
    labelZh: "Claude Sonnet 4.5",
    labelEn: "Claude Sonnet 4.5",
    provider: "anthropic",
    model: "claude-sonnet-4.5",
    temperature: 0.15,
    max_tokens: 4000,
  },
  {
    templateId: "gpt-5",
    labelZh: "GPT-5",
    labelEn: "GPT-5",
    provider: "openai",
    model: "gpt-5",
    temperature: 0.15,
    max_tokens: 4000,
  },
  {
    templateId: "grok-4",
    labelZh: "Grok 4",
    labelEn: "Grok 4",
    provider: "xai",
    model: "grok-4",
    temperature: 0.2,
    max_tokens: 4000,
  },
  {
    templateId: "gemini-2.5-pro",
    labelZh: "Gemini 2.5 Pro",
    labelEn: "Gemini 2.5 Pro",
    provider: "google",
    model: "gemini-2.5-pro",
    temperature: 0.15,
    max_tokens: 4000,
  },
];

export const ACCOUNT_RESERVED_KEYS = new Set(["id", "name", "dex_type", "testnet", "hedge_mode"]);

export const MODEL_RESERVED_KEYS = new Set<keyof ConfigModel>([
  "id",
  "provider",
  "model",
  "temperature",
  "max_tokens",
  "api_key",
  "location",
]);

