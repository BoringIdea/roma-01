"use client";

import type { AdminFormState } from "@/app/settings/types";

interface AdminSectionProps {
  language: string;
  adminForm: AdminFormState;
  onAdminChange: (updater: (prev: AdminFormState) => AdminFormState) => void;
}

export function AdminSection({ language, adminForm, onAdminChange }: AdminSectionProps) {
  return (
    <section
      className="rounded-xl border p-5"
      style={{ borderColor: "var(--panel-border)", background: "var(--panel-bg)" }}
    >
      <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider">
        {language === "zh" ? "管理员账号" : "Administrator"}
      </h2>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-1">
          <label className="text-[11px] font-semibold uppercase tracking-wider">
            {language === "zh" ? "用户名" : "Username"}
          </label>
          <input
            type="text"
            value={adminForm.username}
            onChange={(e) =>
              onAdminChange((prev) => ({
                ...prev,
                username: e.target.value,
              }))
            }
            className="w-full rounded border bg-transparent px-3 py-2 text-xs outline-none focus:ring-1"
            style={{ borderColor: "var(--panel-border)" }}
          />
        </div>

        <div className="space-y-1">
          <label className="text-[11px] font-semibold uppercase tracking-wider">
            {language === "zh" ? "新密码（留空保持不变）" : "New Password (leave blank to keep)"}
          </label>
          <input
            type="password"
            value={adminForm.password}
            onChange={(e) =>
              onAdminChange((prev) => ({
                ...prev,
                password: e.target.value,
              }))
            }
            className="w-full rounded border bg-transparent px-3 py-2 text-xs outline-none focus:ring-1"
            style={{ borderColor: "var(--panel-border)" }}
            placeholder={language === "zh" ? "可选" : "Optional"}
          />
        </div>

        <div className="space-y-1">
          <label className="text-[11px] font-semibold uppercase tracking-wider">
            {language === "zh" ? "确认新密码" : "Confirm Password"}
          </label>
          <input
            type="password"
            value={adminForm.confirmPassword}
            onChange={(e) =>
              onAdminChange((prev) => ({
                ...prev,
                confirmPassword: e.target.value,
              }))
            }
            className="w-full rounded border bg-transparent px-3 py-2 text-xs outline-none focus:ring-1"
            style={{ borderColor: "var(--panel-border)" }}
            placeholder={language === "zh" ? "可选" : "Optional"}
          />
        </div>
      </div>

      <p className="mt-2 text-[10px]" style={{ color: "var(--muted-text)" }}>
        {language === "zh"
          ? "更改管理员信息后将立即生效，并记录更新时间。"
          : "Administrator changes take effect immediately and update the stored timestamp."}
      </p>
    </section>
  );
}

