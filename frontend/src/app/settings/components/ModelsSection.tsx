"use client";

import { useState } from "react";

import type { ModelFormState } from "@/app/settings/types";
import { MODEL_FILTER_ALL, MODEL_LOCATION_OPTIONS } from "@/app/settings/constants";

interface ModelsSectionProps {
  language: string;
  configLoading: boolean;
  modelFilterOptions: string[];
  modelViewFilter: string;
  onModelFilterChange: (value: string) => void;
  onModelIdChange: (previousId: string, nextId: string) => void;
  onAddModel: () => void;
  modelsForm: ModelFormState[];
  filteredModels: ModelFormState[];
  onAddModelField: (modelIndex: number) => void;
  onRemoveModelField: (modelIndex: number, fieldIndex: number) => void;
  onRemoveModel: (modelIndex: number) => void;
  updateModelAt: (
    modelIndex: number,
    updater: (draft: ModelFormState) => ModelFormState,
  ) => void;
}

export function ModelsSection({
  language,
  configLoading,
  modelFilterOptions,
  modelViewFilter,
  onModelFilterChange,
  onModelIdChange,
  onAddModel,
  modelsForm,
  filteredModels,
  onAddModelField,
  onRemoveModelField,
  onRemoveModel,
  updateModelAt,
}: ModelsSectionProps) {
  const [visibleSecrets, setVisibleSecrets] = useState<Record<string, boolean>>({});

  const isSensitiveKey = (key: string) => {
    const normalized = key.trim().toLowerCase();
    if (!normalized) return false;
    return (
      normalized.includes("key") ||
      normalized.includes("secret") ||
      normalized.includes("token")
    );
  };

  const makeSecretId = (modelId: string, fieldKey: string, index?: number) => {
    const suffix = fieldKey.trim() ? fieldKey : String(index ?? 0);
    return `${modelId}::${suffix}`;
  };

  const toggleSecret = (id: string) => {
    setVisibleSecrets((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <section
      className="rounded-xl border p-5"
      style={{ borderColor: "var(--panel-border)", background: "var(--panel-bg)" }}
    >
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="text-sm font-semibold uppercase tracking-wider">
            {language === "zh" ? "模型配置" : "Model Configuration"}
          </h2>
          <p className="text-[11px]" style={{ color: "var(--muted-text)" }}>
            {language === "zh"
              ? "管理可用的大模型提供方、API Key 以及模型参数。"
              : "Manage available model providers, API keys, and tuning parameters."}
          </p>
        </div>
        <button
          onClick={onAddModel}
          className="rounded border px-3 py-2 text-[11px] uppercase tracking-widest transition hover:opacity-80"
          style={{ borderColor: "var(--panel-border)" }}
        >
          {language === "zh" ? "新增模型" : "Add Model"}
        </button>
      </div>

      {configLoading && modelsForm.length === 0 ? (
        <div
          className="mt-4 flex h-32 items-center justify-center rounded border text-xs"
          style={{ borderColor: "var(--panel-border)", color: "var(--muted-text)" }}
        >
          {language === "zh" ? "加载模型配置..." : "Loading model configuration..."}
        </div>
      ) : modelsForm.length === 0 ? (
        <div
          className="mt-4 flex h-32 items-center justify-center rounded border text-xs"
          style={{ borderColor: "var(--panel-border)", color: "var(--muted-text)" }}
        >
          {language === "zh" ? "暂无模型配置" : "No models configured yet."}
        </div>
      ) : (
        <>
          <div className="mt-4 flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
            <div>
              <span className="text-[11px] font-semibold uppercase tracking-wider">
                {language === "zh" ? "筛选模型" : "Filter Models"}
              </span>
              <p className="text-[10px]" style={{ color: "var(--muted-text)" }}>
                {language === "zh"
                  ? "选择需要查看或编辑的模型，默认为显示全部。"
                  : "Select a specific model to review or edit, or show all."}
              </p>
            </div>
            <select
              value={modelViewFilter}
              onChange={(e) => onModelFilterChange(e.target.value)}
              className="w-full rounded border bg-transparent px-3 py-2 text-xs outline-none focus:ring-1 capitalize md:w-64"
              style={{ borderColor: "var(--panel-border)" }}
            >
              {modelFilterOptions.map((option) => {
                if (option === MODEL_FILTER_ALL) {
                  return (
                    <option key={option} value={option}>
                      {language === "zh" ? "全部模型" : "All Models"}
                    </option>
                  );
                }
                const record = modelsForm.find((model) => model.id === option);
                const label = record
                  ? `${option} (${record.model || record.provider || "model"})`
                  : option;
                return (
                  <option key={option} value={option}>
                    {label}
                  </option>
                );
              })}
            </select>
          </div>

          {filteredModels.length === 0 ? (
            <div
              className="mt-4 flex h-32 items-center justify-center rounded border text-xs"
              style={{ borderColor: "var(--panel-border)", color: "var(--muted-text)" }}
            >
              {language === "zh" ? "当前筛选没有结果" : "No models match the current filter."}
            </div>
          ) : (
            <div className="mt-4 space-y-5">
              {filteredModels.map((model) => {
                const modelIndex = modelsForm.indexOf(model);
                if (modelIndex < 0) {
                  return null;
                }
                const displayIndex = modelIndex + 1;
                return (
                  <div
                    key={`${model.id}-${modelIndex}`}
                    className="space-y-4 rounded-lg border p-4"
                    style={{ borderColor: "var(--panel-border)", background: "var(--panel-bg)" }}
                  >
                    <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                      <div>
                        <h3 className="text-xs font-semibold uppercase tracking-wider">
                          {language === "zh" ? `模型 #${displayIndex}` : `Model #${displayIndex}`}
                        </h3>
                        <p className="text-[10px]" style={{ color: "var(--muted-text)" }}>
                          {language === "zh" ? "当前 ID：" : "Current ID:"} {model.id}
                        </p>
                      </div>
                      <button
                        onClick={() => onRemoveModel(modelIndex)}
                        disabled={modelsForm.length <= 1}
                        className="rounded border px-2 py-1 text-[10px] uppercase tracking-widest transition hover:opacity-80 disabled:opacity-40"
                        style={{ borderColor: "var(--panel-border)" }}
                      >
                        {language === "zh" ? "删除" : "Remove"}
                      </button>
                    </div>

                    <div className="grid gap-4 md:grid-cols-3">
                      <div className="space-y-1">
                        <label className="text-[11px] font-semibold uppercase tracking-wider">
                          {language === "zh" ? "模型 ID" : "Model ID"}
                        </label>
                        <input
                          type="text"
                          value={model.id}
                          onChange={(e) => {
                            const prevId = model.id;
                            const nextId = e.target.value;
                            updateModelAt(modelIndex, (draft) => {
                              draft.id = nextId;
                              return draft;
                            });
                            onModelIdChange(prevId, nextId);
                          }}
                          className="w-full rounded border bg-transparent px-3 py-2 text-xs outline-none focus:ring-1"
                          style={{ borderColor: "var(--panel-border)" }}
                        />
                      </div>

                      <div className="space-y-1">
                        <label className="text-[11px] font-semibold uppercase tracking-wider">
                          {language === "zh" ? "提供方" : "Provider"}
                        </label>
                        <input
                          type="text"
                          value={model.provider}
                          onChange={(e) =>
                            updateModelAt(modelIndex, (draft) => {
                              draft.provider = e.target.value;
                              return draft;
                            })
                          }
                          className="w-full rounded border bg-transparent px-3 py-2 text-xs outline-none focus:ring-1"
                          style={{ borderColor: "var(--panel-border)" }}
                        />
                      </div>

                      <div className="space-y-1">
                        <label className="text-[11px] font-semibold uppercase tracking-wider">
                          {language === "zh" ? "模型名称" : "Model"}
                        </label>
                        <input
                          type="text"
                          value={model.model}
                          onChange={(e) =>
                            updateModelAt(modelIndex, (draft) => {
                              draft.model = e.target.value;
                              return draft;
                            })
                          }
                          className="w-full rounded border bg-transparent px-3 py-2 text-xs outline-none focus:ring-1"
                          style={{ borderColor: "var(--panel-border)" }}
                        />
                      </div>
                    </div>

                    <div className="grid gap-4 md:grid-cols-3">
                      <div className="space-y-1">
                        <label className="text-[11px] font-semibold uppercase tracking-wider">
                          {language === "zh" ? "温度" : "Temperature"}
                        </label>
                        <input
                          type="number"
                          step="0.01"
                          value={model.temperature ?? ""}
                          onChange={(e) =>
                            updateModelAt(modelIndex, (draft) => {
                              const value = e.target.value.trim();
                              draft.temperature = value === "" ? undefined : Number(value);
                              return draft;
                            })
                          }
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
                          value={model.max_tokens ?? ""}
                          onChange={(e) =>
                            updateModelAt(modelIndex, (draft) => {
                              const value = e.target.value.trim();
                              draft.max_tokens = value === "" ? undefined : Number(value);
                              return draft;
                            })
                          }
                          className="w-full rounded border bg-transparent px-3 py-2 text-xs outline-none focus:ring-1"
                          style={{ borderColor: "var(--panel-border)" }}
                        />
                      </div>

                      <div className="space-y-1">
                        <label className="text-[11px] font-semibold uppercase tracking-wider">
                          {language === "zh" ? "部署区域" : "Location"}
                        </label>
                        <select
                          value={model.location_display || model.location || "international"}
                          onChange={(e) =>
                            updateModelAt(modelIndex, (draft) => {
                              draft.location = e.target.value;
                              draft.location_display = e.target.value;
                              return draft;
                            })
                          }
                          className="w-full rounded border bg-transparent px-3 py-2 text-xs capitalize outline-none focus:ring-1"
                          style={{ borderColor: "var(--panel-border)" }}
                        >
                          {MODEL_LOCATION_OPTIONS.map((option) => (
                            <option key={option.value} value={option.value}>
                              {language === "zh" ? option.labelZh : option.labelEn}
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>

                    <div className="space-y-1">
                      <label className="text-[11px] font-semibold uppercase tracking-wider">API Key</label>
                      {(() => {
                        const fieldId = makeSecretId(model.id, "api_key");
                        const isVisible = visibleSecrets[fieldId];
                        const rawValue = model.api_key_display ?? model.api_key ?? "";
                        const shouldMask = rawValue.length > 0;
                        return (
                          <div className="flex items-center gap-2">
                            <input
                              type={shouldMask && !isVisible ? "password" : "text"}
                              value={rawValue}
                              onChange={(e) =>
                                updateModelAt(modelIndex, (draft) => {
                                  draft.api_key = e.target.value;
                                  draft.api_key_display = e.target.value;
                                  return draft;
                                })
                              }
                              className="w-full rounded border bg-transparent px-3 py-2 text-xs outline-none focus:ring-1"
                              style={{ borderColor: "var(--panel-border)" }}
                              placeholder={language === "zh" ? "支持 ${ENV_VAR}" : "Supports ${ENV_VAR}"}
                            />
                            {shouldMask && (
                              <button
                                type="button"
                                onClick={() => toggleSecret(fieldId)}
                                className="rounded border px-2 py-1 text-[10px] transition hover:opacity-80"
                                style={{ borderColor: "var(--panel-border)", color: "var(--muted-text)" }}
                                aria-label={isVisible ? (language === "zh" ? "隐藏 API Key" : "Hide API Key") : language === "zh" ? "显示 API Key" : "Show API Key"}
                              >
                                {isVisible ? "🙈" : "👁"}
                              </button>
                            )}
                          </div>
                        );
                      })()}
                      {model.api_key &&
                        model.api_key_display &&
                        model.api_key !== model.api_key_display && (
                          <p className="text-[10px]" style={{ color: "var(--muted-text)" }}>
                            {language === "zh"
                              ? `值来自环境变量 ${model.api_key}`
                              : `Value sourced from env ${model.api_key}`}
                          </p>
                        )}
                    </div>

                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-[11px] font-semibold uppercase tracking-wider">
                          {language === "zh" ? "额外字段" : "Extra Fields"}
                        </span>
                        <button
                          onClick={() => onAddModelField(modelIndex)}
                          className="rounded border px-2 py-1 text-[10px] uppercase tracking-widest transition hover:opacity-80"
                          style={{ borderColor: "var(--panel-border)" }}
                        >
                          {language === "zh" ? "新增字段" : "Add Field"}
                        </button>
                      </div>

                      {model.extraFields.length === 0 ? (
                        <p className="text-[10px]" style={{ color: "var(--muted-text)" }}>
                          {language === "zh"
                            ? "暂无额外字段，可用于自定义路由、Headers 等参数。"
                            : "No extra fields yet. Use this area for custom routes, headers, or other parameters."}
                        </p>
                      ) : (
                        <div className="space-y-2">
                          {model.extraFields.map((field, fieldIndex) => {
                            const isLocked = field.locked && field.key.trim().length > 0;
                            const isEnvPlaceholder =
                              field.rawValue.startsWith("${") && field.rawValue.endsWith("}");
                            return (
                              <div
                                key={`${field.key}-${fieldIndex}`}
                                className="space-y-1 rounded border p-2"
                                style={{ borderColor: "var(--panel-border)" }}
                              >
                                <div className="grid gap-2 md:grid-cols-[1fr_1fr_auto] md:items-center">
                                  <input
                                    type="text"
                                    value={field.key}
                                    readOnly={isLocked}
                                    onChange={(e) =>
                                      updateModelAt(modelIndex, (draft) => {
                                        const fields = [...draft.extraFields];
                                        if (!fields[fieldIndex].locked) {
                                          fields[fieldIndex] = {
                                            ...fields[fieldIndex],
                                            key: e.target.value,
                                          };
                                        }
                                        draft.extraFields = fields;
                                        return draft;
                                      })
                                    }
                                    className="rounded border bg-transparent px-3 py-2 text-xs outline-none focus:ring-1"
                                    style={{
                                      borderColor: "var(--panel-border)",
                                      opacity: isLocked ? 0.6 : 1,
                                    }}
                                    placeholder={language === "zh" ? "字段名" : "Field Key"}
                                  />
                                  <div className="flex items-center gap-2">
                                    {(() => {
                                      const fieldId = makeSecretId(model.id, field.key, fieldIndex);
                                      const isVisible = visibleSecrets[fieldId];
                                      const isEnvPlaceholderField =
                                        field.rawValue.startsWith("${") && field.rawValue.endsWith("}");
                                      const shouldMask = isSensitiveKey(field.key) && !isEnvPlaceholderField;
                                      return (
                                        <>
                                          <input
                                            type={shouldMask && !isVisible ? "password" : "text"}
                                            value={field.displayValue}
                                            onChange={(e) =>
                                              updateModelAt(modelIndex, (draft) => {
                                                const fields = [...draft.extraFields];
                                                fields[fieldIndex] = {
                                                  ...fields[fieldIndex],
                                                  rawValue: e.target.value,
                                                  displayValue: e.target.value,
                                                };
                                                draft.extraFields = fields;
                                                return draft;
                                              })
                                            }
                                            className="w-full rounded border bg-transparent px-3 py-2 text-xs outline-none focus:ring-1"
                                            style={{ borderColor: "var(--panel-border)" }}
                                            placeholder={language === "zh" ? "字段值" : "Field Value"}
                                          />
                                          {shouldMask && (
                                            <button
                                              type="button"
                                              onClick={() => toggleSecret(fieldId)}
                                              className="rounded border px-2 py-1 text-[10px] transition hover:opacity-80"
                                              style={{ borderColor: "var(--panel-border)", color: "var(--muted-text)" }}
                                              aria-label={isVisible ? (language === "zh" ? "隐藏字段值" : "Hide field value") : language === "zh" ? "显示字段值" : "Show field value"}
                                            >
                                              {isVisible ? "🙈" : "👁"}
                                            </button>
                                          )}
                                        </>
                                      );
                                    })()}
                                  </div>
                                  <button
                                    onClick={() => onRemoveModelField(modelIndex, fieldIndex)}
                                    className="rounded border px-2 py-1 text-[10px] uppercase tracking-widest transition hover:opacity-80"
                                    style={{ borderColor: "var(--panel-border)" }}
                                  >
                                    {language === "zh" ? "移除" : "Remove"}
                                  </button>
                                </div>
                                {isEnvPlaceholder && (
                                  <div className="text-[10px]" style={{ color: "var(--muted-text)" }}>
                                    {language === "zh"
                                      ? `值来自环境变量 ${field.rawValue}`
                                      : `Value sourced from env ${field.rawValue}`}
                                  </div>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>
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

