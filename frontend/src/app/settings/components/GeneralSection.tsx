"use client";

import { LOG_LEVEL_OPTIONS, PROMPT_LANGUAGE_OPTIONS } from "@/app/settings/constants";
import type { SystemConfig } from "@/types";

interface GeneralSectionProps {
  language: string;
  configLoading: boolean;
  systemForm: SystemConfig | null;
  onSystemChange: (updater: (prev: SystemConfig) => SystemConfig) => void;
}

export function GeneralSection({ language, configLoading, systemForm, onSystemChange }: GeneralSectionProps) {
  return (
    <section
      className="rounded-xl border p-5"
      style={{ borderColor: "var(--panel-border)", background: "var(--panel-bg)" }}
    >
      <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider">
        {language === "zh" ? "系统设置" : "System Settings"}
      </h2>

      {configLoading && !systemForm ? (
        <div className="text-[11px]" style={{ color: "var(--muted-text)" }}>
          {language === "zh" ? "加载系统配置..." : "Loading system configuration..."}
        </div>
      ) : systemForm ? (
        <>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-1">
              <label className="text-[11px] font-semibold uppercase tracking-wider">
                {language === "zh" ? "扫描间隔（分钟）" : "Scan Interval (minutes)"}
              </label>
              <input
                type="number"
                min={1}
                max={60}
                value={systemForm.scan_interval_minutes}
                onChange={(e) =>
                  onSystemChange((prev) => ({
                    ...prev,
                    scan_interval_minutes: Number(e.target.value),
                  }))
                }
                className="w-full rounded border bg-transparent px-3 py-2 text-xs outline-none focus:ring-1"
                style={{ borderColor: "var(--panel-border)" }}
              />
            </div>

            <div className="space-y-1">
              <label className="text-[11px] font-semibold uppercase tracking-wider">
                {language === "zh" ? "并发智能体上限" : "Max Concurrent Agents"}
              </label>
              <input
                type="number"
                min={1}
                max={50}
                value={systemForm.max_concurrent_agents}
                onChange={(e) =>
                  onSystemChange((prev) => ({
                    ...prev,
                    max_concurrent_agents: Number(e.target.value),
                  }))
                }
                className="w-full rounded border bg-transparent px-3 py-2 text-xs outline-none focus:ring-1"
                style={{ borderColor: "var(--panel-border)" }}
              />
            </div>

            <div className="space-y-1">
              <label className="text-[11px] font-semibold uppercase tracking-wider">
                {language === "zh" ? "日志等级" : "Log Level"}
              </label>
              <select
                value={systemForm.log_level}
                onChange={(e) =>
                  onSystemChange((prev) => ({
                    ...prev,
                    log_level: e.target.value as SystemConfig["log_level"],
                  }))
                }
                className="w-full rounded border bg-transparent px-3 py-2 text-xs outline-none focus:ring-1"
                style={{ borderColor: "var(--panel-border)" }}
              >
                {LOG_LEVEL_OPTIONS.map((level) => (
                  <option key={level} value={level}>
                    {level}
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-1">
              <label className="text-[11px] font-semibold uppercase tracking-wider">
                {language === "zh" ? "提示词语言" : "Prompt Language"}
              </label>
              <select
                value={systemForm.prompt_language}
                onChange={(e) =>
                  onSystemChange((prev) => ({
                    ...prev,
                    prompt_language: e.target.value as SystemConfig["prompt_language"],
                  }))
                }
                className="w-full rounded border bg-transparent px-3 py-2 text-xs capitalize outline-none focus:ring-1"
                style={{ borderColor: "var(--panel-border)" }}
              >
                {PROMPT_LANGUAGE_OPTIONS.map((option) => (
                  <option key={option} value={option}>
                    {option.toUpperCase()}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Trade History Analysis Section */}
          <div className="mt-6 border-t pt-6" style={{ borderColor: "var(--panel-border)" }}>
          <h3 className="mb-4 text-xs font-semibold uppercase tracking-wider">
            {language === "zh" ? "交易历史分析" : "Trade History Analysis"}
          </h3>
          
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-1">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={systemForm.trade_history_analysis?.enabled ?? true}
                  onChange={(e) =>
                    onSystemChange((prev) => ({
                      ...prev,
                      trade_history_analysis: {
                        ...(prev.trade_history_analysis || {
                          enabled: true,
                          analysis_interval_hours: 12,
                          analysis_period_days: 30,
                          min_trades_required: 10,
                        }),
                        enabled: e.target.checked,
                      },
                    }))
                  }
                  className="rounded border"
                  style={{ borderColor: "var(--panel-border)" }}
                />
                <span className="text-[11px] font-semibold uppercase tracking-wider">
                  {language === "zh" ? "启用分析" : "Enable Analysis"}
                </span>
              </label>
              <p className="text-[10px]" style={{ color: "var(--muted-text)" }}>
                {language === "zh"
                  ? "自动分析交易历史并生成优化建议"
                  : "Automatically analyze trade history and generate insights"}
              </p>
            </div>

            <div className="space-y-1">
              <label className="text-[11px] font-semibold uppercase tracking-wider">
                {language === "zh" ? "分析间隔（小时）" : "Analysis Interval (hours)"}
              </label>
              <input
                type="number"
                min={1}
                max={168}
                step={0.5}
                value={systemForm.trade_history_analysis?.analysis_interval_hours ?? 12}
                onChange={(e) =>
                  onSystemChange((prev) => ({
                    ...prev,
                    trade_history_analysis: {
                      ...(prev.trade_history_analysis || {
                        enabled: true,
                        analysis_interval_hours: 12,
                        analysis_period_days: 30,
                        min_trades_required: 10,
                      }),
                      analysis_interval_hours: Number(e.target.value),
                    },
                  }))
                }
                disabled={!systemForm.trade_history_analysis?.enabled}
                className="w-full rounded border bg-transparent px-3 py-2 text-xs outline-none focus:ring-1 disabled:opacity-50"
                style={{ borderColor: "var(--panel-border)" }}
              />
            </div>

            <div className="space-y-1">
              <label className="text-[11px] font-semibold uppercase tracking-wider">
                {language === "zh" ? "分析周期（天）" : "Analysis Period (days)"}
              </label>
              <input
                type="number"
                min={7}
                max={365}
                value={systemForm.trade_history_analysis?.analysis_period_days ?? 30}
                onChange={(e) =>
                  onSystemChange((prev) => ({
                    ...prev,
                    trade_history_analysis: {
                      ...(prev.trade_history_analysis || {
                        enabled: true,
                        analysis_interval_hours: 12,
                        analysis_period_days: 30,
                        min_trades_required: 10,
                      }),
                      analysis_period_days: Number(e.target.value),
                    },
                  }))
                }
                disabled={!systemForm.trade_history_analysis?.enabled}
                className="w-full rounded border bg-transparent px-3 py-2 text-xs outline-none focus:ring-1 disabled:opacity-50"
                style={{ borderColor: "var(--panel-border)" }}
              />
            </div>

            <div className="space-y-1">
              <label className="text-[11px] font-semibold uppercase tracking-wider">
                {language === "zh" ? "最少交易数" : "Min Trades Required"}
              </label>
              <input
                type="number"
                min={5}
                max={1000}
                value={systemForm.trade_history_analysis?.min_trades_required ?? 10}
                onChange={(e) =>
                  onSystemChange((prev) => ({
                    ...prev,
                    trade_history_analysis: {
                      ...(prev.trade_history_analysis || {
                        enabled: true,
                        analysis_interval_hours: 12,
                        analysis_period_days: 30,
                        min_trades_required: 10,
                      }),
                      min_trades_required: Number(e.target.value),
                    },
                  }))
                }
                disabled={!systemForm.trade_history_analysis?.enabled}
                className="w-full rounded border bg-transparent px-3 py-2 text-xs outline-none focus:ring-1 disabled:opacity-50"
                style={{ borderColor: "var(--panel-border)" }}
              />
              <p className="text-[10px]" style={{ color: "var(--muted-text)" }}>
                {language === "zh"
                  ? "少于这个数量的交易将不进行分析"
                  : "Analysis will not run if trades are fewer than this"}
              </p>
            </div>
          </div>
          </div>
        </>
      ) : (
        <div className="text-[11px]" style={{ color: "var(--muted-text)" }}>
          {language === "zh" ? "未获取到系统配置。" : "System configuration unavailable."}
        </div>
      )}
    </section>
  );
}

