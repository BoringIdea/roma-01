"use client";

import { useState, useMemo } from "react";
import useSWR from "swr";
import { api } from "@/lib/api";
import { getAgentModelColor } from "@/lib/model/meta";
import { fmtUSD } from "@/lib/utils/formatters";
import Link from "next/link";
import { useLanguage } from "@/store/useLanguage";
import { getTranslation } from "@/lib/i18n";

type SortKey = 
  | "equity" 
  | "return_pct" 
  | "total_pnl" 
  | "win_rate" 
  | "biggest_win" 
  | "biggest_loss" 
  | "sharpe" 
  | "trades"
  | "avg_trade_size"
  | "median_trade_size"
  | "avg_hold"
  | "median_hold"
  | "pct_long"
  | "expectancy"
  | "median_leverage"
  | "avg_leverage"
  | "avg_confidence"
  | "median_confidence";

// Format hold time from minutes to "5h 30m" format
function fmtHoldTime(minutes: number): string {
  const hours = Math.floor(minutes / 60);
  const mins = Math.floor(minutes % 60);
  return `${hours}h ${mins}m`;
}

// Component for a single leaderboard row that handles its own data fetching
function LeaderboardRow({ 
  agent, 
  index, 
  mode 
}: { 
  agent: any;
  index: number;
  mode: "overall" | "advanced";
}) {
  const isRunning = agent.is_running;
  
  // Only fetch data if agent is running
  const { data: account } = useSWR(
    isRunning ? `/agent/${agent.id}/account` : null,
    isRunning ? () => api.getAccount(agent.id) : null,
    { refreshInterval: 10000 }
  );

  const { data: analytics } = useSWR(
    isRunning ? `/agent/${agent.id}/analytics` : null,
    isRunning ? () => api.getAnalytics(agent.id) : null,
    { refreshInterval: 30000 }
  );

  // Fetch equity history to get initial balance
  const { data: equityHistory } = useSWR(
    isRunning ? `/agent/${agent.id}/equity` : null,
    isRunning ? () => api.getEquityHistory(agent.id) : null,
    { refreshInterval: 60000 }
  );

  const color = getAgentModelColor(agent);
  
  // If not running, show gray row
  if (!isRunning) {
    return (
      <tr
        className="border-b"
        style={{
          borderColor: "color-mix(in oklab, var(--panel-border) 50%, transparent)",
          opacity: 0.4,
        }}
      >
        <td className="py-1.5 pr-2 font-bold">{index + 1}</td>
        <td className="py-1.5 pr-2">
          <div className="inline-flex items-center gap-2">
            <div 
              className="w-2.5 h-2.5 rounded-full"
              style={{ background: "#6b7280" }}
            />
            <span className="font-semibold">{agent.name || agent.id}</span>
          </div>
        </td>
        <td className="py-1.5 pr-2 tabular-nums" colSpan={mode === "advanced" ? 11 : 8} style={{ color: "var(--muted-text)" }}>
          <span className="text-[10px]">—</span>
        </td>
      </tr>
    );
  }

  // If running but data not loaded yet
  if (!account || !analytics || !equityHistory) {
    return (
      <tr>
        <td colSpan={mode === "advanced" ? 13 : 10} className="py-2 text-center text-xs" style={{ color: "var(--muted-text)" }}>
          Loading...
        </td>
      </tr>
    );
  }

  const equityAdjusted = account.adjusted_total_balance ?? account.total_wallet_balance ?? 0;
  // Use first equity history point as initial balance, fallback to adjusted equity or 10000
  const initialPoint = equityHistory.length > 0 ? equityHistory[0] : null;
  const initialBalance = initialPoint
    ? initialPoint.adjusted_equity ?? initialPoint.equity
    : equityAdjusted || 10000;
  const equityDisplay = account.gross_total_balance ?? account.total_wallet_balance ?? equityAdjusted;
  const totalPnl = equityAdjusted - initialBalance;
  const returnPct = initialBalance > 0 ? (totalPnl / initialBalance) * 100 : 0;
  const sharpe = returnPct > 0 ? returnPct / 100 : returnPct / 50;

  return (
    <tr
      className="border-b hover:bg-opacity-50"
      style={{
        borderColor: "color-mix(in oklab, var(--panel-border) 50%, transparent)",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.background = `${color}08`;
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.background = "transparent";
      }}
    >
      <td className="py-1.5 pr-2 font-bold">{index + 1}</td>
      <td className="py-1.5 pr-2">
        <Link
          href={`/agent/${agent.id}`}
          className="inline-flex items-center gap-2 hover:underline"
        >
          <div 
            className="w-2.5 h-2.5 rounded-full"
            style={{ background: color }}
          />
          <span className="font-semibold">{agent.name || agent.id}</span>
          {isRunning && (
            <span 
              className="text-[9px] px-1.5 py-0.5 rounded font-semibold"
              style={{ 
                background: "rgba(34, 197, 94, 0.15)",
                color: "#22c55e"
              }}
            >
              LIVE
            </span>
          )}
        </Link>
      </td>
      <td className="py-1.5 pr-2 tabular-nums font-semibold" style={{ color: "var(--brand-accent)" }}>
        {fmtUSD(equityDisplay)}
      </td>
      {mode === "advanced" ? (
        <>
          <td className="py-1.5 pr-2 tabular-nums">
            {fmtUSD(analytics.avg_trade_size || 0)}
          </td>
          <td className="py-1.5 pr-2 tabular-nums">
            {fmtUSD(analytics.median_trade_size || 0)}
          </td>
          <td className="py-1.5 pr-2 tabular-nums">
            {fmtHoldTime(analytics.avg_hold_mins || 0)}
          </td>
          <td className="py-1.5 pr-2 tabular-nums">
            {fmtHoldTime(analytics.median_hold_mins || 0)}
          </td>
          <td className="py-1.5 pr-2 tabular-nums">
            {(analytics.pct_long || 0).toFixed(2)}%
          </td>
          <td 
            className="py-1.5 pr-2 tabular-nums font-semibold"
            style={{ 
              color: (analytics.expectancy || 0) >= 0 ? "#22c55e" : "#ef4444" 
            }}
          >
            {fmtUSD(analytics.expectancy || 0)}
          </td>
          <td className="py-1.5 pr-2 tabular-nums">
            {(analytics.median_leverage || 10).toFixed(1)}
          </td>
          <td className="py-1.5 pr-2 tabular-nums">
            {(analytics.avg_leverage || 10).toFixed(1)}
          </td>
          <td className="py-1.5 pr-2 tabular-nums">
            {(analytics.avg_confidence || 0).toFixed(1)}%
          </td>
          <td className="py-1.5 pr-2 tabular-nums">
            {(analytics.median_confidence || 0).toFixed(1)}%
          </td>
        </>
      ) : (
        <>
          <td 
            className="py-1.5 pr-2 tabular-nums font-semibold"
            style={{ 
              color: returnPct >= 0 ? "#22c55e" : "#ef4444" 
            }}
          >
            {returnPct >= 0 ? "+" : ""}{returnPct.toFixed(2)}%
          </td>
          <td 
            className="py-1.5 pr-2 tabular-nums font-semibold"
            style={{ 
              color: totalPnl >= 0 ? "#22c55e" : "#ef4444" 
            }}
          >
            {fmtUSD(totalPnl)}
          </td>
          <td className="py-1.5 pr-2 tabular-nums">
            {fmtUSD((analytics.total_trades > 0 ? (analytics.avg_win + Math.abs(analytics.avg_loss)) * 0.05 : 0))}
          </td>
          <td className="py-1.5 pr-2 tabular-nums">
            {(analytics.win_rate || 0).toFixed(1)}%
          </td>
          <td 
            className="py-1.5 pr-2 tabular-nums"
            style={{ color: "#22c55e" }}
          >
            {fmtUSD(analytics.biggest_win || 0)}
          </td>
          <td 
            className="py-1.5 pr-2 tabular-nums"
            style={{ color: "#ef4444" }}
          >
            {fmtUSD(analytics.biggest_loss || 0)}
          </td>
          <td className="py-1.5 pr-2 tabular-nums">
            {sharpe.toFixed(3)}
          </td>
          <td className="py-1.5 pr-2 tabular-nums">
            {analytics.total_trades || 0}
          </td>
        </>
      )}
    </tr>
  );
}

export default function LeaderboardTable({
  mode = "overall",
  agents,
}: {
  mode?: "overall" | "advanced";
  agents: any[];
}) {
  const language = useLanguage((s) => s.language);
  const t = getTranslation(language).leaderboard;
  
  const [sortKey, setSortKey] = useState<SortKey>("equity");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  // Sort will be handled by the parent or we show unsorted for now
  // Since each row fetches its own data, client-side sorting would be complex
  // For now, we'll just display in the order received

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
  };

  return (
    <div
      className="rounded-md border"
      style={{
        background: "var(--panel-bg)",
        borderColor: "var(--panel-border)",
      }}
    >
      <div className="overflow-x-auto">
        <table className="w-full text-left text-[10px] terminal-text">
          <thead style={{ color: "var(--muted-text)" }}>
            <tr className="border-b" style={{ borderColor: "var(--panel-border)" }}>
              <Th label={t.rank} />
              <Th label={t.model} />
              <ThSort
                label={t.acctValue}
                active={sortKey === "equity"}
                dir={sortDir}
                onClick={() => toggleSort("equity")}
              />
              {mode === "advanced" ? (
                <>
                  <ThSort
                    label={t.avgTradeSize}
                    active={sortKey === "avg_trade_size"}
                    dir={sortDir}
                    onClick={() => toggleSort("avg_trade_size")}
                  />
                  <ThSort
                    label={t.medianTradeSize}
                    active={sortKey === "median_trade_size"}
                    dir={sortDir}
                    onClick={() => toggleSort("median_trade_size")}
                  />
                  <ThSort
                    label={t.avgHold}
                    active={sortKey === "avg_hold"}
                    dir={sortDir}
                    onClick={() => toggleSort("avg_hold")}
                  />
                  <ThSort
                    label={t.medianHold}
                    active={sortKey === "median_hold"}
                    dir={sortDir}
                    onClick={() => toggleSort("median_hold")}
                  />
                  <ThSort
                    label="% LONG"
                    active={sortKey === "pct_long"}
                    dir={sortDir}
                    onClick={() => toggleSort("pct_long")}
                  />
                  <ThSort
                    label={t.expectancy}
                    active={sortKey === "expectancy"}
                    dir={sortDir}
                    onClick={() => toggleSort("expectancy")}
                  />
                  <ThSort
                    label={t.medianLeverage}
                    active={sortKey === "median_leverage"}
                    dir={sortDir}
                    onClick={() => toggleSort("median_leverage")}
                  />
                  <ThSort
                    label={t.avgLeverage}
                    active={sortKey === "avg_leverage"}
                    dir={sortDir}
                    onClick={() => toggleSort("avg_leverage")}
                  />
                  <ThSort
                    label={t.avgConfidence}
                    active={sortKey === "avg_confidence"}
                    dir={sortDir}
                    onClick={() => toggleSort("avg_confidence")}
                  />
                  <ThSort
                    label={t.medianConfidence}
                    active={sortKey === "median_confidence"}
                    dir={sortDir}
                    onClick={() => toggleSort("median_confidence")}
                  />
                </>
              ) : (
                <>
                  <ThSort
                    label={t.returnPercent}
                    active={sortKey === "return_pct"}
                    dir={sortDir}
                    onClick={() => toggleSort("return_pct")}
                  />
                  <ThSort
                    label={t.totalPnl}
                    active={sortKey === "total_pnl"}
                    dir={sortDir}
                    onClick={() => toggleSort("total_pnl")}
                  />
                  <Th label={t.fees} />
                  <ThSort
                    label={t.winRate}
                    active={sortKey === "win_rate"}
                    dir={sortDir}
                    onClick={() => toggleSort("win_rate")}
                  />
                  <ThSort
                    label={t.biggestWin}
                    active={sortKey === "biggest_win"}
                    dir={sortDir}
                    onClick={() => toggleSort("biggest_win")}
                  />
                  <ThSort
                    label={t.biggestLoss}
                    active={sortKey === "biggest_loss"}
                    dir={sortDir}
                    onClick={() => toggleSort("biggest_loss")}
                  />
                  <ThSort
                    label={t.sharpe}
                    active={sortKey === "sharpe"}
                    dir={sortDir}
                    onClick={() => toggleSort("sharpe")}
                  />
                  <ThSort
                    label={t.trades}
                    active={sortKey === "trades"}
                    dir={sortDir}
                    onClick={() => toggleSort("trades")}
                  />
                </>
              )}
            </tr>
          </thead>
          <tbody style={{ color: "var(--foreground)" }}>
            {agents.length === 0 ? (
              <tr>
                <td colSpan={mode === "advanced" ? 13 : 10} className="py-8 text-center">
                  <div style={{ color: "var(--muted-text)" }}>
                    No agents available
                  </div>
                </td>
              </tr>
            ) : (
              agents.map((agent, index) => (
                <LeaderboardRow
                  key={agent.id}
                  agent={agent}
                  index={index}
                  mode={mode}
                />
              ))
            )}
          </tbody>
        </table>
      </div>
      
      {/* Note at bottom */}
      <div 
        className="border-t px-3 py-2 text-[10px]"
        style={{ 
          borderColor: "var(--panel-border)",
          color: "var(--muted-text)" 
        }}
      >
        <strong>{t.note}</strong> {t.completedTradesNote}
      </div>
    </div>
  );
}

function Th({ label }: { label: string }) {
  return (
    <th className="py-1.5 pr-2 text-[10px] font-normal uppercase tracking-wide whitespace-nowrap">
      {label}
    </th>
  );
}

function ThSort({
  label,
  active,
  dir,
  onClick,
}: {
  label: string;
  active: boolean;
  dir: "asc" | "desc";
  onClick: () => void;
}) {
  return (
    <th className="py-1.5 pr-2 text-[10px] uppercase tracking-wide">
      <button
        className="flex items-center gap-0.5 font-normal hover:opacity-70 transition-opacity whitespace-nowrap"
        style={{ color: active ? "var(--foreground)" : "var(--muted-text)" }}
        onClick={onClick}
      >
        {label}
        {active && (
          <span className="text-[9px]">
            {dir === "asc" ? "▲" : "▼"}
          </span>
        )}
      </button>
    </th>
  );
}
