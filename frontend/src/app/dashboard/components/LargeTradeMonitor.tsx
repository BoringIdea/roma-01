"use client";

import { useState } from "react";
import useSWR from "swr";
import { api } from "@/lib/api";
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

  return (
    <div
      className="rounded-xl border p-5"
      style={{
        borderColor: "var(--panel-border)",
        background: "var(--panel-bg)",
      }}
    >
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between mb-4">
        <div>
          <h2 className="text-sm font-semibold uppercase tracking-wider">
            {language === "zh" ? "大额交易监控" : "Large Trade Monitor"}
          </h2>
          {data?.stats && (
            <p className="text-xs mt-1" style={{ color: "var(--muted-text)" }}>
              {language === "zh" ? "总计" : "Total"}: {data.stats.total_count} {language === "zh" ? "笔" : "trades"} | 
              ${data.stats.total_volume.toLocaleString(undefined, { maximumFractionDigits: 0 })}
            </p>
          )}
        </div>

        <div className="flex items-center gap-2">
          <select
            value={timeWindow}
            onChange={(e) => {
              setPage(0);
              setTimeWindow(e.target.value as "1h" | "6h" | "24h");
            }}
            className="rounded border px-2 py-1 text-xs"
            style={{
              borderColor: "var(--panel-border)",
              background: "var(--panel-bg)",
            }}
          >
            <option value="1h">1h</option>
            <option value="6h">6h</option>
            <option value="24h">24h</option>
          </select>

          <div className="flex items-center gap-1 text-xs">
            <button
              className="px-2 py-1 border rounded disabled:opacity-40"
              style={{ borderColor: "var(--panel-border)" }}
              disabled={!canPrev}
              onClick={() => setPage((p) => Math.max(0, p - 1))}
            >
              {language === "zh" ? "上一页" : "Prev"}
            </button>
            <span>
              {page + 1}/{totalPages || 1}
            </span>
            <button
              className="px-2 py-1 border rounded disabled:opacity-40"
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
        <div className="text-center py-8">Loading...</div>
      ) : error ? (
        <div className="text-center py-8 text-red-500">
          {language === "zh" ? "加载数据失败" : "Error loading data"}
        </div>
      ) : !data?.trades || data.trades.length === 0 ? (
        <div className="text-center py-8" style={{ color: "var(--muted-text)" }}>
          {language === "zh" ? "暂无大额交易" : "No large trades found"}
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr style={{ borderBottomColor: "var(--panel-border)" }}>
                <th className="text-left py-2">{language === "zh" ? "交易对" : "Symbol"}</th>
                <th className="text-left py-2">{language === "zh" ? "方向" : "Side"}</th>
                <th className="text-right py-2">{language === "zh" ? "价格" : "Price"}</th>
                <th className="text-right py-2">{language === "zh" ? "金额" : "Amount"}</th>
                <th className="text-right py-2">{language === "zh" ? "时间" : "Time"}</th>
              </tr>
            </thead>
            <tbody>
              {data.trades.map((trade: LargeTrade, index: number) => (
                <tr
                  key={`${trade.trade_id || index}-${trade.timestamp}`}
                  style={{ borderBottomColor: "var(--panel-border)" }}
                >
                  <td className="py-2">
                    {trade.symbol}
                  </td>
                  <td
                    className="py-2"
                    style={{
                      color: trade.side === "BUY" ? "#10b981" : "#ef4444",
                    }}
                  >
                    {trade.side}
                  </td>
                  <td className="text-right py-2">
                    {trade.price.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                  </td>
                  <td className="text-right py-2 font-semibold">
                    ${trade.quote_quantity.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                  </td>
                  <td className="text-right py-2 text-xs">
                    {new Date(trade.timestamp).toLocaleTimeString()}
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

