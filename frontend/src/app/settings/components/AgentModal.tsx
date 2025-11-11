"use client";

import { useEffect, useState } from "react";

import { PROMPT_LANGUAGE_OPTIONS } from "@/app/settings/constants";
import type { AgentDraft, AgentStrategyState, AccountFormState, ModelFormState } from "@/app/settings/types";

const TRADING_STYLE_OPTIONS = [
  { value: "balanced", labelZh: "均衡", labelEn: "Balanced" },
  { value: "aggressive", labelZh: "激进", labelEn: "Aggressive" },
  { value: "conservative", labelZh: "稳健", labelEn: "Conservative" },
];

const RISK_FIELDS: Array<{
  key: keyof AgentStrategyState["risk_management"];
  labelZh: string;
  labelEn: string;
}> = [
  { key: "max_positions", labelZh: "最大持仓数", labelEn: "Max Positions" },
  { key: "max_leverage", labelZh: "最大杠杆", labelEn: "Max Leverage" },
  { key: "max_position_size_pct", labelZh: "单仓占比(%)", labelEn: "Max Position Size (%)" },
  { key: "max_total_position_pct", labelZh: "总仓位占比(%)", labelEn: "Max Total Exposure (%)" },
  { key: "max_single_trade_pct", labelZh: "单笔仓位上限(%)", labelEn: "Max Single Trade (%)" },
  {
    key: "max_single_trade_with_positions_pct",
    labelZh: "持仓情况下单笔上限(%)",
    labelEn: "Max Trade With Existing (%)",
  },
  { key: "max_daily_loss_pct", labelZh: "最大日亏损(%)", labelEn: "Max Daily Drawdown (%)" },
  { key: "stop_loss_pct", labelZh: "止损(%)", labelEn: "Stop Loss (%)" },
  { key: "take_profit_pct", labelZh: "止盈(%)", labelEn: "Take Profit (%)" },
];

const parseCoinsInput = (value: string): string[] =>
  value
    .split(/[,\s]+/)
    .map((coin) => coin.trim().toUpperCase())
    .filter(Boolean);

interface AgentModalProps {
  language: string;
  visible: boolean;
  agentDraft: AgentDraft;
  error: string | null;
  accountsForm: AccountFormState[];
  modelsForm: ModelFormState[];
  onDraftChange: (field: keyof AgentDraft, value: string | boolean) => void;
  onStrategyChange: (updater: (draft: AgentStrategyState) => void) => void;
  onClose: () => void;
  onSubmit: () => void;
}

export function AgentModal({
  language,
  visible,
  agentDraft,
  error,
  accountsForm,
  modelsForm,
  onDraftChange,
  onStrategyChange,
  onClose,
  onSubmit,
}: AgentModalProps) {
  const [showStrategyAdvanced, setShowStrategyAdvanced] = useState(false);
  const strategy = agentDraft.strategy;

  useEffect(() => {
    if (visible) {
      setShowStrategyAdvanced(false);
    }
  }, [visible]);

  if (!visible) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center px-4 backdrop-blur">
      <div
        className="w-full max-w-2xl rounded-xl border bg-[color:var(--panel-bg)] p-6 shadow-lg"
        style={{ borderColor: "var(--panel-border)" }}
      >
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-sm font-semibold uppercase tracking-widest" style={{ color: "var(--foreground)" }}>
              {language === "zh" ? "新增智能体" : "Create Agent"}
            </h2>
            <p className="mt-1 text-[11px]" style={{ color: "var(--muted-text)" }}>
              {language === "zh"
                ? "选择要绑定的账户与模型，填写智能体 ID 与名称，创建后可继续在列表中调整详细策略。"
                : "Choose the account and model pairing, then set the agent ID and name. You can fine-tune strategy details after creation."}
            </p>
          </div>
          <button
            onClick={onClose}
            className="rounded border px-3 py-1 text-[10px] uppercase tracking-widest"
            style={{ borderColor: "var(--panel-border)", color: "var(--muted-text)" }}
          >
            {language === "zh" ? "取消" : "Cancel"}
          </button>
        </div>

        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <div className="space-y-1">
            <label className="text-[11px] font-semibold uppercase tracking-wider">
              {language === "zh" ? "智能体 ID" : "Agent ID"}
            </label>
            <input
              type="text"
              value={agentDraft.id}
              onChange={(e) => onDraftChange("id", e.target.value)}
              className="w-full rounded border bg-transparent px-3 py-2 text-xs outline-none focus:ring-1"
              style={{ borderColor: "var(--panel-border)" }}
              placeholder="agent-01"
            />
          </div>

          <div className="space-y-1">
            <label className="text-[11px] font-semibold uppercase tracking-wider">
              {language === "zh" ? "显示名称" : "Display Name"}
            </label>
            <input
              type="text"
              value={agentDraft.name}
              onChange={(e) => onDraftChange("name", e.target.value)}
              className="w-full rounded border bg-transparent px-3 py-2 text-xs outline-none focus:ring-1"
              style={{ borderColor: "var(--panel-border)" }}
              placeholder={language === "zh" ? "例如 主策略智能体" : "e.g. Primary Strategy"}
            />
          </div>

          <div className="space-y-1">
            <label className="text-[11px] font-semibold uppercase tracking-wider">
              {language === "zh" ? "绑定账户" : "Linked Account"}
            </label>
            <select
              value={agentDraft.account_id}
              onChange={(e) => onDraftChange("account_id", e.target.value)}
              className="w-full rounded border bg-transparent px-3 py-2 text-xs outline-none focus:ring-1"
              style={{ borderColor: "var(--panel-border)" }}
            >
              {accountsForm.map((account) => (
                <option key={account.id} value={account.id}>
                  {account.name || account.id}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-1">
            <label className="text-[11px] font-semibold uppercase tracking-wider">
              {language === "zh" ? "绑定模型" : "Linked Model"}
            </label>
            <select
              value={agentDraft.model_id}
              onChange={(e) => onDraftChange("model_id", e.target.value)}
              className="w-full rounded border bg-transparent px-3 py-2 text-xs outline-none focus:ring-1"
              style={{ borderColor: "var(--panel-border)" }}
            >
              {modelsForm.map((model) => (
                <option key={model.id} value={model.id}>
                  {model.model || model.id}
                </option>
              ))}
            </select>
          </div>
        </div>

        <label
          className="mt-4 flex items-center gap-2 text-[10px] uppercase tracking-widest"
          style={{ color: "var(--muted-text)" }}
        >
          <input
            type="checkbox"
            className="h-4 w-4"
            checked={agentDraft.enabled}
            onChange={(e) => onDraftChange("enabled", e.target.checked)}
          />
          {language === "zh" ? "创建后立即启用" : "Enable immediately"}
        </label>

        <div className="mt-6 flex flex-col gap-3 rounded border p-4" style={{ borderColor: "var(--panel-border)" }}>
          <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
            <div>
              <h3 className="text-sm font-semibold uppercase tracking-wider" style={{ color: "var(--foreground)" }}>
                {language === "zh" ? "策略配置" : "Strategy Configuration"}
              </h3>
              <p className="text-[11px]" style={{ color: "var(--muted-text)" }}>
                {language === "zh"
                  ? "默认策略已根据系统推荐值填充，可保留默认值或展开高级选项调整。"
                  : "Defaults use system-recommended values. Expand advanced options to customise."}
              </p>
            </div>
            <button
              onClick={() => setShowStrategyAdvanced((prev) => !prev)}
              className="self-start rounded border px-3 py-1 text-[10px] uppercase tracking-widest transition hover:opacity-80"
              style={{ borderColor: "var(--panel-border)", color: "var(--muted-text)" }}
            >
              {showStrategyAdvanced
                ? language === "zh" ? "收起高级选项" : "Hide Advanced"
                : language === "zh" ? "展开高级选项" : "Show Advanced"}
            </button>
          </div>

          {showStrategyAdvanced && (
            <div className="space-y-4 max-h-[420px] overflow-y-auto pr-2" style={{ scrollbarWidth: "thin" }}>
              <div className="grid gap-4 md:grid-cols-3">
                <div className="space-y-1">
                  <label className="text-[11px] font-semibold uppercase tracking-wider">
                    {language === "zh" ? "初始资金" : "Initial Balance"}
                  </label>
                  <input
                    type="number"
                    value={strategy.initial_balance}
                    onChange={(e) =>
                      onStrategyChange((draft) => {
                        draft.initial_balance = Number(e.target.value);
                      })
                    }
                    className="w-full rounded border bg-transparent px-3 py-2 text-xs outline-none focus:ring-1"
                    style={{ borderColor: "var(--panel-border)" }}
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-[11px] font-semibold uppercase tracking-wider">
                    {language === "zh" ? "扫描频率（分钟）" : "Scan Interval (minutes)"}
                  </label>
                  <input
                    type="number"
                    value={strategy.scan_interval_minutes}
                    onChange={(e) =>
                      onStrategyChange((draft) => {
                        draft.scan_interval_minutes = Number(e.target.value);
                      })
                    }
                    className="w-full rounded border bg-transparent px-3 py-2 text-xs outline-none focus:ring-1"
                    style={{ borderColor: "var(--panel-border)" }}
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-[11px] font-semibold uppercase tracking-wider">
                    {language === "zh" ? "账户使用上限(%)" : "Max Account Usage (%)"}
                  </label>
                  <input
                    type="number"
                    value={strategy.max_account_usage_pct}
                    onChange={(e) =>
                      onStrategyChange((draft) => {
                        draft.max_account_usage_pct = Number(e.target.value);
                      })
                    }
                    className="w-full rounded border bg-transparent px-3 py-2 text-xs outline-none focus:ring-1"
                    style={{ borderColor: "var(--panel-border)" }}
                  />
                </div>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-1">
                  <label className="text-[11px] font-semibold uppercase tracking-wider">
                    {language === "zh" ? "提示词语言" : "Prompt Language"}
                  </label>
                  <select
                    value={strategy.prompt_language}
                    onChange={(e) =>
                      onStrategyChange((draft) => {
                        draft.prompt_language = e.target.value as AgentStrategyState["prompt_language"];
                      })
                    }
                    className="w-full rounded border bg-transparent px-3 py-2 text-xs outline-none focus:ring-1 capitalize"
                    style={{ borderColor: "var(--panel-border)" }}
                  >
                    {PROMPT_LANGUAGE_OPTIONS.map((option) => (
                      <option key={option} value={option}>
                        {option.toUpperCase()}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="text-[11px] font-semibold uppercase tracking-wider">
                    {language === "zh" ? "交易风格" : "Trading Style"}
                  </label>
                  <select
                    value={strategy.trading_style}
                    onChange={(e) =>
                      onStrategyChange((draft) => {
                        draft.trading_style = e.target.value;
                      })
                    }
                    className="w-full rounded border bg-transparent px-3 py-2 text-xs outline-none focus:ring-1 capitalize"
                    style={{ borderColor: "var(--panel-border)" }}
                  >
                    {TRADING_STYLE_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {language === "zh" ? option.labelZh : option.labelEn}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-[11px] font-semibold uppercase tracking-wider">
                  {language === "zh" ? "默认标的（用逗号分隔）" : "Default Symbols (comma separated)"}
                </label>
                <input
                  type="text"
                  value={strategy.default_coins.join(", ")}
                  onChange={(e) =>
                    onStrategyChange((draft) => {
                      draft.default_coins = parseCoinsInput(e.target.value);
                    })
                  }
                  className="w-full rounded border bg-transparent px-3 py-2 text-xs outline-none focus:ring-1"
                  style={{ borderColor: "var(--panel-border)" }}
                />
              </div>

              <div>
                <h4 className="text-[11px] font-semibold uppercase tracking-wider">
                  {language === "zh" ? "风险控制" : "Risk Management"}
                </h4>
                <div className="mt-3 grid gap-3 md:grid-cols-3">
                  {RISK_FIELDS.map((field) => (
                    <div key={field.key} className="space-y-1">
                      <label className="text-[10px] uppercase tracking-wider" style={{ color: "var(--muted-text)" }}>
                        {language === "zh" ? field.labelZh : field.labelEn}
                      </label>
                      <input
                        type="number"
                        value={strategy.risk_management[field.key] ?? 0}
                        onChange={(e) =>
                          onStrategyChange((draft) => {
                            draft.risk_management[field.key] = Number(e.target.value);
                          })
                        }
                        className="w-full rounded border bg-transparent px-3 py-2 text-xs outline-none focus:ring-1"
                        style={{ borderColor: "var(--panel-border)" }}
                      />
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="text-[11px] font-semibold uppercase tracking-wider">
                  {language === "zh" ? "高级下单控制" : "Advanced Orders"}
                </h4>
                <div className="mt-3 grid gap-3 md:grid-cols-2">
                  <label className="flex items-center gap-2 text-[10px] uppercase tracking-widest" style={{ color: "var(--muted-text)" }}>
                    <input
                      type="checkbox"
                      className="h-4 w-4"
                      checked={strategy.advanced_orders.enable_take_profit}
                      onChange={(e) =>
                        onStrategyChange((draft) => {
                          draft.advanced_orders.enable_take_profit = e.target.checked;
                        })
                      }
                    />
                    {language === "zh" ? "启用止盈" : "Enable Take Profit"}
                  </label>
                  <div className="flex items-center gap-2">
                    <input
                      type="number"
                      value={strategy.advanced_orders.take_profit_pct}
                      onChange={(e) =>
                        onStrategyChange((draft) => {
                          draft.advanced_orders.take_profit_pct = Number(e.target.value);
                        })
                      }
                      className="w-full rounded border bg-transparent px-3 py-2 text-xs outline-none focus:ring-1"
                      style={{ borderColor: "var(--panel-border)" }}
                      placeholder={language === "zh" ? "止盈%" : "Take Profit %"}
                    />
                    <span className="text-[11px]" style={{ color: "var(--muted-text)" }}>%</span>
                  </div>
                  <label className="flex items-center gap-2 text-[10px] uppercase tracking-widest" style={{ color: "var(--muted-text)" }}>
                    <input
                      type="checkbox"
                      className="h-4 w-4"
                      checked={strategy.advanced_orders.enable_stop_loss}
                      onChange={(e) =>
                        onStrategyChange((draft) => {
                          draft.advanced_orders.enable_stop_loss = e.target.checked;
                        })
                      }
                    />
                    {language === "zh" ? "启用止损" : "Enable Stop Loss"}
                  </label>
                  <div className="flex items-center gap-2">
                    <input
                      type="number"
                      value={strategy.advanced_orders.stop_loss_pct}
                      onChange={(e) =>
                        onStrategyChange((draft) => {
                          draft.advanced_orders.stop_loss_pct = Number(e.target.value);
                        })
                      }
                      className="w-full rounded border bg-transparent px-3 py-2 text-xs outline-none focus:ring-1"
                      style={{ borderColor: "var(--panel-border)" }}
                      placeholder={language === "zh" ? "止损%" : "Stop Loss %"}
                    />
                    <span className="text-[11px]" style={{ color: "var(--muted-text)" }}>%</span>
                  </div>
                </div>
              </div>

              <div className="space-y-3">
                <p className="text-[10px]" style={{ color: "var(--muted-text)" }}>
                  {language === "zh"
                    ? "提示词内容请前往“智能体提示词”标签页统一编辑。"
                    : "Manage prompt content from the Agent Prompts tab."}
                </p>
              </div>
            </div>
          )}
        </div>

        {error && (
          <div className="mt-4 rounded border px-3 py-2 text-[10px]" style={{ borderColor: "#ef4444", color: "#ef4444" }}>
            {error}
          </div>
        )}

        <div className="mt-6 flex items-center justify-end gap-2">
          <button
            onClick={onClose}
            className="rounded border px-4 py-2 text-[11px] uppercase tracking-widest"
            style={{ borderColor: "var(--panel-border)", color: "var(--muted-text)" }}
          >
            {language === "zh" ? "取消" : "Cancel"}
          </button>
          <button
            onClick={onSubmit}
            disabled={accountsForm.length === 0 || modelsForm.length === 0}
            className="rounded px-4 py-2 text-[11px] font-semibold uppercase tracking-widest transition disabled:opacity-40"
            style={{ background: "var(--brand-accent)", color: "#ffffff" }}
          >
            {language === "zh" ? "确认添加" : "Add Agent"}
          </button>
        </div>
      </div>
    </div>
  );
}

