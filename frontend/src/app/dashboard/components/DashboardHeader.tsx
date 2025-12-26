"use client";

import { useLanguage } from "@/store/useLanguage";

interface DashboardHeaderProps {
  dexFilter: "all" | "aster" | "hyperliquid";
}

export default function DashboardHeader({
  dexFilter,
}: DashboardHeaderProps) {
  const language = useLanguage((s) => s.language);

  const getDexLabel = () => {
    if (dexFilter === "aster") return "Aster";
    if (dexFilter === "hyperliquid") return "Hyperliquid";
    return language === "zh" ? "全部" : "All";
  };

  return (
    <div
      className="border-b pb-8 mb-8"
      style={{
        borderColor: "var(--panel-border)",
      }}
    >
      <div>
        <h1 className="text-4xl font-black uppercase tracking-tighter italic">
          {language === "zh" ? "交易看板" : "Trading Dashboard"}
          {dexFilter !== "all" && (
            <span className="ml-4 text-lg font-normal opacity-50 not-italic">
              [{getDexLabel()}]
            </span>
          )}
        </h1>
        <p className="text-sm" style={{ color: "var(--muted-text)" }}>
          {language === "zh"
            ? "实时监控大额交易和市场数据排行"
            : "Real-time large trade monitoring and market data rankings"}
        </p>
      </div>
    </div>
  );
}

