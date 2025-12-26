"use client";

import { useState, useMemo } from "react";
import useSWR from "swr";
import { api } from "@/lib/api";
import { useLanguage } from "@/store/useLanguage";

interface TokenRankingsProps {
  dexFilter: "all" | "aster" | "hyperliquid";
}

interface TokenRanking {
  symbol: string;
  funding_rate?: number;
  volume_24h?: number;
  quote_volume_24h?: number;
  price_change_24h?: number;
  price_change_percent_24h?: number;
  open_interest?: number;
  dex: "aster" | "hyperliquid";
}

type SortField =
  | "symbol"
  | "funding_rate"
  | "quote_volume_24h"
  | "price_change_percent_24h"
  | "open_interest";

type SortOrder = "asc" | "desc";

export default function TokenRankings({
  dexFilter,
}: TokenRankingsProps) {
  const language = useLanguage((s) => s.language);

  // Default sort by volume (quote_volume_24h) descending
  const [sortField, setSortField] = useState<SortField>("quote_volume_24h");
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc");
  const [page, setPage] = useState(0);
  const pageSize = 10;

  // Fetch multiple ranking types and merge them
  const { data: volumeData } = useSWR(
    `/dashboard/rankings/volume?dex=${dexFilter === "all" ? "" : dexFilter}`,
    () => api.getTokenRankings("volume", dexFilter === "all" ? undefined : dexFilter, "desc", 100),
    { refreshInterval: 30000 }
  );

  const { data: priceChangeData } = useSWR(
    `/dashboard/rankings/price-change?dex=${dexFilter === "all" ? "" : dexFilter}`,
    () => api.getTokenRankings("price-change", dexFilter === "all" ? undefined : dexFilter, "desc", 100),
    { refreshInterval: 30000 }
  );

  const { data: fundingRateData } = useSWR(
    `/dashboard/rankings/funding-rate?dex=${dexFilter === "all" ? "" : dexFilter}`,
    () => api.getTokenRankings("funding-rate", dexFilter === "all" ? undefined : dexFilter, "desc", 100),
    { refreshInterval: 30000 }
  );

  const { data: openInterestData } = useSWR(
    (dexFilter === "hyperliquid" || dexFilter === "all") ? `/dashboard/rankings/open-interest` : null,
    () => api.getTokenRankings("open-interest", undefined, "desc", 100),
    { refreshInterval: 30000 }
  );

  // Merge all ranking data by symbol and dex
  const mergedData = useMemo(() => {
    const dataMap = new Map<string, TokenRanking>();

    // Merge volume data
    if (volumeData) {
      volumeData.forEach((item: any) => {
        const key = `${item.symbol}-${item.dex}`;
        dataMap.set(key, { ...item });
      });
    }

    // Merge price change data
    if (priceChangeData) {
      priceChangeData.forEach((item: any) => {
        const key = `${item.symbol}-${item.dex}`;
        const existing = dataMap.get(key) || { symbol: item.symbol, dex: item.dex };
        dataMap.set(key, { ...existing, ...item });
      });
    }

    // Merge funding rate data
    if (fundingRateData) {
      fundingRateData.forEach((item: any) => {
        const key = `${item.symbol}-${item.dex}`;
        const existing = dataMap.get(key) || { symbol: item.symbol, dex: item.dex };
        dataMap.set(key, { ...existing, funding_rate: item.funding_rate });
      });
    }

    // Merge open interest data (Hyperliquid only)
    if (openInterestData) {
      openInterestData.forEach((item: any) => {
        const key = `${item.symbol}-${item.dex}`;
        const existing = dataMap.get(key) || { symbol: item.symbol, dex: item.dex };
        dataMap.set(key, { ...existing, open_interest: item.open_interest });
      });
    }

    return Array.from(dataMap.values());
  }, [volumeData, priceChangeData, fundingRateData, openInterestData]);

  const isLoading = !volumeData && !priceChangeData;
  const error = false; // Could enhance to track errors from all requests

  // Sort data
  const sortedData = useMemo(() => {
    if (!mergedData || mergedData.length === 0) return [];

    const sorted = [...mergedData].sort((a, b) => {
      let aValue: number | string = 0;
      let bValue: number | string = 0;

      switch (sortField) {
        case "symbol":
          aValue = a.symbol;
          bValue = b.symbol;
          break;
        case "funding_rate":
          aValue = a.funding_rate ?? 0;
          bValue = b.funding_rate ?? 0;
          break;
        case "quote_volume_24h":
          aValue = a.quote_volume_24h ?? 0;
          bValue = b.quote_volume_24h ?? 0;
          break;
        case "price_change_percent_24h":
          aValue = a.price_change_percent_24h ?? 0;
          bValue = b.price_change_percent_24h ?? 0;
          break;
        case "open_interest":
          aValue = a.open_interest ?? 0;
          bValue = b.open_interest ?? 0;
          break;
      }

      if (typeof aValue === "string" && typeof bValue === "string") {
        return sortOrder === "asc"
          ? aValue.localeCompare(bValue)
          : bValue.localeCompare(aValue);
      }

      return sortOrder === "asc"
        ? (aValue as number) - (bValue as number)
        : (bValue as number) - (aValue as number);
    });

    return sorted;
  }, [mergedData, sortField, sortOrder]);

  // Paginate sorted data
  const paginatedData = useMemo(() => {
    const start = page * pageSize;
    const end = start + pageSize;
    return sortedData.slice(start, end);
  }, [sortedData, page, pageSize]);

  const totalPages = Math.ceil(sortedData.length / pageSize);
  const canPrev = page > 0;
  const canNext = page < totalPages - 1;

  const handleSort = (field: SortField) => {
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
          <h2 className="text-sm font-black uppercase tracking-widest">
            {language === "zh" ? "代币数据排行" : "Token Rankings"}
          </h2>
          {sortedData.length > 0 && (
            <p className="text-[10px] mt-1 font-bold uppercase opacity-40 px-1 border inline-block" style={{ borderColor: "var(--panel-border)" }}>
              {language === "zh" ? "总计" : "Total"}: {sortedData.length} {language === "zh" ? "个代币" : "tokens"}
            </p>
          )}
        </div>

        {sortedData.length > pageSize && (
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
        )}
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-xs font-bold uppercase tracking-widest opacity-30">Loading...</div>
      ) : error ? (
        <div className="text-center py-12 text-xs font-bold uppercase tracking-widest text-red-500">
          {language === "zh" ? "加载数据失败" : "Error loading data"}
        </div>
      ) : !sortedData || sortedData.length === 0 ? (
        <div className="text-center py-12 text-xs font-bold uppercase tracking-widest opacity-30" style={{ color: "var(--muted-text)" }}>
          {language === "zh" ? "暂无数据" : "No data available"}
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b" style={{ borderColor: "var(--panel-border)" }}>
                <th
                  className="text-left py-4 px-6 font-bold uppercase tracking-widest cursor-pointer hover:bg-black hover:text-white transition-colors"
                  onClick={() => handleSort("symbol")}
                >
                  {language === "zh" ? "资产" : "Symbol"}
                  <SortIcon field="symbol" />
                </th>
                <th
                  className="text-right py-4 px-6 font-bold uppercase tracking-widest cursor-pointer hover:bg-black hover:text-white transition-colors"
                  onClick={() => handleSort("funding_rate")}
                >
                  {language === "zh" ? "资金费" : "Funding"}
                  <SortIcon field="funding_rate" />
                </th>
                <th
                  className="text-right py-4 px-6 font-bold uppercase tracking-widest cursor-pointer hover:bg-black hover:text-white transition-colors"
                  onClick={() => handleSort("quote_volume_24h")}
                >
                  {language === "zh" ? "成交额" : "Volume"}
                  <SortIcon field="quote_volume_24h" />
                </th>
                <th
                  className="text-right py-4 px-6 font-bold uppercase tracking-widest cursor-pointer hover:bg-black hover:text-white transition-colors"
                  onClick={() => handleSort("price_change_percent_24h")}
                >
                  {language === "zh" ? "涨跌幅" : "Change"}
                  <SortIcon field="price_change_percent_24h" />
                </th>
                {(dexFilter === "hyperliquid" || dexFilter === "all") && (
                  <th
                    className="text-right py-4 px-6 font-bold uppercase tracking-widest cursor-pointer hover:bg-black hover:text-white transition-colors"
                    onClick={() => handleSort("open_interest")}
                  >
                    {language === "zh" ? "持仓" : "OI"}
                    <SortIcon field="open_interest" />
                  </th>
                )}
              </tr>
            </thead>
            <tbody>
              {paginatedData.map((token, index) => (
                <tr
                  key={`${token.symbol}-${token.dex}-${index}`}
                  className="border-b last:border-b-0 hover:bg-neutral-50 transition-colors"
                  style={{ borderColor: "var(--panel-border)" }}
                >
                  <td className="py-4 px-6 font-bold italic">
                    {token.symbol}
                  </td>
                  <td className="text-right py-4 px-6 font-mono tabular-nums">
                    {token.funding_rate !== undefined
                      ? `${token.funding_rate.toFixed(4)}%`
                      : "-"}
                  </td>
                  <td className="text-right py-4 px-6 font-black font-mono tabular-nums">
                    {token.quote_volume_24h
                      ? `$${token.quote_volume_24h.toLocaleString(undefined, { maximumFractionDigits: 0 })}`
                      : "-"}
                  </td>
                  <td className="text-right py-4 px-6">
                    <span
                      className="font-black italic px-2 py-0.5 border text-[9px] tracking-tighter"
                      style={{
                        borderColor: (token.price_change_percent_24h ?? 0) >= 0 ? "#22c55e" : "#ef4444",
                        color: (token.price_change_percent_24h ?? 0) >= 0 ? "#22c55e" : "#ef4444",
                        background: (token.price_change_percent_24h ?? 0) >= 0 ? "rgba(34, 197, 94, 0.05)" : "rgba(239, 68, 68, 0.05)",
                      }}
                    >
                      {token.price_change_percent_24h !== undefined
                        ? `${token.price_change_percent_24h >= 0 ? "+" : ""}${token.price_change_percent_24h.toFixed(2)}%`
                        : "-"}
                    </span>
                  </td>
                  {(dexFilter === "hyperliquid" || dexFilter === "all") && (
                    <td className="text-right py-4 px-6 font-mono tabular-nums opacity-60">
                      {token.open_interest
                        ? `$${token.open_interest.toLocaleString(undefined, { maximumFractionDigits: 0 })}`
                        : "-"}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

