"use client";

import { useEffect, useMemo, useState } from "react";
import useSWR from "swr";
import Link from "next/link";
import { configApi, initializeConfigAuthTokenFromStorage, setConfigAuthToken } from "@/lib/api";
import type {
  ConfigAccount,
  ConfigAgent,
  ConfigModel,
  ConfigResolvedAccount,
  ConfigResolvedModel,
  ConfigResponse,
  ConfigUpdatePayload,
  PromptLanguage,
  SystemConfig,
} from "@/types";
import { useLanguage } from "@/store/useLanguage";
import PromptEditor from "@/components/PromptEditor";

import {
  AdminFormState,
  AccountFormState,
  ModelFormState,
  SettingsTab,
  AccountFilter,
  AgentFilter,
  ModelFilter,
  AccountDraft,
  AgentDraft,
  ModelDraft,
} from "@/app/settings/types";
import {
  LOG_LEVEL_OPTIONS,
  PROMPT_LANGUAGE_OPTIONS,
  MODEL_FILTER_ALL,
  ACCOUNT_FILTER_ALL,
  AGENT_FILTER_ALL,
  MODEL_TEMPLATES,
  ACCOUNT_TYPES,
  ACCOUNT_TYPE_REQUIRED_FIELDS,
} from "@/app/settings/constants";
import {
  deepClone,
  normalizeAccountsConfig,
  normalizeModelsConfig,
  normalizeAgentsConfig,
  sanitizeAccountsForSave,
  sanitizeModelsForSave,
  sanitizeAgentsForSave,
  validateAccounts,
  validateModels,
  validateAgents,
  generateModelId,
  generateAccountId,
  createNewAgentConfig,
  createNewModelConfig,
  normalizeModelLocation,
  sortByKey,
  createDefaultRiskManagement,
  createDefaultAdvancedOrders,
  createDefaultCustomPrompts,
  DEFAULT_AGENT_SYMBOLS,
} from "@/app/settings/helpers";
import { SettingsLoginModal } from "@/app/settings/components/SettingsLoginModal";
import { SettingsTabs } from "@/app/settings/components/SettingsTabs";
import { GeneralSection } from "@/app/settings/components/GeneralSection";
import { AdminSection } from "@/app/settings/components/AdminSection";
import { AccountsSection } from "@/app/settings/components/AccountsSection";
import { ModelsSection } from "@/app/settings/components/ModelsSection";
import { AgentsSection } from "@/app/settings/components/AgentsSection";
import { PromptsSection } from "@/app/settings/components/PromptsSection";
import { ModelTemplateModal } from "@/app/settings/components/ModelTemplateModal";
import { AccountModal } from "@/app/settings/components/AccountModal";
import { AgentModal } from "@/app/settings/components/AgentModal";



const applyResolved = <T = unknown>(raw: T, resolved: any): T => {
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

const buildAgentStrategyDefaults = (language: string, system?: SystemConfig | null): ConfigAgent["strategy"] => {
  const fallbackPrompt = (system?.prompt_language ?? (language === "zh" ? "zh" : "en")) as PromptLanguage;
  return {
    initial_balance: 10000,
    scan_interval_minutes: system?.scan_interval_minutes ?? 3,
    max_account_usage_pct: 100,
    prompt_language: fallbackPrompt,
    default_coins: [...DEFAULT_AGENT_SYMBOLS],
    trading_style: "balanced",
    risk_management: createDefaultRiskManagement(),
    advanced_orders: createDefaultAdvancedOrders(),
    custom_prompts: createDefaultCustomPrompts(),
  };
};








export default function SettingsPage() {
  const language = useLanguage((s) => s.language);

  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(() => !!initializeConfigAuthTokenFromStorage());
  const [loginError, setLoginError] = useState<string | null>(null);
  const [loginLoading, setLoginLoading] = useState(false);
  const [systemForm, setSystemForm] = useState<SystemConfig | null>(null);
  const [adminForm, setAdminForm] = useState<AdminFormState>({
    username: "",
    password: "",
    confirmPassword: "",
  });
  const [activeTab, setActiveTab] = useState<SettingsTab>("general");
  const [accountsForm, setAccountsForm] = useState<AccountFormState[]>([]);
  const [accountViewFilter, setAccountViewFilter] = useState<AccountFilter>(ACCOUNT_FILTER_ALL);
  const [showAccountModal, setShowAccountModal] = useState(false);
  const [accountModalError, setAccountModalError] = useState<string | null>(null);
  const [accountDraft, setAccountDraft] = useState<AccountDraft>({
    id: "",
    name: "",
    dex_type: ACCOUNT_TYPES[0],
    testnet: false,
    hedge_mode: false,
    user: "",
    signer: "",
    private_key: "",
    api_secret: "",
    account_id: "",
  });
  const [modelsForm, setModelsForm] = useState<ModelFormState[]>([]);
  const [modelViewFilter, setModelViewFilter] = useState<string>(MODEL_FILTER_ALL);
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null);
  const [agentsForm, setAgentsForm] = useState<ConfigAgent[]>([]);
  const [agentViewFilter, setAgentViewFilter] = useState<AgentFilter>(AGENT_FILTER_ALL);
  const [showAgentModal, setShowAgentModal] = useState(false);
  const [agentModalError, setAgentModalError] = useState<string | null>(null);
  const [agentDraft, setAgentDraft] = useState<AgentDraft>({
    id: "",
    name: "",
    account_id: "",
    model_id: "",
    enabled: false,
    strategy: buildAgentStrategyDefaults(language),
  });
  const [originalAgentsSnapshot, setOriginalAgentsSnapshot] = useState<string>("[]");
  const [originalAccountsSnapshot, setOriginalAccountsSnapshot] = useState<string>("[]");
  const [originalModelsSnapshot, setOriginalModelsSnapshot] = useState<string>("[]");
  const [showModelTemplateModal, setShowModelTemplateModal] = useState(false);
  const [modelTemplateError, setModelTemplateError] = useState<string | null>(null);
  const [modelDraft, setModelDraft] = useState<ModelDraft>({
    id: "",
    provider: MODEL_TEMPLATES[0].provider,
    model: MODEL_TEMPLATES[0].model,
    temperature: (MODEL_TEMPLATES[0].temperature ?? 0.15).toString(),
    max_tokens: (MODEL_TEMPLATES[0].max_tokens ?? 4000).toString(),
    api_key: "",
    location: normalizeModelLocation(MODEL_TEMPLATES[0].extra?.location),
  });
  const [draftIdWasEdited, setDraftIdWasEdited] = useState(false);
  const providerOptions = useMemo(
    () => Array.from(new Set(MODEL_TEMPLATES.map((template) => template.provider))),
    [],
  );
  const modelsByProvider = useMemo(
    () => MODEL_TEMPLATES.filter((template) => template.provider === modelDraft.provider),
    [modelDraft.provider],
  );
  const modelFilterOptions = useMemo(() => {
    const unique = modelsForm.map((model) => model.id).filter((id) => !!id);
    return [MODEL_FILTER_ALL, ...Array.from(new Set(unique))];
  }, [modelsForm]);
  const filteredModels = useMemo(() => {
    if (modelViewFilter === MODEL_FILTER_ALL) {
      return modelsForm;
    }
    return modelsForm.filter((model) => model.id === modelViewFilter);
  }, [modelViewFilter, modelsForm]);
  const accountFilterOptions = useMemo(() => {
    const unique = accountsForm.map((account) => account.id).filter((id) => !!id);
    return [ACCOUNT_FILTER_ALL, ...Array.from(new Set(unique))];
  }, [accountsForm]);
  const filteredAccounts = useMemo(() => {
    if (accountViewFilter === ACCOUNT_FILTER_ALL) {
      return accountsForm;
    }
    return accountsForm.filter((account) => account.id === accountViewFilter);
  }, [accountViewFilter, accountsForm]);
  const agentFilterOptions = useMemo(() => {
    const unique = agentsForm.map((agent) => agent.id).filter((id) => !!id);
    return [AGENT_FILTER_ALL, ...Array.from(new Set(unique))];
  }, [agentsForm]);
  const filteredAgents = useMemo(() => {
    if (agentViewFilter === AGENT_FILTER_ALL) {
      return agentsForm;
    }
    return agentsForm.filter((agent) => agent.id === agentViewFilter);
  }, [agentViewFilter, agentsForm]);

  const {
    data,
    error: configError,
    isLoading: configLoading,
    mutate,
  } = useSWR<ConfigResponse>(
    isAuthenticated ? "/settings/config" : null,
    () => configApi.getConfig(),
    {
      onError: (error) => {
        if (error instanceof Error && error.message === "CONFIG_AUTH_EXPIRED") {
          setConfigAuthToken(null);
          setIsAuthenticated(false);
          setLoginError(
            language === "zh" ? "会话已过期，请重新登录。" : "Session expired, please sign in again."
          );
        }
      },
    }
  );

  useEffect(() => {
    if (data) {
      setSystemForm({ ...data.system });
      setAdminForm({
        username: data.auth.admin.username,
        password: "",
        confirmPassword: "",
      });
      const normalizedAccounts = normalizeAccountsConfig(
        data.accounts ?? [],
        data.accounts_resolved ?? [],
      );
      setAccountsForm(normalizedAccounts);
      setOriginalAccountsSnapshot(JSON.stringify(normalizedAccounts));
      setAccountViewFilter(ACCOUNT_FILTER_ALL);
      const normalizedModels = normalizeModelsConfig(
        data.models ?? [],
        data.models_resolved ?? [],
      );
      setModelsForm(normalizedModels);
      setOriginalModelsSnapshot(JSON.stringify(normalizedModels));
      setModelViewFilter(MODEL_FILTER_ALL);
      const normalizedAgents = normalizeAgentsConfig(
        data.agents ?? [],
        data.system,
        data.agents_resolved ?? [],
      );
      setAgentsForm(normalizedAgents);
      setOriginalAgentsSnapshot(JSON.stringify(normalizedAgents));
      setAgentViewFilter(AGENT_FILTER_ALL);
      setSelectedAgentId(normalizedAgents[0]?.id ?? null);
      setSaveSuccess(null);
      setSaveError(null);
    }
  }, [data]);

  useEffect(() => {
    if (agentsForm.length === 0) {
      setSelectedAgentId(null);
      return;
    }
    if (!selectedAgentId || !agentsForm.some((agent) => agent.id === selectedAgentId)) {
      setSelectedAgentId(agentsForm[0].id);
    }
  }, [agentsForm, selectedAgentId]);

  useEffect(() => {
    if (agentsForm.length === 0) {
      return;
    }
    const accountIds = new Set(accountsForm.map((account) => account.id));
    const modelIds = new Set(modelsForm.map((model) => model.id));
    const fallbackAccount = accountsForm[0]?.id ?? "";
    const fallbackModel = modelsForm[0]?.id ?? "";
    if (!fallbackAccount || !fallbackModel) {
      return;
    }
    setAgentsForm((prev) => {
      let changed = false;
      const next = prev.map((agent) => {
        let updated = agent;
        if (!accountIds.has(agent.account_id)) {
          changed = true;
          updated = { ...updated, account_id: fallbackAccount };
        }
        if (!modelIds.has(agent.model_id)) {
          changed = true;
          updated = { ...updated, model_id: fallbackModel };
        }
        return updated;
      });
      return changed ? next : prev;
    });
  }, [accountsForm, modelsForm]);

  useEffect(() => {
    if (!modelFilterOptions.includes(modelViewFilter)) {
      setModelViewFilter(MODEL_FILTER_ALL);
    }
  }, [modelFilterOptions, modelViewFilter]);

  useEffect(() => {
    if (!accountFilterOptions.includes(accountViewFilter)) {
      setAccountViewFilter(ACCOUNT_FILTER_ALL);
    }
  }, [accountFilterOptions, accountViewFilter]);

  useEffect(() => {
    if (!agentFilterOptions.includes(agentViewFilter)) {
      setAgentViewFilter(AGENT_FILTER_ALL);
    }
  }, [agentFilterOptions, agentViewFilter]);

  const hasSystemChanges = useMemo(() => {
    if (!systemForm || !data) return false;
    return (
      systemForm.scan_interval_minutes !== data.system.scan_interval_minutes ||
      systemForm.max_concurrent_agents !== data.system.max_concurrent_agents ||
      systemForm.log_level !== data.system.log_level ||
      systemForm.prompt_language !== data.system.prompt_language
    );
  }, [systemForm, data]);

  const hasAdminChanges = useMemo(() => {
    if (!data) return false;
    return (
      adminForm.username.trim() !== data.auth.admin.username ||
      adminForm.password.trim().length > 0
    );
  }, [adminForm, data]);

  const passwordMismatch = adminForm.password !== adminForm.confirmPassword;
  const serializedAgents = useMemo(() => JSON.stringify(agentsForm), [agentsForm]);
  const serializedAccounts = useMemo(() => JSON.stringify(accountsForm), [accountsForm]);
  const serializedModels = useMemo(() => JSON.stringify(modelsForm), [modelsForm]);
  const hasAgentChanges = useMemo(
    () => serializedAgents !== originalAgentsSnapshot,
    [serializedAgents, originalAgentsSnapshot],
  );
  const hasAccountChanges = useMemo(
    () => serializedAccounts !== originalAccountsSnapshot,
    [serializedAccounts, originalAccountsSnapshot],
  );
  const hasModelChanges = useMemo(
    () => serializedModels !== originalModelsSnapshot,
    [serializedModels, originalModelsSnapshot],
  );
  const hasChanges = !!(
    hasSystemChanges ||
    hasAccountChanges ||
    hasModelChanges ||
    hasAgentChanges ||
    (hasAdminChanges && !passwordMismatch)
  );

  const handleLogin = async (username: string, password: string) => {
    setLoginLoading(true);
    setLoginError(null);
    try {
      await configApi.login(username, password);
      setIsAuthenticated(true);
      mutate(); // trigger config fetch
    } catch (error) {
      if (error instanceof Error) {
        setLoginError(error.message || "Failed to sign in");
      } else {
        setLoginError("Failed to sign in");
      }
    } finally {
      setLoginLoading(false);
    }
  };

  const handleDiscard = () => {
    if (!data) return;
    setSystemForm({ ...data.system });
    setAdminForm({
      username: data.auth.admin.username,
      password: "",
      confirmPassword: "",
    });
    const normalizedAccounts = normalizeAccountsConfig(
      data.accounts ?? [],
      data.accounts_resolved ?? [],
    );
    setAccountsForm(normalizedAccounts);
    setOriginalAccountsSnapshot(JSON.stringify(normalizedAccounts));
    setAccountViewFilter(ACCOUNT_FILTER_ALL);
    const normalizedModels = normalizeModelsConfig(
      data.models ?? [],
      data.models_resolved ?? [],
    );
    setModelsForm(normalizedModels);
    setOriginalModelsSnapshot(JSON.stringify(normalizedModels));
    setModelViewFilter(MODEL_FILTER_ALL);
    const normalizedAgents = normalizeAgentsConfig(
      data.agents ?? [],
      data.system,
      data.agents_resolved ?? [],
    );
    setAgentsForm(normalizedAgents);
    setOriginalAgentsSnapshot(JSON.stringify(normalizedAgents));
    setAgentViewFilter(AGENT_FILTER_ALL);
    setSelectedAgentId(normalizedAgents[0]?.id ?? null);
    setSaveError(null);
    setSaveSuccess(null);
  };

  const handleSave = async () => {
    if (!data || !systemForm) return;
    if (adminForm.password && passwordMismatch) {
      setSaveError(language === "zh" ? "两次输入的密码不一致" : "Passwords do not match");
      return;
    }

    const payload: ConfigUpdatePayload = {};
    if (hasSystemChanges) {
      payload.system = { ...systemForm };
    }
    if (hasAdminChanges) {
      payload.admin = {
        username: adminForm.username.trim(),
        password: adminForm.password.trim() || undefined,
      };
    }
    if (hasAccountChanges) {
      const accountsValidation = validateAccounts(accountsForm, language);
      if (accountsValidation) {
        setSaveError(accountsValidation);
        return;
      }
      payload.accounts = sanitizeAccountsForSave(accountsForm);
    }
    if (hasModelChanges) {
      const modelsValidation = validateModels(modelsForm, language);
      if (modelsValidation) {
        setSaveError(modelsValidation);
        return;
      }
      payload.models = sanitizeModelsForSave(modelsForm);
    }
    if (hasAgentChanges) {
      const agentsValidation = validateAgents(agentsForm, accountsForm, modelsForm, language);
      if (agentsValidation) {
        setSaveError(agentsValidation);
        return;
      }
      const fallbackLanguage = (systemForm.prompt_language ?? data.system.prompt_language ?? "en") as PromptLanguage;
      payload.agents = sanitizeAgentsForSave(agentsForm, fallbackLanguage);
    }

    if (!payload.system && !payload.admin && !payload.accounts && !payload.models && !payload.agents) {
      setSaveSuccess(language === "zh" ? "没有可以保存的更改" : "No changes to save");
      return;
    }

    setSaving(true);
    setSaveError(null);
    setSaveSuccess(null);

    try {
      const updated = await configApi.updateConfig(payload);
      mutate(updated, false);
      setSystemForm({ ...updated.system });
      setAdminForm({
        username: updated.auth.admin.username,
        password: "",
        confirmPassword: "",
      });
      const normalizedAccounts = normalizeAccountsConfig(
        updated.accounts ?? [],
        updated.accounts_resolved ?? [],
      );
      setAccountsForm(normalizedAccounts);
      setOriginalAccountsSnapshot(JSON.stringify(normalizedAccounts));
      setAccountViewFilter(ACCOUNT_FILTER_ALL);
      const normalizedModels = normalizeModelsConfig(
        updated.models ?? [],
        updated.models_resolved ?? [],
      );
      setModelsForm(normalizedModels);
      setOriginalModelsSnapshot(JSON.stringify(normalizedModels));
      setModelViewFilter(MODEL_FILTER_ALL);
      const normalizedAgents = normalizeAgentsConfig(
        updated.agents ?? [],
        updated.system,
        updated.agents_resolved ?? [],
      );
      setAgentsForm(normalizedAgents);
      setOriginalAgentsSnapshot(JSON.stringify(normalizedAgents));
      setAgentViewFilter(AGENT_FILTER_ALL);
      setSelectedAgentId(normalizedAgents[0]?.id ?? null);
      setSaveSuccess(language === "zh" ? "配置已保存" : "Configuration saved");
    } catch (error) {
      if (error instanceof Error) {
        setSaveError(error.message || "Failed to save configuration");
      } else {
        setSaveError("Failed to save configuration");
      }
    } finally {
      setSaving(false);
    }
  };

  const updateAgentAt = (index: number, updater: (agent: ConfigAgent) => ConfigAgent) => {
    setAgentsForm((prev) =>
      prev.map((agent, i) => {
        if (i !== index) {
          return agent;
        }
        const draft = deepClone(agent);
        return updater(draft);
      }),
    );
  };

  const handleSystemSectionChange = (updater: (prev: SystemConfig) => SystemConfig) => {
    setSystemForm((prev) => (prev ? updater({ ...prev }) : prev));
  };

  const handleAdminSectionChange = (updater: (prev: AdminFormState) => AdminFormState) => {
    setAdminForm((prev) => updater({ ...prev }));
  };

  const handleAccountIdChange = (previousId: string, nextId: string) => {
    if (accountViewFilter === previousId) {
      setAccountViewFilter(nextId);
    }
    setAgentsForm((prev) =>
      prev.map((agent) =>
        agent.account_id === previousId ? { ...agent, account_id: nextId } : agent,
      ),
    );
  };

  const handleModelIdChange = (previousId: string, nextId: string) => {
    if (modelViewFilter === previousId) {
      setModelViewFilter(nextId);
    }
    setAgentsForm((prev) =>
      prev.map((agent) =>
        agent.model_id === previousId ? { ...agent, model_id: nextId } : agent,
      ),
    );
    if (selectedAgentId === previousId) {
      setSelectedAgentId(nextId);
    }
  };

  const handleAgentIdChange = (previousId: string, nextId: string) => {
    if (selectedAgentId === previousId) {
      setSelectedAgentId(nextId);
    }
    if (agentViewFilter === previousId) {
      setAgentViewFilter(nextId);
    }
  };

  const handleAddAgent = () => {
    const baseSystem = systemForm ?? data?.system ?? null;
    if (!baseSystem) {
      setSaveError(language === "zh" ? "系统配置尚未加载完成" : "System config not ready yet");
      return;
    }
    if (accountsForm.length === 0 || modelsForm.length === 0) {
      setSaveError(language === "zh" ? "请先配置账户和模型" : "Configure accounts and models first");
      return;
    }
    setSaveError(null);
    const baseAgent = createNewAgentConfig({ existingAgents: agentsForm, system: baseSystem, language });
    const preferredAccount = accountViewFilter !== ACCOUNT_FILTER_ALL ? accountViewFilter : accountsForm[0]?.id ?? "";
    const preferredModel = modelViewFilter !== MODEL_FILTER_ALL ? modelViewFilter : modelsForm[0]?.id ?? "";
    setAgentDraft({
      id: baseAgent.id,
      name: baseAgent.name,
      account_id: preferredAccount,
      model_id: preferredModel,
      enabled: false,
      strategy: deepClone(baseAgent.strategy),
    });
    setAgentModalError(null);
    setShowAgentModal(true);
  };

  const handleAgentModalClose = () => {
    setShowAgentModal(false);
    setAgentModalError(null);
    setAgentDraft({
      id: "",
      name: "",
      account_id: "",
      model_id: "",
      enabled: false,
      strategy: buildAgentStrategyDefaults(language, systemForm ?? data?.system ?? null),
    });
  };

  const handleAgentDraftChange = (field: keyof AgentDraft, value: string | boolean) => {
    setAgentModalError(null);
    if (field === "enabled") {
      setAgentDraft((prev) => ({ ...prev, enabled: Boolean(value) }));
      return;
    }
    setAgentDraft((prev) => ({ ...prev, [field]: String(value) }));
  };

  const handleAgentStrategyChange = (updater: (draft: AgentDraft["strategy"]) => void) => {
    setAgentModalError(null);
    setAgentDraft((prev) => {
      const nextStrategy = deepClone(prev.strategy);
      updater(nextStrategy);
      return { ...prev, strategy: nextStrategy };
    });
  };

  const handleConfirmAddAgent = () => {
    const trimmedId = agentDraft.id.trim();
    if (!trimmedId) {
      setAgentModalError(language === "zh" ? "智能体 ID 不能为空。" : "Agent ID cannot be empty.");
      return;
    }
    if (agentsForm.some((agent) => agent.id === trimmedId)) {
      setAgentModalError(language === "zh" ? `智能体 ID 重复：${trimmedId}` : `Duplicate agent ID: ${trimmedId}`);
      return;
    }

    const trimmedName = agentDraft.name.trim();
    if (!trimmedName) {
      setAgentModalError(language === "zh" ? "显示名称不能为空。" : "Display name cannot be empty.");
      return;
    }

    if (!agentDraft.account_id) {
      setAgentModalError(language === "zh" ? "请选择一个绑定账户。" : "Please select an account.");
      return;
    }
    if (!agentDraft.model_id) {
      setAgentModalError(language === "zh" ? "请选择一个绑定模型。" : "Please select a model.");
      return;
    }

    if (!accountsForm.some((account) => account.id === agentDraft.account_id)) {
      setAgentModalError(language === "zh" ? "绑定账户不存在。" : "Selected account does not exist.");
      return;
    }
    if (!modelsForm.some((model) => model.id === agentDraft.model_id)) {
      setAgentModalError(language === "zh" ? "绑定模型不存在。" : "Selected model does not exist.");
      return;
    }

    const baseSystem = systemForm ?? data?.system ?? null;
    if (!baseSystem) {
      setAgentModalError(language === "zh" ? "系统配置尚未加载完成" : "System config not ready yet");
      return;
    }

    const baseAgent = createNewAgentConfig({ existingAgents: agentsForm, system: baseSystem, language });
    const newAgent: ConfigAgent = {
      ...baseAgent,
      id: trimmedId,
      name: trimmedName,
      enabled: agentDraft.enabled,
      account_id: agentDraft.account_id,
      model_id: agentDraft.model_id,
      strategy: deepClone(agentDraft.strategy),
    };

    setAgentsForm((prev) => [...prev, newAgent]);
    setAgentViewFilter(newAgent.id);
    setSelectedAgentId(newAgent.id);
    setAgentModalError(null);
    setShowAgentModal(false);
    setAgentDraft({
      id: "",
      name: "",
      account_id: "",
      model_id: "",
      enabled: false,
      strategy: buildAgentStrategyDefaults(language, systemForm ?? data?.system ?? null),
    });
  };

  const handleRemoveAgent = (index: number) => {
    if (agentsForm.length <= 1) {
      setSaveError(language === "zh" ? "至少需要保留一个智能体配置。" : "At least one agent must remain.");
      return;
    }
    const removedId = agentsForm[index]?.id;
    setAgentsForm((prev) => {
      const next = prev.filter((_, i) => i !== index);
      if (removedId && selectedAgentId === removedId) {
        setSelectedAgentId(next[0]?.id ?? null);
      }
      if (removedId) {
        setAgentViewFilter((current) => {
          if (current === removedId) {
            return next[0]?.id ?? AGENT_FILTER_ALL;
          }
          return current;
        });
      }
      return next;
    });
  };

  const updateAccountAt = (index: number, updater: (account: AccountFormState) => AccountFormState) => {
    setAccountsForm((prev) => {
      if (index < 0 || index >= prev.length) {
        return prev;
      }
      const previousId = prev[index]?.id;
      const next = prev.map((account, i) => {
        if (i !== index) return account;
        const draft = deepClone(account);
        return updater(draft);
      });
      const nextId = next[index]?.id;
      if (previousId && nextId && previousId !== nextId) {
        setAgentsForm((prevAgents) =>
          prevAgents.map((agent) =>
            agent.account_id === previousId ? { ...agent, account_id: nextId } : agent,
          ),
        );
      }
      return next;
    });
  };

  const handleAddAccount = () => {
    const suggestedId = generateAccountId(new Set(accountsForm.map((account) => account.id)));
    setAccountDraft({
      id: suggestedId,
      name: "",
      dex_type: ACCOUNT_TYPES[0],
      testnet: false,
      hedge_mode: false,
      user: "",
      signer: "",
      private_key: "",
      api_secret: "",
      account_id: "",
    });
    setAccountModalError(null);
    setShowAccountModal(true);
  };

  const handleAccountModalClose = () => {
    setShowAccountModal(false);
    setAccountModalError(null);
    setAccountDraft({ id: "", name: "", dex_type: ACCOUNT_TYPES[0], testnet: false, hedge_mode: false, user: "", signer: "", private_key: "", api_secret: "", account_id: "" });
  };

  const handleAccountDraftChange = (field: keyof AccountDraft, value: string | boolean) => {
    setAccountModalError(null);
    if (field === "testnet" || field === "hedge_mode") {
      setAccountDraft((prev) => ({ ...prev, [field]: Boolean(value) }));
      return;
    }
    if (field === "dex_type") {
      const nextType = value as AccountDraft["dex_type"];
      setAccountDraft((prev) => ({ ...prev, dex_type: nextType }));
      return;
    }
    setAccountDraft((prev) => ({ ...prev, [field]: String(value) }));
  };

  const handleRemoveAccount = (index: number) => {
    if (accountsForm.length <= 1) {
      setSaveError(language === "zh" ? "至少需要保留一个账户配置。" : "At least one account must remain.");
      return;
    }
    setAccountsForm((prev) => {
      if (index < 0 || index >= prev.length) {
        return prev;
      }
      const removedId = prev[index]?.id;
      const next = prev.filter((_, i) => i !== index);
      const fallbackAccount = next[0]?.id ?? prev[0]?.id ?? "";
      if (removedId) {
        setAgentsForm((prevAgents) =>
          prevAgents.map((agent) =>
            agent.account_id === removedId
              ? { ...agent, account_id: fallbackAccount || agent.account_id }
              : agent,
          ),
        );
        setAccountViewFilter((current) =>
          current === removedId ? fallbackAccount || ACCOUNT_FILTER_ALL : current,
        );
      }
      return next;
    });
  };

  const handleConfirmAddAccount = () => {
    const trimmedId = accountDraft.id.trim();
    const trimmedName = accountDraft.name.trim();
    if (!trimmedId) {
      setAccountModalError(language === "zh" ? "请填写账户 ID" : "Account ID is required");
      return;
    }
    if (accountsForm.some((account) => account.id === trimmedId)) {
      setAccountModalError(language === "zh" ? "账户 ID 已存在" : "Account ID already exists");
      return;
    }

    const fieldDefinitions =
      ACCOUNT_TYPE_REQUIRED_FIELDS[accountDraft.dex_type as (typeof ACCOUNT_TYPES)[number]] ?? [];
    const requiredExtraFields: AccountFormState["extraFields"] = [];
    for (const fieldDef of fieldDefinitions) {
      const raw = (accountDraft[fieldDef.key as keyof AccountDraft] as string | undefined)?.trim() ?? "";
      if (!raw) {
        const label = language === "zh" ? fieldDef.labelZh : fieldDef.labelEn;
        setAccountModalError(
          language === "zh" ? `${label} 为必填项` : `${label} is required`,
        );
        return;
      }
      requiredExtraFields.push({
        key: fieldDef.key,
        rawValue: raw,
        displayValue: raw,
        locked: true,
      });
    }

    const newAccount: AccountFormState = {
      id: trimmedId,
      name: trimmedName || trimmedId,
      dex_type: accountDraft.dex_type,
      testnet: accountDraft.testnet,
      hedge_mode: accountDraft.hedge_mode,
      extraFields: sortByKey(requiredExtraFields),
    };

    setSaveError(null);
    setSaveSuccess(null);
    setAccountsForm((prev) => [...prev, newAccount]);
    setAccountViewFilter(trimmedId);
    setAccountModalError(null);
    setShowAccountModal(false);
    setAccountDraft({ id: "", name: "", dex_type: ACCOUNT_TYPES[0], testnet: false, hedge_mode: false, user: "", signer: "", private_key: "", api_secret: "", account_id: "" });
  };

  const handleAddAccountField = (accountIndex: number) => {
    updateAccountAt(accountIndex, (draft) => {
      draft.extraFields = [
        ...draft.extraFields,
        { key: "", rawValue: "", displayValue: "", locked: false },
      ];
      return draft;
    });
  };

  const handleRemoveAccountField = (accountIndex: number, fieldIndex: number) => {
    updateAccountAt(accountIndex, (draft) => {
      draft.extraFields = draft.extraFields.filter((_, i) => i !== fieldIndex);
      return draft;
    });
  };

  const updateModelAt = (index: number, updater: (model: ModelFormState) => ModelFormState) => {
    setModelsForm((prev) => {
      if (index < 0 || index >= prev.length) {
        return prev;
      }
      const previousId = prev[index]?.id;
      const next = prev.map((model, i) => {
        if (i !== index) return model;
        const draft = deepClone(model);
        return updater(draft);
      });
      const nextId = next[index]?.id;
      if (previousId && nextId && previousId !== nextId) {
        setAgentsForm((prevAgents) =>
          prevAgents.map((agent) =>
            agent.model_id === previousId ? { ...agent, model_id: nextId } : agent,
          ),
        );
      }
      return next;
    });
  };

  const handleAddModel = () => {
    const defaultTemplate = MODEL_TEMPLATES[0];
    const existingIds = new Set(modelsForm.map((model) => model.id));
    const suggestedId = generateModelId(existingIds, defaultTemplate.provider);
    setModelDraft({
      id: suggestedId,
      provider: defaultTemplate.provider,
      model: defaultTemplate.model,
      temperature: (defaultTemplate.temperature ?? 0.15).toString(),
      max_tokens: (defaultTemplate.max_tokens ?? 4000).toString(),
      api_key: "",
      location: normalizeModelLocation(defaultTemplate.extra?.location),
    });
    setModelTemplateError(null);
    setDraftIdWasEdited(false);
    setShowModelTemplateModal(true);
  };

  const handleRemoveModel = (index: number) => {
    if (modelsForm.length <= 1) {
      setSaveError(language === "zh" ? "至少需要保留一个模型配置。" : "At least one model must remain.");
      return;
    }
    setModelsForm((prev) => {
      if (index < 0 || index >= prev.length) {
        return prev;
      }
      const removedId = prev[index]?.id;
      const next = prev.filter((_, i) => i !== index);
      const fallbackModel = next[0]?.id ?? prev[0]?.id ?? "";
      if (removedId) {
        setAgentsForm((prevAgents) =>
          prevAgents.map((agent) =>
            agent.model_id === removedId
              ? { ...agent, model_id: fallbackModel || agent.model_id }
              : agent,
          ),
        );
      }
      return next;
    });
  };

  const handleAddModelField = (modelIndex: number) => {
    updateModelAt(modelIndex, (draft) => {
      draft.extraFields = [
        ...draft.extraFields,
        { key: "", rawValue: "", displayValue: "", locked: false },
      ];
      return draft;
    });
  };

  const handleRemoveModelField = (modelIndex: number, fieldIndex: number) => {
    updateModelAt(modelIndex, (draft) => {
      draft.extraFields = draft.extraFields.filter((_, i) => i !== fieldIndex);
      return draft;
    });
  };

  const handleModelTemplateClose = () => {
    setShowModelTemplateModal(false);
    setDraftIdWasEdited(false);
  };

  const handleModelTemplateProviderChange = (provider: string) => {
    const available = MODEL_TEMPLATES.filter((template) => template.provider === provider);
    const fallbackTemplate = available[0] ?? MODEL_TEMPLATES[0];
    const existingIds = new Set(modelsForm.map((model) => model.id));
    setModelTemplateError(null);
    setModelDraft((prev) => {
      const prevTemperatureNumber = Number(prev.temperature);
      const templateTemperature = fallbackTemplate.temperature;
      const computedTemperature =
        templateTemperature !== undefined && templateTemperature !== null
          ? templateTemperature
          : Number.isNaN(prevTemperatureNumber)
            ? 0.15
            : prevTemperatureNumber;

      const prevMaxTokensNumber = Number(prev.max_tokens);
      const templateMaxTokens = fallbackTemplate.max_tokens;
      const computedMaxTokens =
        templateMaxTokens !== undefined && templateMaxTokens !== null
          ? templateMaxTokens
          : Number.isNaN(prevMaxTokensNumber)
            ? 4000
            : prevMaxTokensNumber;

      const shouldAutoId = !draftIdWasEdited;
      const nextId = shouldAutoId ? generateModelId(existingIds, provider) : prev.id;

      return {
        ...prev,
        provider,
        model: fallbackTemplate.model,
        temperature: computedTemperature.toString(),
        max_tokens: computedMaxTokens.toString(),
        location: normalizeModelLocation(fallbackTemplate.extra?.location),
        id: nextId,
      };
    });
  };

  const handleModelTemplateModelChange = (modelValue: string) => {
    const template = MODEL_TEMPLATES.find(
      (item) => item.provider === modelDraft.provider && item.model === modelValue,
    );
    setModelTemplateError(null);
    setModelDraft((prev) => {
      const prevTemperatureNumber = Number(prev.temperature);
      const templateTemperature = template?.temperature;
      const computedTemperature =
        templateTemperature !== undefined && templateTemperature !== null
          ? templateTemperature
          : Number.isNaN(prevTemperatureNumber)
            ? 0.15
            : prevTemperatureNumber;

      const prevMaxTokensNumber = Number(prev.max_tokens);
      const templateMaxTokens = template?.max_tokens;
      const computedMaxTokens =
        templateMaxTokens !== undefined && templateMaxTokens !== null
          ? templateMaxTokens
          : Number.isNaN(prevMaxTokensNumber)
            ? 4000
            : prevMaxTokensNumber;

      return {
        ...prev,
        model: modelValue,
        temperature: computedTemperature.toString(),
        max_tokens: computedMaxTokens.toString(),
        location: template ? normalizeModelLocation(template.extra?.location) : prev.location,
      };
    });
  };

  const handleModelDraftChange = (field: keyof ModelDraft, value: string) => {
    setModelTemplateError(null);
    if (field === "location") {
      setModelDraft((prev) => ({ ...prev, location: value as "china" | "international" }));
    } else {
      setModelDraft((prev) => ({ ...prev, [field]: value }));
    }
    if (field === "id") {
      setDraftIdWasEdited(true);
    }
  };

  const handleModelTemplateSubmit = () => {
    const trimmedId = modelDraft.id.trim();
    if (!trimmedId) {
      setModelTemplateError(language === "zh" ? "请填写模型 ID" : "Please provide a model ID");
      return;
    }
    if (modelsForm.some((model) => model.id === trimmedId)) {
      setModelTemplateError(
        language === "zh" ? "模型 ID 已存在，请换一个" : "Model ID already exists. Please choose another.",
      );
      return;
    }

    const trimmedApiKey = modelDraft.api_key.trim();
    if (!trimmedApiKey) {
      setModelTemplateError(language === "zh" ? "API Key 为必填项" : "API key is required");
      return;
    }

    const templateExists = MODEL_TEMPLATES.some(
      (entry) => entry.provider === modelDraft.provider && entry.model === modelDraft.model,
    );
    if (!templateExists) {
      setModelTemplateError(
        language === "zh" ? "所选提供方暂不支持该模型" : "Selected provider/model combination is not supported.",
      );
      return;
    }

    const newModel = createNewModelConfig(modelsForm, {
      id: trimmedId,
      provider: modelDraft.provider,
      model: modelDraft.model,
      temperature: modelDraft.temperature,
      max_tokens: modelDraft.max_tokens,
      api_key: trimmedApiKey,
      location: modelDraft.location,
    });
    setModelsForm((prev) => [...prev, newModel]);
    setModelViewFilter(newModel.id);
    setModelTemplateError(null);
    setShowModelTemplateModal(false);
    setDraftIdWasEdited(false);
  };

  const tabItems = useMemo(
    () => [
      { id: "general" as SettingsTab, label: language === "zh" ? "通用设置" : "General" },
      { id: "accounts" as SettingsTab, label: language === "zh" ? "账户配置" : "Accounts" },
      { id: "models" as SettingsTab, label: language === "zh" ? "模型配置" : "Models" },
      { id: "agents" as SettingsTab, label: language === "zh" ? "智能体配置" : "Agents" },
      { id: "prompts" as SettingsTab, label: language === "zh" ? "智能体提示词" : "Prompts" },
    ],
    [language],
  );

  const modelNameOptions = useMemo(() => {
    const names = modelsForm.map((model) => model.model).filter((name) => !!name);
    return Array.from(new Set(names));
  }, [modelsForm]);

  if (!isAuthenticated) {
    return (
      <SettingsLoginModal onSubmit={handleLogin} loading={loginLoading} error={loginError} />
    );
  }

  return (
    <div className="flex min-h-screen flex-col" style={{ background: "var(--app-bg)", color: "var(--foreground)" }}>
      <div className="mx-auto w-full max-w-6xl px-4 py-6 space-y-6">
        <header className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-lg font-black uppercase tracking-[0.3em]">
              {language === "zh" ? "配置中心" : "Configuration Center"}
            </h1>
            <p className="text-[11px]" style={{ color: "var(--muted-text)" }}>
              {language === "zh"
                ? "管理系统配置、账户、模型与智能体提示词。"
                : "Manage system settings, accounts, models, and agent prompts."}
            </p>
          </div>
          <Link
            href="/"
            className="inline-flex items-center justify-center rounded border px-3 py-1 text-[11px] uppercase tracking-widest transition hover:opacity-80"
            style={{
              borderColor: "var(--panel-border)",
              color: "var(--brand-accent)",
            }}
          >
            {language === "zh" ? "返回控制台" : "Back to Dashboard"}
          </Link>
        </header>

        {configError && (
          <div className="rounded border px-4 py-3 text-xs" style={{ borderColor: "#ef4444", color: "#ef4444" }}>
            {configError instanceof Error ? configError.message : String(configError)}
          </div>
        )}

        <SettingsTabs activeTab={activeTab} tabs={tabItems} onChange={setActiveTab} />

        <datalist id="model-provider-options">
          {providerOptions.map((provider) => (
            <option key={provider} value={provider} />
          ))}
        </datalist>
        <datalist id="model-name-options">
          {modelNameOptions.map((modelName) => (
            <option key={modelName} value={modelName} />
          ))}
        </datalist>

        <div className="space-y-6">
          {activeTab === "general" && (
            <>
              <GeneralSection
                language={language}
                configLoading={configLoading}
                systemForm={systemForm}
                onSystemChange={handleSystemSectionChange}
              />
              <AdminSection
                language={language}
                adminForm={adminForm}
                onAdminChange={handleAdminSectionChange}
              />
            </>
          )}

          {activeTab === "accounts" && (
            <AccountsSection
              language={language}
              configLoading={configLoading}
              accountFilterOptions={accountFilterOptions}
              accountViewFilter={accountViewFilter}
              onAccountFilterChange={setAccountViewFilter}
              onAccountIdChange={handleAccountIdChange}
              onAddAccount={handleAddAccount}
              accountsForm={accountsForm}
              filteredAccounts={filteredAccounts}
              onAddAccountField={handleAddAccountField}
              onRemoveAccountField={handleRemoveAccountField}
              onRemoveAccount={handleRemoveAccount}
              updateAccountAt={updateAccountAt}
            />
          )}

          {activeTab === "models" && (
            <ModelsSection
              language={language}
              configLoading={configLoading}
              modelFilterOptions={modelFilterOptions}
              modelViewFilter={modelViewFilter}
              onModelFilterChange={setModelViewFilter}
              onModelIdChange={handleModelIdChange}
              onAddModel={handleAddModel}
              modelsForm={modelsForm}
              filteredModels={filteredModels}
              onAddModelField={handleAddModelField}
              onRemoveModelField={handleRemoveModelField}
              onRemoveModel={handleRemoveModel}
              updateModelAt={updateModelAt}
            />
          )}

          {activeTab === "agents" && (
            <AgentsSection
              language={language}
              configLoading={configLoading}
              systemForm={systemForm}
              accountsForm={accountsForm}
              modelsForm={modelsForm}
              agentsForm={agentsForm}
              filteredAgents={filteredAgents}
              agentFilterOptions={agentFilterOptions}
              agentViewFilter={agentViewFilter}
              onAgentFilterChange={setAgentViewFilter}
              onAgentIdChange={handleAgentIdChange}
              onAddAgent={handleAddAgent}
              onRemoveAgent={handleRemoveAgent}
              updateAgentAt={updateAgentAt}
            />
          )}

          {activeTab === "prompts" && (
            <PromptsSection
              language={language}
              agentsForm={agentsForm}
              selectedAgentId={selectedAgentId}
              onSelectAgent={setSelectedAgentId}
              PromptEditorComponent={PromptEditor}
            />
          )}
        </div>

        <div className="sticky bottom-4 flex flex-wrap items-center justify-end gap-2 rounded border px-4 py-3"
          style={{ borderColor: "var(--panel-border)", background: "var(--panel-bg)" }}
        >
          <div className="flex-1 text-[11px]" style={{ color: "var(--muted-text)" }}>
            {saveError && <span className="text-red-500">{saveError}</span>}
            {saveSuccess && <span style={{ color: "var(--brand-accent)" }}>{saveSuccess}</span>}
            {!saveError && !saveSuccess && (
              <span>
                {hasChanges
                  ? language === "zh"
                    ? "有未保存的更改"
                    : "You have unsaved changes"
                  : language === "zh"
                    ? "所有更改已保存"
                    : "All changes saved"}
              </span>
            )}
          </div>
          <button
            onClick={handleDiscard}
            disabled={saving || !hasChanges}
            className="rounded border px-4 py-2 text-[11px] uppercase tracking-widest transition hover:opacity-80 disabled:opacity-40"
            style={{ borderColor: "var(--panel-border)" }}
          >
            {language === "zh" ? "撤销" : "Discard"}
          </button>
          <button
            onClick={handleSave}
            disabled={saving || !hasChanges}
            className="rounded px-4 py-2 text-[11px] font-semibold uppercase tracking-widest transition hover:opacity-80 disabled:opacity-40"
            style={{
              background: "var(--brand-accent)",
              color: "#ffffff",
            }}
          >
            {saving
              ? language === "zh"
                ? "保存中..."
                : "Saving..."
              : language === "zh"
                ? "保存"
                : "Save"}
          </button>
        </div>
      </div>

      <ModelTemplateModal
        language={language}
        visible={showModelTemplateModal}
        modelDraft={modelDraft}
        modelTemplateError={modelTemplateError}
        providerOptions={providerOptions}
        modelsByProvider={modelsByProvider}
        draftIdWasEdited={draftIdWasEdited}
        onClose={handleModelTemplateClose}
        onProviderChange={handleModelTemplateProviderChange}
        onModelChange={handleModelTemplateModelChange}
        onDraftChange={handleModelDraftChange}
        onSubmit={handleModelTemplateSubmit}
      />

      <AccountModal
        language={language}
        visible={showAccountModal}
        accountDraft={accountDraft}
        error={accountModalError}
        onDraftChange={handleAccountDraftChange}
        onClose={handleAccountModalClose}
        onSubmit={handleConfirmAddAccount}
      />

      <AgentModal
        language={language}
        visible={showAgentModal}
        agentDraft={agentDraft}
        error={agentModalError}
        accountsForm={accountsForm}
        modelsForm={modelsForm}
        onDraftChange={handleAgentDraftChange}
        onStrategyChange={handleAgentStrategyChange}
        onClose={handleAgentModalClose}
        onSubmit={handleConfirmAddAgent}
      />

    </div>
  );
}
