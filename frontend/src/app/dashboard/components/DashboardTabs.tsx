"use client";

import { useLanguage } from "@/store/useLanguage";

export type DashboardTab = "leaderboard" | "large-trades" | "token-rankings";

interface TabItem {
  id: DashboardTab;
  labelZh: string;
  labelEn: string;
}

const DASHBOARD_TABS: TabItem[] = [
  { id: "leaderboard", labelZh: "交易者排行榜", labelEn: "Trader Leaderboard" },
  { id: "large-trades", labelZh: "大额交易监控", labelEn: "Large Trade Monitor" },
  { id: "token-rankings", labelZh: "代币数据排行", labelEn: "Token Rankings" },
];

interface DashboardTabsProps {
  activeTab: DashboardTab;
  onChange: (tab: DashboardTab) => void;
}

export default function DashboardTabs({ activeTab, onChange }: DashboardTabsProps) {
  const language = useLanguage((s) => s.language);

  return (
    <nav
      className="flex flex-wrap text-[11px] font-black uppercase tracking-[0.1em] mb-8"
      style={{ background: "var(--panel-bg)" }}
    >
      {DASHBOARD_TABS.map((tab) => {
        const isActive = activeTab === tab.id;
        return (
          <button
            key={tab.id}
            onClick={() => onChange(tab.id)}
            className="px-6 py-3 transition-colors border -ml-[1px] first:ml-0"
            style={{
              background: isActive ? "var(--foreground)" : "transparent",
              color: isActive ? "var(--background)" : "var(--foreground)",
              borderColor: "var(--panel-border)",
            }}
          >
            {language === "zh" ? tab.labelZh : tab.labelEn}
          </button>
        );
      })}
    </nav>
  );
}

