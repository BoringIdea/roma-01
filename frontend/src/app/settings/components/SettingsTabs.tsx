"use client";

import type { SettingsTab } from "@/app/settings/types";

interface TabItem {
  id: SettingsTab;
  label: string;
}

interface SettingsTabsProps {
  activeTab: SettingsTab;
  tabs: TabItem[];
  onChange: (tab: SettingsTab) => void;
}

export function SettingsTabs({ activeTab, tabs, onChange }: SettingsTabsProps) {
  return (
    <nav
      className="flex flex-wrap gap-2 rounded-xl border p-2 text-[11px] uppercase tracking-[0.25em]"
      style={{ borderColor: "var(--panel-border)", background: "var(--panel-bg)" }}
    >
      {tabs.map((tab) => {
        const isActive = activeTab === tab.id;
        return (
          <button
            key={tab.id}
            onClick={() => onChange(tab.id)}
            className="rounded px-3 py-1.5 transition"
            style={{
              background: isActive ? "var(--brand-accent)" : "transparent",
              color: isActive ? "#ffffff" : "var(--foreground)",
              border: isActive ? "1px solid var(--brand-accent)" : "1px solid var(--panel-border)",
            }}
          >
            {tab.label}
          </button>
        );
      })}
    </nav>
  );
}

