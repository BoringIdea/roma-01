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
      ) : (
        <div className="text-[11px]" style={{ color: "var(--muted-text)" }}>
          {language === "zh" ? "未获取到系统配置。" : "System configuration unavailable."}
        </div>
      )}
    </section>
  );
}

