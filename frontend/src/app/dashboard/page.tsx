"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import DashboardHeader from "./components/DashboardHeader";
import HyperliquidLeaderboard from "./components/HyperliquidLeaderboard";
import LargeTradeMonitor from "./components/LargeTradeMonitor";
import TokenRankings from "./components/TokenRankings";

type DexFilter = "all" | "aster" | "hyperliquid";

import DashboardTabs, { DashboardTab } from "./components/DashboardTabs";

function DashboardContent() {
  const searchParams = useSearchParams();
  const [dexFilter, setDexFilter] = useState<DexFilter>("all");
  const [activeTab, setActiveTab] = useState<DashboardTab>("leaderboard");

  useEffect(() => {
    const dex = searchParams.get("dex");
    if (dex === "aster" || dex === "hyperliquid") {
      setDexFilter(dex);
    } else {
      setDexFilter("all");
    }
  }, [searchParams]);

  return (
    <div className="container mx-auto p-6">
      <DashboardHeader dexFilter={dexFilter} />

      <div className="mt-6">
        <DashboardTabs activeTab={activeTab} onChange={setActiveTab} />

        {activeTab === "leaderboard" && (
          <HyperliquidLeaderboard dexFilter={dexFilter} />
        )}

        {activeTab === "large-trades" && (
          <LargeTradeMonitor dexFilter={dexFilter} />
        )}

        {activeTab === "token-rankings" && (
          <TokenRankings dexFilter={dexFilter} />
        )}
      </div>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <Suspense fallback={
      <div className="container mx-auto p-6">
        <div className="text-center py-8">Loading...</div>
      </div>
    }>
      <DashboardContent />
    </Suspense>
  );
}

