"use client";

import { PROMPT_LANGUAGE_OPTIONS } from "@/app/settings/constants";
import type { AccountFormState, ModelFormState } from "@/app/settings/types";
import type { ConfigAgent, PromptLanguage, SystemConfig } from "@/types";

const TRADING_STYLES = [
  { value: "balanced", labelZh: "均衡", labelEn: "Balanced" },
  { value: "aggressive", labelZh: "激进", labelEn: "Aggressive" },
  { value: "conservative", labelZh: "稳健", labelEn: "Conservative" },
];

const RISK_FIELDS: Array<{
  key: keyof ConfigAgent["strategy"]["risk_management"];
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
    .split(/[\s,]+/)
    .map((coin) => coin.trim().toUpperCase())
    .filter(Boolean);

interface AgentStrategyEditorProps {
  language: string;
  agent: ConfigAgent;
  onChange: (updater: (draft: ConfigAgent) => ConfigAgent) => void;
}

function AgentStrategyEditor({ language, agent, onChange }: AgentStrategyEditorProps) {
  const strategy = agent.strategy;

  return (
    <div className="space-y-4 rounded border p-4" style={{ borderColor: "var(--panel-border)" }}>
      <div className="grid gap-4 md:grid-cols-3">
        <div className="space-y-1">
          <label className="text-[11px] font-semibold uppercase tracking-wider">
            {language === "zh" ? "初始资金" : "Initial Balance"}
          </label>
          <input
            type="number"
            value={strategy.initial_balance}
            onChange={(e) =>
              onChange((draft) => {
                draft.strategy.initial_balance = Number(e.target.value);
                return draft;
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
              onChange((draft) => {
                draft.strategy.scan_interval_minutes = Number(e.target.value);
                return draft;
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
              onChange((draft) => {
                draft.strategy.max_account_usage_pct = Number(e.target.value);
                return draft;
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
              onChange((draft) => {
                draft.strategy.prompt_language = e.target.value as PromptLanguage;
                return draft;
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
            {language === "zh" ? "默认标的（用逗号分隔）" : "Default Symbols (comma separated)"}
          </label>
          <input
            type="text"
            value={strategy.default_coins.join(", ")}
            onChange={(e) =>
              onChange((draft) => {
                draft.strategy.default_coins = parseCoinsInput(e.target.value);
                return draft;
              })
            }
            className="w-full rounded border bg-transparent px-3 py-2 text-xs outline-none focus:ring-1"
            style={{ borderColor: "var(--panel-border)" }}
          />
        </div>
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
                value={strategy.risk_management[field.key] ?? ""}
                onChange={(e) =>
                  onChange((draft) => {
                    draft.strategy.risk_management[field.key] = Number(e.target.value);
                    return draft;
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
                onChange((draft) => {
                  draft.strategy.advanced_orders.enable_take_profit = e.target.checked;
                  return draft;
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
                onChange((draft) => {
                  draft.strategy.advanced_orders.take_profit_pct = Number(e.target.value);
                  return draft;
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
                onChange((draft) => {
                  draft.strategy.advanced_orders.enable_stop_loss = e.target.checked;
                  return draft;
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
                onChange((draft) => {
                  draft.strategy.advanced_orders.stop_loss_pct = Number(e.target.value);
                  return draft;
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

      <div>
        <p className="text-[10px]" style={{ color: "var(--muted-text)" }}>
          {language === "zh"
            ? "提示词内容现由“智能体提示词”标签页统一管理。"
            : "Prompt content is now managed from the Agent Prompts tab."}
        </p>
      </div>
    </div>
  );
}

interface AgentsSectionProps {
  language: string;
  configLoading: boolean;
  systemForm: SystemConfig | null;
  accountsForm: AccountFormState[];
  modelsForm: ModelFormState[];
  agentsForm: ConfigAgent[];
  filteredAgents: ConfigAgent[];
  agentFilterOptions: string[];
  agentViewFilter: string;
  onAgentFilterChange: (value: string) => void;
  onAgentIdChange: (previousId: string, nextId: string) => void;
  onAddAgent: () => void;
  onRemoveAgent: (agentIndex: number) => void;
  updateAgentAt: (
    agentIndex: number,
    updater: (draft: ConfigAgent) => ConfigAgent,
  ) => void;
}

export function AgentsSection({
  language,
  configLoading,
  systemForm,
  accountsForm,
  modelsForm,
  agentsForm,
  filteredAgents,
  agentFilterOptions,
  agentViewFilter,
  onAgentFilterChange,
  onAgentIdChange,
  onAddAgent,
  onRemoveAgent,
  updateAgentAt,
}: AgentsSectionProps) {
  return (
    <section
      className="rounded-xl border p-5"
      style={{ borderColor: "var(--panel-border)", background: "var(--panel-bg)" }}
    >
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="text-sm font-semibold uppercase tracking-wider">
            {language === "zh" ? "智能体配置" : "Agent Configuration"}
          </h2>
          <p className="text-[11px]" style={{ color: "var(--muted-text)" }}>
            {language === "zh"
              ? "管理交易智能体与账户、模型的绑定，调整策略参数。"
              : "Manage trading agents, bindings, and strategy parameters."}
          </p>
          {(accountsForm.length === 0 || modelsForm.length === 0) && (
            <p className="mt-1 text-[10px]" style={{ color: "#ef4444" }}>
              {language === "zh"
                ? "请先在\"账户配置\"和\"模型配置\"选项卡中至少保留一个配置。"
                : "Ensure at least one account and one model exist under the Accounts and Models tabs."}
            </p>
          )}
        </div>
        <button
          onClick={onAddAgent}
          disabled={accountsForm.length === 0 || modelsForm.length === 0}
          className="rounded border px-3 py-2 text-[11px] uppercase tracking-widest transition hover:opacity-80 disabled:opacity-40"
          style={{ borderColor: "var(--panel-border)" }}
        >
          {language === "zh" ? "新增智能体" : "Add Agent"}
        </button>
      </div>

      {configLoading && agentsForm.length === 0 ? (
        <div
          className="mt-4 flex h-32 items-center justify-center rounded border text-xs"
          style={{ borderColor: "var(--panel-border)", color: "var(--muted-text)" }}
        >
          {language === "zh" ? "加载智能体配置..." : "Loading agent configuration..."}
        </div>
      ) : agentsForm.length === 0 ? (
        <div
          className="mt-4 flex h-32 items-center justify-center rounded border text-xs"
          style={{ borderColor: "var(--panel-border)", color: "var(--muted-text)" }}
        >
          {language === "zh" ? "暂无智能体配置" : "No agents configured yet."}
        </div>
      ) : (
        <>
          <div className="mt-4 flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
            <div>
              <span className="text-[11px] font-semibold uppercase tracking-wider">
                {language === "zh" ? "筛选智能体" : "Filter Agents"}
              </span>
              <p className="text-[10px]" style={{ color: "var(--muted-text)" }}>
                {language === "zh"
                  ? "选择需要查看或编辑的智能体，默认为显示全部。"
                  : "Select an agent to review or edit, or show all."}
              </p>
            </div>
            <select
              value={agentViewFilter}
              onChange={(e) => onAgentFilterChange(e.target.value)}
              className="w-full rounded border bg-transparent px-3 py-2 text-xs outline-none focus:ring-1 capitalize md:w-64"
              style={{ borderColor: "var(--panel-border)" }}
            >
              {agentFilterOptions.map((option) => (
                <option key={option} value={option}>
                  {option === "__all__"
                    ? language === "zh"
                      ? "全部智能体"
                      : "All Agents"
                    : option}
                </option>
              ))}
            </select>
          </div>

          {filteredAgents.length === 0 ? (
            <div
              className="mt-4 flex h-32 items-center justify-center rounded border text-xs"
              style={{ borderColor: "var(--panel-border)", color: "var(--muted-text)" }}
            >
              {language === "zh" ? "当前筛选没有结果" : "No agents match the current filter."}
            </div>
          ) : (
            <div className="mt-4 space-y-5">
              {filteredAgents.map((agent) => {
                const agentIndex = agentsForm.indexOf(agent);
                if (agentIndex < 0) {
                  return null;
                }
                const displayIndex = agentIndex + 1;
                return (
                  <div
                    key={`${agent.id}-${agentIndex}`}
                    className="space-y-4 rounded-lg border p-4"
                    style={{ borderColor: "var(--panel-border)", background: "var(--panel-bg)" }}
                  >
                    <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                      <div>
                        <h3 className="text-xs font-semibold uppercase tracking-wider">
                          {language === "zh" ? `智能体 #${displayIndex}` : `Agent #${displayIndex}`}
                        </h3>
                        <p className="text-[10px]" style={{ color: "var(--muted-text)" }}>
                          {language === "zh" ? "当前 ID：" : "Current ID:"} {agent.id}
                        </p>
                      </div>
                      <div className="flex items-center gap-3">
                        <label
                          className="flex items-center gap-2 text-[10px] uppercase tracking-widest"
                          style={{ color: "var(--muted-text)" }}
                        >
                          <input
                            type="checkbox"
                            className="h-4 w-4"
                            checked={agent.enabled}
                            onChange={(e) =>
                              updateAgentAt(agentIndex, (draft) => {
                                draft.enabled = e.target.checked;
                                return draft;
                              })
                            }
                          />
                          {language === "zh" ? "启用" : "Enabled"}
                        </label>
                        <button
                          onClick={() => onRemoveAgent(agentIndex)}
                          disabled={agentsForm.length <= 1}
                          className="rounded border px-2 py-1 text-[10px] uppercase tracking-widest transition hover:opacity-80 disabled:opacity-40"
                          style={{ borderColor: "var(--panel-border)" }}
                        >
                          {language === "zh" ? "删除" : "Remove"}
                        </button>
                      </div>
                    </div>

                    <div className="grid gap-4 md:grid-cols-3">
                      <div className="space-y-1">
                        <label className="text-[11px] font-semibold uppercase tracking-wider">
                          {language === "zh" ? "智能体 ID" : "Agent ID"}
                        </label>
                        <input
                          type="text"
                          value={agent.id}
                          onChange={(e) => {
                            const prevId = agent.id;
                            const nextId = e.target.value;
                            updateAgentAt(agentIndex, (draft) => {
                              draft.id = nextId;
                              return draft;
                            });
                            onAgentIdChange(prevId, nextId);
                          }}
                          className="w-full rounded border bg-transparent px-3 py-2 text-xs outline-none focus:ring-1"
                          style={{ borderColor: "var(--panel-border)" }}
                        />
                      </div>

                      <div className="space-y-1">
                        <label className="text-[11px] font-semibold uppercase tracking-wider">
                          {language === "zh" ? "显示名称" : "Display Name"}
                        </label>
                        <input
                          type="text"
                          value={agent.name}
                          onChange={(e) =>
                            updateAgentAt(agentIndex, (draft) => {
                              draft.name = e.target.value;
                              return draft;
                            })
                          }
                          className="w-full rounded border bg-transparent px-3 py-2 text-xs outline-none focus:ring-1"
                          style={{ borderColor: "var(--panel-border)" }}
                        />
                      </div>

                      <div className="space-y-1">
                        <label className="text-[11px] font-semibold uppercase tracking-wider">
                          {language === "zh" ? "交易风格" : "Trading Style"}
                        </label>
                        <select
                          value={agent.strategy.trading_style}
                          onChange={(e) =>
                            updateAgentAt(agentIndex, (draft) => {
                              draft.strategy.trading_style = e.target.value;
                              return draft;
                            })
                          }
                          className="w-full rounded border bg-transparent px-3 py-2 text-xs capitalize outline-none focus:ring-1"
                          style={{ borderColor: "var(--panel-border)" }}
                        >
                          {TRADING_STYLES.map((style) => (
                            <option key={style.value} value={style.value}>
                              {language === "zh" ? style.labelZh : style.labelEn}
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>

                    <div className="grid gap-4 md:grid-cols-2">
                      <div className="space-y-1">
                        <label className="text-[11px] font-semibold uppercase tracking-wider">
                          {language === "zh" ? "绑定账户" : "Linked Account"}
                        </label>
                        <select
                          value={agent.account_id}
                          onChange={(e) =>
                            updateAgentAt(agentIndex, (draft) => {
                              draft.account_id = e.target.value;
                              return draft;
                            })
                          }
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
                          value={agent.model_id}
                          onChange={(e) =>
                            updateAgentAt(agentIndex, (draft) => {
                              draft.model_id = e.target.value;
                              return draft;
                            })
                          }
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

                    <AgentStrategyEditor
                      language={language}
                      agent={agent}
                      onChange={(updater) => updateAgentAt(agentIndex, updater)}
                    />
                  </div>
                );
              })}
            </div>
          )}
        </>
      )}
    </section>
  );
}

export { TRADING_STYLES };

