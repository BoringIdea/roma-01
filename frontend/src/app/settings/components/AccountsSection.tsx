"use client";

import { useState } from "react";

import type { AccountFormState } from "@/app/settings/types";
import { ACCOUNT_FILTER_ALL, ACCOUNT_TYPES } from "@/app/settings/constants";
import { sortByKey } from "@/app/settings/helpers";

interface AccountsSectionProps {
  language: string;
  configLoading: boolean;
  accountFilterOptions: string[];
  accountViewFilter: string;
  onAccountFilterChange: (value: string) => void;
  onAccountIdChange: (previousId: string, nextId: string) => void;
  onAddAccount: () => void;
  accountsForm: AccountFormState[];
  filteredAccounts: AccountFormState[];
  onAddAccountField: (accountIndex: number) => void;
  onRemoveAccountField: (accountIndex: number, fieldIndex: number) => void;
  onRemoveAccount: (accountIndex: number) => void;
  updateAccountAt: (
    accountIndex: number,
    updater: (draft: AccountFormState) => AccountFormState,
  ) => void;
}

export function AccountsSection({
  language,
  configLoading,
  accountFilterOptions,
  accountViewFilter,
  onAccountFilterChange,
  onAccountIdChange,
  onAddAccount,
  accountsForm,
  filteredAccounts,
  onAddAccountField,
  onRemoveAccountField,
  onRemoveAccount,
  updateAccountAt,
}: AccountsSectionProps) {
  const [visibleSecrets, setVisibleSecrets] = useState<Record<string, boolean>>({});

  const isSensitiveKey = (key: string) => {
    const normalized = key.trim().toLowerCase();
    if (!normalized) return false;
    return (
      normalized.includes("private") ||
      normalized.includes("secret") ||
      normalized.includes("api_key") ||
      normalized.endsWith("key") ||
      normalized.includes("token")
    );
  };

  const makeSecretId = (accountId: string, fieldKey: string, index: number) =>
    `${accountId}::${fieldKey || index}`;

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
            {language === "zh" ? "账户配置" : "Account Configuration"}
          </h2>
          <p className="text-[11px]" style={{ color: "var(--muted-text)" }}>
            {language === "zh"
              ? "管理 DEX 账户、凭证与衍生参数，供智能体绑定使用。"
              : "Manage DEX accounts, credentials, and supporting parameters for agent bindings."}
          </p>
        </div>
        <button
          onClick={onAddAccount}
          className="rounded border px-3 py-2 text-[11px] uppercase tracking-widest transition hover:opacity-80"
          style={{ borderColor: "var(--panel-border)" }}
        >
          {language === "zh" ? "新增账户" : "Add Account"}
        </button>
      </div>

      {configLoading && accountsForm.length === 0 ? (
        <div
          className="mt-4 flex h-32 items-center justify-center rounded border text-xs"
          style={{ borderColor: "var(--panel-border)", color: "var(--muted-text)" }}
        >
          {language === "zh" ? "加载账户配置..." : "Loading account configuration..."}
        </div>
      ) : accountsForm.length === 0 ? (
        <div
          className="mt-4 flex h-32 items-center justify-center rounded border text-xs"
          style={{ borderColor: "var(--panel-border)", color: "var(--muted-text)" }}
        >
          {language === "zh" ? "暂无账户配置" : "No accounts configured yet."}
        </div>
      ) : (
        <>
          <div className="mt-4 flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
            <div>
              <span className="text-[11px] font-semibold uppercase tracking-wider">
                {language === "zh" ? "筛选账户" : "Filter Accounts"}
              </span>
              <p className="text-[10px]" style={{ color: "var(--muted-text)" }}>
                {language === "zh"
                  ? "选择需要查看或编辑的账户，默认为显示全部。"
                  : "Select an account to review or edit, or show all."}
              </p>
            </div>
            <select
              value={accountViewFilter}
              onChange={(e) => onAccountFilterChange(e.target.value)}
              className="w-full rounded border bg-transparent px-3 py-2 text-xs outline-none focus:ring-1 capitalize md:w-64"
              style={{ borderColor: "var(--panel-border)" }}
            >
              {accountFilterOptions.map((option) => {
                if (option === ACCOUNT_FILTER_ALL) {
                  return (
                    <option key={option} value={option}>
                      {language === "zh" ? "全部账户" : "All Accounts"}
                    </option>
                  );
                }
                const record = accountsForm.find((account) => account.id === option);
                const label = record
                  ? `${option} (${record.name || record.dex_type || "account"})`
                  : option;
                return (
                  <option key={option} value={option}>
                    {label}
                  </option>
                );
              })}
            </select>
          </div>

          {filteredAccounts.length === 0 ? (
            <div
              className="mt-4 flex h-32 items-center justify-center rounded border text-xs"
              style={{ borderColor: "var(--panel-border)", color: "var(--muted-text)" }}
            >
              {language === "zh" ? "当前筛选没有结果" : "No accounts match the current filter."}
            </div>
          ) : (
            <div className="mt-4 space-y-5">
              {filteredAccounts.map((account) => {
                const accountIndex = accountsForm.indexOf(account);
                if (accountIndex < 0) {
                  return null;
                }
                const displayIndex = accountIndex + 1;
                const dexOptions = Array.from(
                  new Set([...ACCOUNT_TYPES, account.dex_type].filter((value) => !!value)),
                );
                return (
                  <div
                    key={`${account.id}-${accountIndex}`}
                    className="space-y-4 rounded-lg border p-4"
                    style={{ borderColor: "var(--panel-border)", background: "var(--panel-bg)" }}
                  >
                    <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                      <div>
                        <h3 className="text-xs font-semibold uppercase tracking-wider">
                          {language === "zh" ? `账户 #${displayIndex}` : `Account #${displayIndex}`}
                        </h3>
                        <p className="text-[10px]" style={{ color: "var(--muted-text)" }}>
                          {language === "zh" ? "当前 ID：" : "Current ID:"} {account.id}
                        </p>
                      </div>
                      <button
                        onClick={() => onRemoveAccount(accountIndex)}
                        disabled={accountsForm.length <= 1}
                        className="rounded border px-2 py-1 text-[10px] uppercase tracking-widest transition hover:opacity-80 disabled:opacity-40"
                        style={{ borderColor: "var(--panel-border)" }}
                      >
                        {language === "zh" ? "删除" : "Remove"}
                      </button>
                    </div>

                    <div className="grid gap-4 md:grid-cols-3">
                      <div className="space-y-1">
                        <label className="text-[11px] font-semibold uppercase tracking-wider">
                          {language === "zh" ? "账户 ID" : "Account ID"}
                        </label>
                        <input
                          type="text"
                          value={account.id}
                          onChange={(e) => {
                            const prevId = account.id;
                            const nextId = e.target.value;
                            updateAccountAt(accountIndex, (draft) => {
                              draft.id = nextId;
                              return draft;
                            });
                            onAccountIdChange(prevId, nextId);
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
                          value={account.name}
                          onChange={(e) =>
                            updateAccountAt(accountIndex, (draft) => {
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
                          {language === "zh" ? "DEX 类型" : "DEX Type"}
                        </label>
                        <select
                          value={account.dex_type}
                          onChange={(e) =>
                            updateAccountAt(accountIndex, (draft) => {
                              draft.dex_type = e.target.value;
                              return draft;
                            })
                          }
                          className="w-full rounded border bg-transparent px-3 py-2 text-xs outline-none focus:ring-1 capitalize"
                          style={{ borderColor: "var(--panel-border)" }}
                        >
                          {dexOptions.map((option) => (
                            <option key={option} value={option}>
                              {option}
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>

                    <div className="flex flex-wrap gap-4">
                      <label
                        className="flex items-center gap-2 text-[10px] uppercase tracking-widest"
                        style={{ color: "var(--muted-text)" }}
                      >
                        <input
                          type="checkbox"
                          className="h-4 w-4"
                          checked={account.testnet}
                          onChange={(e) =>
                            updateAccountAt(accountIndex, (draft) => {
                              draft.testnet = e.target.checked;
                              return draft;
                            })
                          }
                        />
                        {language === "zh" ? "测试网" : "Testnet"}
                      </label>
                      <label
                        className="flex items-center gap-2 text-[10px] uppercase tracking-widest"
                        style={{ color: "var(--muted-text)" }}
                      >
                        <input
                          type="checkbox"
                          className="h-4 w-4"
                          checked={account.hedge_mode}
                          onChange={(e) =>
                            updateAccountAt(accountIndex, (draft) => {
                              draft.hedge_mode = e.target.checked;
                              return draft;
                            })
                          }
                        />
                        {language === "zh" ? "对冲模式" : "Hedge Mode"}
                      </label>
                    </div>

                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-[11px] font-semibold uppercase tracking-wider">
                          {language === "zh" ? "额外字段" : "Extra Fields"}
                        </span>
                        <button
                          onClick={() => onAddAccountField(accountIndex)}
                          className="rounded border px-2 py-1 text-[10px] uppercase tracking-widest transition hover:opacity-80"
                          style={{ borderColor: "var(--panel-border)" }}
                        >
                          {language === "zh" ? "新增字段" : "Add Field"}
                        </button>
                      </div>

                      {account.extraFields.length === 0 ? (
                        <p className="text-[10px]" style={{ color: "var(--muted-text)" }}>
                          {language === "zh"
                            ? "暂无额外字段，可用于填写 API 凭证等敏感信息。"
                            : "No extra fields yet. Use this section for API credentials or additional metadata."}
                        </p>
                      ) : (
                        <div className="space-y-2">
                          {account.extraFields.map((field, fieldIndex) => {
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
                                      updateAccountAt(accountIndex, (draft) => {
                                        const fields = [...draft.extraFields];
                                        if (!fields[fieldIndex].locked) {
                                          fields[fieldIndex] = {
                                            ...fields[fieldIndex],
                                            key: e.target.value,
                                          };
                                        }
                                        draft.extraFields = sortByKey(fields);
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
                                      const fieldId = makeSecretId(account.id, field.key, fieldIndex);
                                      const isVisible = visibleSecrets[fieldId];
                                      const shouldMask = isSensitiveKey(field.key) && !(isEnvPlaceholder && field.displayValue === field.rawValue);
                                      return (
                                        <>
                                          <input
                                            type={shouldMask && !isVisible ? "password" : "text"}
                                            value={field.displayValue}
                                            onChange={(e) =>
                                              updateAccountAt(accountIndex, (draft) => {
                                                const fields = [...draft.extraFields];
                                                fields[fieldIndex] = {
                                                  ...fields[fieldIndex],
                                                  rawValue: e.target.value,
                                                  displayValue: e.target.value,
                                                  locked: fields[fieldIndex].locked,
                                                };
                                                draft.extraFields = sortByKey(fields);
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
                                    onClick={() => onRemoveAccountField(accountIndex, fieldIndex)}
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

