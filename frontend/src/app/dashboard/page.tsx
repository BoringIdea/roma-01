"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import DashboardHeader from "./components/DashboardHeader";
import HyperliquidLeaderboard from "./components/HyperliquidLeaderboard";
import LargeTradeMonitor from "./components/LargeTradeMonitor";
import TokenRankings from "./components/TokenRankings";

type DexFilter = "all" | "aster" | "hyperliquid";

function DashboardContent() {
  const searchParams = useSearchParams();
  const [dexFilter, setDexFilter] = useState<DexFilter>("all");

  useEffect(() => {
    const dex = searchParams.get("dex");
    if (dex === "aster" || dex === "hyperliquid") {
      setDexFilter(dex);
    } else {
      setDexFilter("all");
    }
  }, [searchParams]);

  return (
    <div className="container mx-auto p-6 space-y-6">
      <DashboardHeader dexFilter={dexFilter} />

      <HyperliquidLeaderboard dexFilter={dexFilter} />

      <div className="flex flex-col gap-6">
        <LargeTradeMonitor dexFilter={dexFilter} />
        <TokenRankings dexFilter={dexFilter} />
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

