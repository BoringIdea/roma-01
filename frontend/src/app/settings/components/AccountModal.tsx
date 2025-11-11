"use client";

import type { AccountDraft } from "@/app/settings/types";
import { ACCOUNT_TYPES, ACCOUNT_TYPE_REQUIRED_FIELDS } from "@/app/settings/constants";

interface AccountModalProps {
  language: string;
  visible: boolean;
  accountDraft: AccountDraft;
  error: string | null;
  onDraftChange: (field: keyof AccountDraft, value: string | boolean) => void;
  onClose: () => void;
  onSubmit: () => void;
}

export function AccountModal({
  language,
  visible,
  accountDraft,
  error,
  onDraftChange,
  onClose,
  onSubmit,
}: AccountModalProps) {
  if (!visible) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center px-4 backdrop-blur">
      <div
        className="w-full max-w-lg rounded-xl border bg-[color:var(--panel-bg)] p-6 shadow-lg"
        style={{ borderColor: "var(--panel-border)" }}
      >
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-sm font-semibold uppercase tracking-widest" style={{ color: "var(--foreground)" }}>
              {language === "zh" ? "新增账户" : "Create Account"}
            </h2>
            <p className="mt-1 text-[11px]" style={{ color: "var(--muted-text)" }}>
              {language === "zh"
                ? "填写账户标识、显示名称与交易所类型，可同时配置测试网和对冲模式。"
                : "Provide the account identifier, display name, and DEX type. You can also toggle testnet and hedge modes."}
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

        <div className="mt-4 space-y-3">
          <div className="space-y-1">
            <label className="text-[11px] font-semibold uppercase tracking-wider">
              {language === "zh" ? "账户 ID" : "Account ID"}
            </label>
            <input
              type="text"
              value={accountDraft.id}
              onChange={(e) => onDraftChange("id", e.target.value)}
              className="w-full rounded border bg-transparent px-3 py-2 text-xs outline-none focus:ring-1"
              style={{ borderColor: "var(--panel-border)" }}
              placeholder="account-01"
            />
          </div>

          <div className="space-y-1">
            <label className="text-[11px] font-semibold uppercase tracking-wider">
              {language === "zh" ? "显示名称" : "Display Name"}
            </label>
            <input
              type="text"
              value={accountDraft.name}
              onChange={(e) => onDraftChange("name", e.target.value)}
              className="w-full rounded border bg-transparent px-3 py-2 text-xs outline-none focus:ring-1"
              style={{ borderColor: "var(--panel-border)" }}
              placeholder={language === "zh" ? "例如 Hyperliquid 主账户" : "e.g. Primary Account"}
            />
          </div>

          <div className="space-y-1">
            <label className="text-[11px] font-semibold uppercase tracking-wider">
              {language === "zh" ? "DEX 类型" : "DEX Type"}
            </label>
            <select
              value={accountDraft.dex_type}
              onChange={(e) => onDraftChange("dex_type", e.target.value)}
              className="w-full rounded border bg-transparent px-3 py-2 text-xs outline-none focus:ring-1 capitalize"
              style={{ borderColor: "var(--panel-border)" }}
            >
              {ACCOUNT_TYPES.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
          </div>

          <div className="flex flex-wrap gap-4">
            <label
              className="flex items-center gap-2 text-[10px] uppercase tracking-widest"
              style={{ color: "var(--muted-text)" }}
            >
              <input
                type="checkbox"
                className="h-4 w-4"
                checked={accountDraft.testnet}
                onChange={(e) => onDraftChange("testnet", e.target.checked)}
              />
              {language === "zh" ? "启用测试网" : "Use Testnet"}
            </label>
            <label
              className="flex items-center gap-2 text-[10px] uppercase tracking-widest"
              style={{ color: "var(--muted-text)" }}
            >
              <input
                type="checkbox"
                className="h-4 w-4"
                checked={accountDraft.hedge_mode}
                onChange={(e) => onDraftChange("hedge_mode", e.target.checked)}
              />
              {language === "zh" ? "启用对冲" : "Enable Hedge Mode"}
            </label>
          </div>

          <div className="space-y-3">
            {ACCOUNT_TYPE_REQUIRED_FIELDS[accountDraft.dex_type as (typeof ACCOUNT_TYPES)[number]]?.map(
              (field) => (
                <div key={field.key} className="space-y-1">
                  <label className="text-[11px] font-semibold uppercase tracking-wider">
                    {language === "zh" ? field.labelZh : field.labelEn}
                  </label>
                  <input
                    type="text"
                    value={(accountDraft[field.key as keyof AccountDraft] as string) ?? ""}
                    onChange={(e) => onDraftChange(field.key as keyof AccountDraft, e.target.value)}
                    className="w-full rounded border bg-transparent px-3 py-2 text-xs outline-none focus:ring-1"
                    style={{ borderColor: "var(--panel-border)" }}
                    placeholder={language === "zh" ? field.placeholderZh ?? "" : field.placeholderEn ?? ""}
                  />
                </div>
              ),
            )}
            <p className="text-[10px]" style={{ color: "var(--muted-text)" }}>
              {language === "zh"
                ? "支持直接输入环境变量占位符（例如 \${VAR_NAME}），保存后会写入配置文件。"
                : "You can paste environment variable placeholders (e.g. \${VAR_NAME}); they will be saved to the config file."}
            </p>
          </div>
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
            className="rounded px-4 py-2 text-[11px] font-semibold uppercase tracking-widest transition"
            style={{ background: "var(--brand-accent)", color: "#ffffff" }}
          >
            {language === "zh" ? "确认添加" : "Add Account"}
          </button>
        </div>
      </div>
    </div>
  );
}

