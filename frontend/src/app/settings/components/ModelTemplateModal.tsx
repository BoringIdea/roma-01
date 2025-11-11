"use client";

import type { ModelDraft } from "@/app/settings/types";
import { MODEL_LOCATION_OPTIONS, MODEL_TEMPLATES } from "@/app/settings/constants";

interface ModelTemplateModalProps {
  language: string;
  visible: boolean;
  modelDraft: ModelDraft;
  modelTemplateError: string | null;
  providerOptions: string[];
  modelsByProvider: Array<(typeof MODEL_TEMPLATES)[number]>;
  draftIdWasEdited: boolean;
  onClose: () => void;
  onProviderChange: (provider: string) => void;
  onModelChange: (model: string) => void;
  onDraftChange: (field: keyof ModelDraft, value: string) => void;
  onSubmit: () => void;
}

export function ModelTemplateModal({
  language,
  visible,
  modelDraft,
  modelTemplateError,
  providerOptions,
  modelsByProvider,
  draftIdWasEdited,
  onClose,
  onProviderChange,
  onModelChange,
  onDraftChange,
  onSubmit,
}: ModelTemplateModalProps) {
  if (!visible) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center px-4 backdrop-blur">
      <div
        className="w-full max-w-3xl rounded-xl border bg-[color:var(--panel-bg)] p-6 shadow-lg"
        style={{ borderColor: "var(--panel-border)" }}
      >
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-sm font-semibold uppercase tracking-widest" style={{ color: "var(--foreground)" }}>
              {language === "zh" ? "创建模型配置" : "Create Model Configuration"}
            </h2>
            <p className="mt-1 text-[11px]" style={{ color: "var(--muted-text)" }}>
              {language === "zh"
                ? "请选择模型提供方与型号，并填写自定义 ID、温度、最大 Token、部署区域与 API Key（可填环境变量占位符）。"
                : "Select a provider and model, then provide a custom ID, temperature, max tokens, location, and API key (environment variable placeholders are supported)."}
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
              {language === "zh" ? "提供方" : "Provider"}
            </label>
            <select
              value={modelDraft.provider}
              onChange={(e) => onProviderChange(e.target.value)}
              className="w-full rounded border bg-transparent px-3 py-2 text-xs outline-none focus:ring-1 capitalize"
              style={{ borderColor: "var(--panel-border)" }}
            >
              {providerOptions.map((provider) => (
                <option key={provider} value={provider}>
                  {provider}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-1">
            <label className="text-[11px] font-semibold uppercase tracking-wider">
              {language === "zh" ? "模型" : "Model"}
            </label>
            <select
              value={modelDraft.model}
              onChange={(e) => onModelChange(e.target.value)}
              className="w-full rounded border bg-transparent px-3 py-2 text-xs outline-none focus:ring-1"
              style={{ borderColor: "var(--panel-border)" }}
            >
              {modelsByProvider.map((template) => (
                <option key={template.templateId} value={template.model}>
                  {template.model}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-1">
            <label className="text-[11px] font-semibold uppercase tracking-wider">
              {language === "zh" ? "模型 ID" : "Model ID"}
            </label>
            <input
              type="text"
              value={modelDraft.id}
              onChange={(e) => onDraftChange("id", e.target.value)}
              className="w-full rounded border bg-transparent px-3 py-2 text-xs outline-none focus:ring-1"
              style={{ borderColor: "var(--panel-border)" }}
              placeholder={language === "zh" ? "自定义唯一 ID" : "Custom unique ID"}
            />
            {!draftIdWasEdited && (
              <p className="text-[10px]" style={{ color: "var(--muted-text)" }}>
                {language === "zh" ? "默认会根据提供方自动生成 ID。" : "Default ID uses provider prefix automatically."}
              </p>
            )}
          </div>

          <div className="space-y-1">
            <label className="text-[11px] font-semibold uppercase tracking-wider">
              {language === "zh" ? "温度" : "Temperature"}
            </label>
            <input
              type="number"
              step="0.01"
              value={modelDraft.temperature}
              onChange={(e) => onDraftChange("temperature", e.target.value)}
              className="w-full rounded border bg-transparent px-3 py-2 text-xs outline-none focus:ring-1"
              style={{ borderColor: "var(--panel-border)" }}
            />
          </div>

          <div className="space-y-1">
            <label className="text-[11px] font-semibold uppercase tracking-wider">
              {language === "zh" ? "最大 Token" : "Max Tokens"}
            </label>
            <input
              type="number"
              value={modelDraft.max_tokens}
              onChange={(e) => onDraftChange("max_tokens", e.target.value)}
              className="w-full rounded border bg-transparent px-3 py-2 text-xs outline-none focus:ring-1"
              style={{ borderColor: "var(--panel-border)" }}
            />
          </div>

          <div className="space-y-1">
            <label className="text-[11px] font-semibold uppercase tracking-wider">
              {language === "zh" ? "部署区域" : "Location"}
            </label>
            <select
              value={modelDraft.location}
              onChange={(e) => onDraftChange("location", e.target.value)}
              className="w-full rounded border bg-transparent px-3 py-2 text-xs outline-none focus:ring-1 capitalize"
              style={{ borderColor: "var(--panel-border)" }}
            >
              {MODEL_LOCATION_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {language === "zh" ? option.labelZh : option.labelEn}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-1 md:col-span-2">
            <label className="text-[11px] font-semibold uppercase tracking-wider">API Key</label>
            <input
              type="text"
              value={modelDraft.api_key}
              onChange={(e) => onDraftChange("api_key", e.target.value)}
              className="w-full rounded border bg-transparent px-3 py-2 text-xs outline-none focus:ring-1"
              style={{ borderColor: "var(--panel-border)" }}
              placeholder={language === "zh" ? "支持填写 ${ENV_VAR}" : "Supports ${ENV_VAR}"}
            />
          </div>
        </div>

        {modelTemplateError && (
          <div className="mt-4 rounded border px-3 py-2 text-[10px]" style={{ borderColor: "#ef4444", color: "#ef4444" }}>
            {modelTemplateError}
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
            className="rounded px-4 py-2 text-[11px] font-semibold uppercase tracking-widest transition"
            style={{ background: "var(--brand-accent)", color: "#ffffff" }}
          >
            {language === "zh" ? "确认添加" : "Add Model"}
          </button>
        </div>
      </div>
    </div>
  );
}

