"use client";

import { useState, useMemo, useEffect } from "react";
import useSWR from "swr";
import { api } from "@/lib/api";
import { useLanguage } from "@/store/useLanguage";

const WINDOW_OPTIONS = [
  { value: "day", label: "1D" },
  { value: "week", label: "7D" },
  { value: "month", label: "30D" },
  { value: "allTime", label: "All" },
] as const;

interface LeaderboardRow {
  rank: number;
  address: string;
  display_name?: string | null;
  account_value: number;
  pnl: number;
  roi: number;
  volume: number;
  window: "day" | "week" | "month" | "allTime";
  dex?: "aster" | "hyperliquid";
}

interface HyperliquidLeaderboardProps {
  pageSize?: number;
  dexFilter?: "all" | "aster" | "hyperliquid";
}

type SortField = "pnl" | "roi" | "volume";
type SortOrder = "asc" | "desc";

const FETCH_LIMIT = 100;

export default function HyperliquidLeaderboard({
  pageSize = 10,
  dexFilter = "all"
}: HyperliquidLeaderboardProps) {
  const language = useLanguage((s) => s.language);
  const [window, setWindow] = useState<"day" | "week" | "month" | "allTime">("month");
  const [page, setPage] = useState(0);
  const [sortField, setSortField] = useState<SortField | null>(null);
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc");

  const dexParam = dexFilter === "all" ? undefined : dexFilter;

  const { data, isLoading } = useSWR(
    `/dashboard/leaderboard?window=${window}&limit=${FETCH_LIMIT}&offset=0&dex=${dexParam || ""}`,
    () => api.getHyperliquidLeaderboard(window, FETCH_LIMIT, 0, dexParam),
    { refreshInterval: 60_000 }
  );

  const allRows = data?.data ?? [];
  const total = data?.total ?? 0;

  // Sort data
  const sortedRows = useMemo(() => {
    if (!sortField || allRows.length === 0) return allRows;

    const sorted = [...allRows].sort((a, b) => {
      let aValue: number = 0;
      let bValue: number = 0;

      switch (sortField) {
        case "pnl":
          aValue = a.pnl;
          bValue = b.pnl;
          break;
        case "roi":
          aValue = a.roi;
          bValue = b.roi;
          break;
        case "volume":
          aValue = a.volume;
          bValue = b.volume;
          break;
      }

      return sortOrder === "asc" ? aValue - bValue : bValue - aValue;
    });

    return sorted;
  }, [allRows, sortField, sortOrder]);

  // Paginate sorted data
  const rows = useMemo(() => {
    const start = page * pageSize;
    const end = start + pageSize;
    return sortedRows.slice(start, end);
  }, [sortedRows, page, pageSize]);

  const totalPages = Math.ceil(sortedRows.length / pageSize);

  // Check if we should show account_value and ROI columns
  // Hide them if filtering by Aster or if all data is from Aster
  const showAccountValueAndROI = useMemo(() => {
    if (dexFilter === "aster") return false;
    if (dexFilter === "hyperliquid") return true;
    // If "all", check if there's any Hyperliquid data
    return allRows.some((row: LeaderboardRow) => row.dex === "hyperliquid");
  }, [dexFilter, allRows]);

  // Reset ROI sort if switching to Aster and currently sorting by ROI
  useEffect(() => {
    if (!showAccountValueAndROI && sortField === "roi") {
      setSortField(null);
      setSortOrder("desc");
    }
  }, [showAccountValueAndROI, sortField]);

  const getTitle = () => {
    if (dexFilter === "aster") {
      return language === "zh" ? "交易者排行榜" : "Trader Leaderboard";
    } else if (dexFilter === "hyperliquid") {
      return language === "zh" ? "交易者排行榜" : "Trader Leaderboard";
    }
    return language === "zh" ? "交易者排行榜" : "Trader Leaderboard";
  };

  const formatUsd = (value: number) =>
    value >= 1_000_000
      ? `$${(value / 1_000_000).toFixed(1)}M`
      : `$${value.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;

  const formatRoi = (value: number) => `${(value * 100).toFixed(2)}%`;

  const addressDisplay = (row: LeaderboardRow) => {
    if (row.display_name) return row.display_name;
    return `${row.address.slice(0, 6)}...${row.address.slice(-4)}`;
  };

  const canPrev = page > 0;
  const canNext = page < totalPages - 1;

  const handleSort = (field: SortField) => {
    // Don't allow sorting by ROI if not showing ROI column
    if (field === "roi" && !showAccountValueAndROI) {
      return;
    }
    if (sortField === field) {
      // Toggle sort order
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      // Set new sort field, default to descending
      setSortField(field);
      setSortOrder("desc");
    }
    // Reset to first page when sorting changes
    setPage(0);
  };

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) return null;
    return <span className="ml-1">{sortOrder === "asc" ? "↑" : "↓"}</span>;
  };

  const summary = useMemo(() => {
    if (!total) return "";
    const baseText = language === "zh" ? "共" : "Total";
    return `${baseText} ${total.toLocaleString()} ${language === "zh" ? "个账户" : "accounts"}`;
  }, [total, language]);

  return (
    <div
      className="border p-0"
      style={{
        borderColor: "var(--panel-border)",
        background: "var(--panel-bg)",
      }}
    >
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between p-6 border-b" style={{ borderColor: "var(--panel-border)" }}>
        <div>
          <h2 className="text-sm font-black uppercase tracking-widest">{getTitle()}</h2>
          <p className="text-[10px] mt-1 font-bold uppercase opacity-40 px-1 border inline-block" style={{ borderColor: "var(--panel-border)" }}>
            {summary}
          </p>
        </div>

        <div className="flex items-center gap-4">
          <select
            className="border px-4 py-1 text-[10px] font-bold uppercase tracking-widest"
            style={{
              borderColor: "var(--panel-border)",
              background: "transparent",
            }}
            value={window}
            onChange={(e) => {
              setPage(0);
              setSortField(null);
              setSortOrder("desc");
              setWindow(e.target.value as typeof window);
            }}
          >
            {WINDOW_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>

          <div className="flex items-center text-[10px] font-bold uppercase tracking-widest">
            <button
              className="px-3 py-1 border hover:bg-black hover:text-white transition-colors disabled:opacity-20 translate-x-[1px]"
              style={{ borderColor: "var(--panel-border)" }}
              disabled={!canPrev}
              onClick={() => setPage((p) => Math.max(0, p - 1))}
            >
              {language === "zh" ? "上一页" : "Prev"}
            </button>
            <span className="px-3 py-1 border relative z-10 bg-white" style={{ borderColor: "var(--panel-border)" }}>
              {page + 1}/{totalPages || 1}
            </span>
            <button
              className="px-3 py-1 border hover:bg-black hover:text-white transition-colors disabled:opacity-20 -translate-x-[1px]"
              style={{ borderColor: "var(--panel-border)" }}
              disabled={!canNext}
              onClick={() => setPage((p) => (canNext ? p + 1 : p))}
            >
              {language === "zh" ? "下一页" : "Next"}
            </button>
          </div>
        </div>
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-xs font-bold uppercase tracking-widest opacity-30">Loading...</div>
      ) : rows.length === 0 ? (
        <div className="text-center py-12 text-xs font-bold uppercase tracking-widest opacity-30" style={{ color: "var(--muted-text)" }}>
          {language === "zh" ? "暂无数据" : "No data available"}
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b" style={{ borderColor: "var(--panel-border)" }}>
                <th className="text-left py-4 px-6 font-bold uppercase tracking-widest w-16">#</th>
                <th className="text-left py-4 px-6 font-bold uppercase tracking-widest">{language === "zh" ? "交易者" : "Trader"}</th>
                {showAccountValueAndROI && (
                  <th className="text-right py-4 px-6 font-bold uppercase tracking-widest">{language === "zh" ? "规模" : "Value"}</th>
                )}
                <th
                  className="text-right py-4 px-6 font-bold uppercase tracking-widest cursor-pointer hover:bg-black hover:text-white transition-colors"
                  onClick={() => handleSort("pnl")}
                >
                  {language === "zh" ? "盈亏" : "PNL"}
                  <SortIcon field="pnl" />
                </th>
                {showAccountValueAndROI && (
                  <th
                    className="text-right py-4 px-6 font-bold uppercase tracking-widest cursor-pointer hover:bg-black hover:text-white transition-colors"
                    onClick={() => handleSort("roi")}
                  >
                    {language === "zh" ? "收益率" : "ROI"}
                    <SortIcon field="roi" />
                  </th>
                )}
                <th
                  className="text-right py-4 px-6 font-bold uppercase tracking-widest cursor-pointer hover:bg-black hover:text-white transition-colors"
                  onClick={() => handleSort("volume")}
                >
                  {language === "zh" ? "成交量" : "Volume"}
                  <SortIcon field="volume" />
                </th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row: LeaderboardRow, index: number) => {
                const displayRank = sortField ? page * pageSize + index + 1 : row.rank;
                return (
                  <tr
                    key={`${row.address}-${row.rank}`}
                    className="border-b last:border-b-0 hover:bg-neutral-50 transition-colors font-mono tabular-nums"
                    style={{ borderColor: "var(--panel-border)" }}
                  >
                    <td className="py-4 px-6 font-black italic">{displayRank}</td>
                    <td className="py-4 px-6">
                      <div className="flex flex-col">
                        <span className="font-bold">{addressDisplay(row)}</span>
                        <span className="text-[10px] opacity-40 font-mono tracking-tight">
                          {row.address}
                          {row.dex && dexFilter === "all" && (
                            <span className="ml-1">[{row.dex}]</span>
                          )}
                        </span>
                      </div>
                    </td>
                    {showAccountValueAndROI && (
                      <td className="py-4 px-6 text-right">{formatUsd(row.account_value)}</td>
                    )}
                    <td className="py-4 px-6 text-right">
                      <span
                        className="font-black italic px-2 py-0.5 border text-[9px] tracking-tighter inline-block"
                        style={{
                          borderColor: row.pnl >= 0 ? "#22c55e" : "#ef4444",
                          color: row.pnl >= 0 ? "#22c55e" : "#ef4444",
                          background: row.pnl >= 0 ? "rgba(34, 197, 94, 0.05)" : "rgba(239, 68, 68, 0.05)",
                        }}
                      >
                        {formatUsd(row.pnl)}
                      </span>
                    </td>
                    {showAccountValueAndROI && (
                      <td className="py-4 px-6 text-right font-bold" style={{ color: row.roi >= 0 ? "#22c55e" : "#ef4444" }}>
                        {formatRoi(row.roi)}
                      </td>
                    )}
                    <td className="py-4 px-6 text-right opacity-60">{formatUsd(row.volume)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

