"use client";

import { useState } from "react";
import useSWR from "swr";
import { api } from "@/lib/api";
import { formatDistanceToNow } from "date-fns";
import { useLanguage } from "@/store/useLanguage";

interface LargeTradeMonitorProps {
  dexFilter: "all" | "aster" | "hyperliquid";
}

interface LargeTrade {
  symbol: string;
  side: "BUY" | "SELL";
  price: number;
  quantity: number;
  quote_quantity: number;
  timestamp: string;
  is_buyer_maker: boolean;
  dex: "aster" | "hyperliquid";
  trade_id?: string;
}

export default function LargeTradeMonitor({
  dexFilter,
}: LargeTradeMonitorProps) {
  const language = useLanguage((s) => s.language);
  const [timeWindow, setTimeWindow] = useState<"1h" | "6h" | "24h">("24h");
  const [page, setPage] = useState(0);
  const pageSize = 10;

  const { data, error, isLoading } = useSWR(
    `/dashboard/large-trades?dex=${dexFilter}&time_window=${timeWindow}&limit=${pageSize}&offset=${page * pageSize}`,
    () => api.getLargeTrades(
      dexFilter === "all" ? undefined : dexFilter,
      undefined,
      undefined,
      100_000,
      timeWindow,
      pageSize,
      page * pageSize
    ),
    {
      refreshInterval: 10000, // Refresh every 10 seconds
    }
  );

  const total = data?.pagination?.total ?? 0;
  const totalPages = Math.ceil(total / pageSize);
  const canPrev = page > 0;
  const canNext = page < totalPages - 1;

  const parseDate = (timestamp: string) => {
    if (!timestamp) return new Date();
    if (/^\d+$/.test(timestamp)) return new Date(parseInt(timestamp));

    let dateStr = timestamp;
    if (dateStr.includes(" ")) dateStr = dateStr.replace(" ", "T");
    if (!dateStr.includes("Z") && !dateStr.includes("+")) {
      dateStr += "Z";
    }
    return new Date(dateStr);
  };

  const formatTime = (timestamp: string) => {
    const d = parseDate(timestamp);
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false });
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
            {language === "zh" ? "大额交易监控" : "Large Trade Monitor"}
          </h2>
          {data?.stats && (
            <p className="text-[10px] mt-1 font-bold uppercase opacity-40 px-1 border" style={{ borderColor: "var(--panel-border)" }}>
              {language === "zh" ? "总计" : "Total"}: {data.stats.total_count} {language === "zh" ? "笔" : "trades"} |
              ${data.stats.total_volume.toLocaleString(undefined, { maximumFractionDigits: 0 })}
            </p>
          )}
        </div>

        <div className="flex items-center gap-4">
          <select
            value={timeWindow}
            onChange={(e) => {
              setPage(0);
              setTimeWindow(e.target.value as "1h" | "6h" | "24h");
            }}
            className="border px-4 py-1 text-[10px] font-bold uppercase tracking-widest"
            style={{
              borderColor: "var(--panel-border)",
              background: "transparent",
            }}
          >
            <option value="1h">1h</option>
            <option value="6h">6h</option>
            <option value="24h">24h</option>
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
      ) : error ? (
        <div className="text-center py-12 text-xs font-bold uppercase tracking-widest text-red-500">
          {language === "zh" ? "加载数据失败" : "Error loading data"}
        </div>
      ) : !data?.trades || data.trades.length === 0 ? (
        <div className="text-center py-12 text-xs font-bold uppercase tracking-widest opacity-30" style={{ color: "var(--muted-text)" }}>
          {language === "zh" ? "暂无大额交易" : "No large trades found"}
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b" style={{ borderColor: "var(--panel-border)" }}>
                <th className="text-left py-4 px-6 font-bold uppercase tracking-widest">{language === "zh" ? "资产" : "Symbol"}</th>
                <th className="text-left py-4 px-6 font-bold uppercase tracking-widest">{language === "zh" ? "方向" : "Side"}</th>
                <th className="text-right py-4 px-6 font-bold uppercase tracking-widest">{language === "zh" ? "价格" : "Price"}</th>
                <th className="text-right py-4 px-6 font-bold uppercase tracking-widest">{language === "zh" ? "金额" : "Amount"}</th>
                <th className="text-right py-4 px-6 font-bold uppercase tracking-widest">{language === "zh" ? "时间" : "Time"}</th>
              </tr>
            </thead>
            <tbody>
              {data.trades.map((trade: LargeTrade, index: number) => (
                <tr
                  key={`${trade.trade_id || index}-${trade.timestamp}`}
                  className="border-b last:border-b-0 hover:bg-neutral-50 transition-colors"
                  style={{ borderColor: "var(--panel-border)" }}
                >
                  <td className="py-4 px-6 font-bold">
                    {trade.symbol}
                  </td>
                  <td className="py-4 px-6">
                    <span
                      className="font-black italic px-2 py-0.5 border text-[9px] tracking-tighter"
                      style={{
                        borderColor: trade.side === "BUY" ? "#22c55e" : "#ef4444",
                        color: trade.side === "BUY" ? "#22c55e" : "#ef4444",
                        background: trade.side === "BUY" ? "rgba(34, 197, 94, 0.05)" : "rgba(239, 68, 68, 0.05)",
                      }}
                    >
                      {trade.side}
                    </span>
                  </td>
                  <td className="text-right py-4 px-6 font-mono tabular-nums">
                    {trade.price.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                  </td>
                  <td className="text-right py-4 px-6 font-black font-mono tabular-nums">
                    ${trade.quote_quantity.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                  </td>
                  <td className="text-right py-4 px-6 text-[10px] font-bold uppercase opacity-40">
                    {formatDistanceToNow(parseDate(trade.timestamp), { addSuffix: true })}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

