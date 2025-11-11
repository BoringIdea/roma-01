"use client";

import { useState } from "react";

import { useLanguage } from "@/store/useLanguage";

interface SettingsLoginModalProps {
  onSubmit: (username: string, password: string) => void;
  loading: boolean;
  error: string | null;
}

export function SettingsLoginModal({ onSubmit, loading, error }: SettingsLoginModalProps) {
  const language = useLanguage((s) => s.language);
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("");

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    if (!username || !password || loading) return;
    onSubmit(username.trim(), password);
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center px-4 backdrop-blur">
      <div
        className="w-full max-w-md rounded-xl border p-6 shadow-lg"
        style={{
          background: "var(--panel-bg)",
          borderColor: "var(--panel-border)",
        }}
      >
        <h2 className="text-sm font-semibold uppercase tracking-widest" style={{ color: "var(--foreground)" }}>
          {language === "zh" ? "管理员登录" : "Administrator Sign-in"}
        </h2>
        <p className="mt-1 text-[11px]" style={{ color: "var(--muted-text)" }}>
          {language === "zh"
            ? "请输入配置中心管理员账号和密码以继续。"
            : "Enter administrator credentials to access configuration settings."}
        </p>

        <form onSubmit={handleSubmit} className="mt-4 space-y-3 text-xs">
          <div className="space-y-1">
            <label className="block font-semibold uppercase tracking-wider" style={{ color: "var(--foreground)" }}>
              {language === "zh" ? "用户名" : "Username"}
            </label>
            <input
              type="text"
              value={username}
              autoComplete="username"
              onChange={(e) => setUsername(e.target.value)}
              className="w-full rounded border bg-transparent px-3 py-2 outline-none transition focus:ring-1"
              style={{
                borderColor: "var(--panel-border)",
                color: "var(--foreground)",
                boxShadow: "var(--input-shadow)",
              }}
              disabled={loading}
              required
            />
          </div>

          <div className="space-y-1">
            <label className="block font-semibold uppercase tracking-wider" style={{ color: "var(--foreground)" }}>
              {language === "zh" ? "密码" : "Password"}
            </label>
            <input
              type="password"
              value={password}
              autoComplete="current-password"
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded border bg-transparent px-3 py-2 outline-none transition focus:ring-1"
              style={{
                borderColor: "var(--panel-border)",
                color: "var(--foreground)",
                boxShadow: "var(--input-shadow)",
              }}
              disabled={loading}
              required
            />
          </div>

          {error && (
            <div className="rounded border px-3 py-2 text-[10px]" style={{ borderColor: "#ef4444", color: "#ef4444" }}>
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded py-2 text-xs font-semibold uppercase tracking-widest transition"
            style={{
              background: "var(--brand-accent)",
              color: "#ffffff",
              opacity: loading ? 0.7 : 1,
            }}
          >
            {loading
              ? language === "zh"
                ? "登录中..."
                : "Signing In..."
              : language === "zh"
                ? "登录"
                : "Sign In"}
          </button>
        </form>
      </div>
    </div>
  );
}

