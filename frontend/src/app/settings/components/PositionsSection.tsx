"use client";

import { useMemo, useState } from "react";
import useSWR, { useSWRConfig } from "swr";
import type { Agent, Position } from "@/types";
import { api } from "@/lib/api";
import { fmtUSD } from "@/lib/utils/formatters";
import { getCoinIcon } from "@/lib/utils/coinIcons";
import { getAgentModelColor, getAgentModelName } from "@/lib/model/meta";
import { useLanguage } from "@/store/useLanguage";

interface ActionMessage {
  type: "success" | "error";
  text: string;
}

export function PositionsSection() {
  const language = useLanguage((s) => s.language);
  const [actionMessage, setActionMessage] = useState<ActionMessage | null>(null);
  const [closingMap, setClosingMap] = useState<Record<string, boolean>>({});
  const [closingAll, setClosingAll] = useState(false);
  const { mutate: globalMutate } = useSWRConfig();

  const { data: agentsData, error: agentsError, isLoading: agentsLoading } = useSWR<Agent[]>(
    "/settings/agents",
    api.getAgents,
    { refreshInterval: 10000 },
  );

  const runningAgents = useMemo(
    () => (agentsData || []).filter((agent) => agent.is_running),
    [agentsData],
  );

  const agentKey = useMemo(
    () => runningAgents.map((agent) => agent.id).sort().join(","),
    [runningAgents],
  );

  const {
    data: positionsMap,
    error: positionsError,
    isLoading: positionsLoading,
    mutate: mutatePositions,
  } = useSWR<Map<string, Position[]>>(
    agentKey ? (["settings-positions", agentKey] as const) : null,
    async ([, key]: readonly [string, string]) => {
      const ids = key.split(",").filter(Boolean);
      const results = await Promise.all(
        ids.map(async (id: string) => {
          try {
            const positions = await api.getPositions(id);
            return [id, positions ?? []] as [string, Position[]];
          } catch (error) {
            console.error(`Failed to fetch positions for ${id}:`, error);
            return [id, []] as [string, Position[]];
          }
        }),
      );
      return new Map(results);
    },
    { refreshInterval: 8000 },
  );

  const positionsData = runningAgents.map((agent) => ({
    agent,
    positions: positionsMap?.get(agent.id) ?? [],
  }));

  const totalPositions = positionsData.reduce((sum, entry) => sum + entry.positions.length, 0);
  const hasPositions = totalPositions > 0;
  const closeAllLabel = language === "zh" ? "一键平仓" : "Close All";
  const closeLabel = language === "zh" ? "平仓" : "Close";
  const loadingLabel = language === "zh" ? "加载持仓中..." : "Loading positions...";
  const noAgentsLabel = language === "zh" ? "无运行中的智能体" : "No running agents";
  const noPositionsLabel = language === "zh" ? "暂无持仓" : "No active positions";

  const setMessage = (type: ActionMessage["type"], text: string) => {
    setActionMessage({ type, text });
    setTimeout(() => setActionMessage(null), 4000);
  };

  const refreshPositions = async () => {
    await mutatePositions(undefined, { revalidate: true });
    await globalMutate(
      (key) => typeof key === "string" && key.includes('"agent-positions"'),
      undefined,
      { revalidate: true },
    );
  };

  const handleClosePosition = async (agentId: string, position: Position, rowKey: string) => {
    const key = rowKey;
    setClosingMap((prev) => ({ ...prev, [key]: true }));
    setActionMessage(null);

    try {
      await api.closeAgentPosition(agentId, {
        symbol: position.symbol,
        side: position.side,
      });
      setMessage("success", language === "zh" ? "平仓指令已发送" : "Close request sent");
      await refreshPositions();
    } catch (error: any) {
      const errorText =
        error?.message ??
        (language === "zh" ? "平仓失败，请稍后重试" : "Failed to close position, please try again");
      setMessage("error", errorText);
    } finally {
      setClosingMap((prev) => {
        const next = { ...prev };
        delete next[key];
        return next;
      });
    }
  };

  const handleCloseAll = async () => {
    if (!hasPositions || closingAll) return;
    setClosingAll(true);
    setActionMessage(null);

    try {
      const agentIds = runningAgents.map((agent) => agent.id);
      await api.closeAllPositions(agentIds);
      setMessage("success", language === "zh" ? "一键平仓已提交" : "Close-all request sent");
      await refreshPositions();
    } catch (error: any) {
      const errorText =
        error?.message ??
        (language === "zh" ? "一键平仓失败，请稍后重试" : "Failed to close all positions, please try again");
      setMessage("error", errorText);
    } finally {
      setClosingAll(false);
    }
  };

  if (agentsLoading) {
    return (
      <div
        className="rounded border px-4 py-6 text-center text-sm"
        style={{ borderColor: "var(--panel-border)", color: "var(--muted-text)" }}
      >
        {loadingLabel}
      </div>
    );
  }

  if (!runningAgents.length) {
    return (
      <div
        className="rounded border px-4 py-6 text-center text-sm"
        style={{ borderColor: "var(--panel-border)", color: "var(--muted-text)" }}
      >
        {noAgentsLabel}
      </div>
    );
  }

  return (
    <section className="space-y-4">
      {actionMessage && (
        <div
          className="rounded border px-3 py-2 text-xs"
          style={{
            borderColor: actionMessage.type === "success" ? "var(--brand-accent)" : "#ef4444",
            color: actionMessage.type === "success" ? "var(--brand-accent)" : "#ef4444",
          }}
        >
          {actionMessage.text}
        </div>
      )}

      {(agentsError || positionsError) && (
        <div className="rounded border px-3 py-2 text-xs" style={{ borderColor: "#ef4444", color: "#ef4444" }}>
          {agentsError?.message || positionsError?.message || "Failed to load data"}
        </div>
      )}

      <div className="flex items-center justify-between">
        <div className="text-xs" style={{ color: "var(--muted-text)" }}>
          {hasPositions
            ? `${totalPositions} ${language === "zh" ? "笔持仓" : "open positions"}`
            : noPositionsLabel}
        </div>
        {hasPositions && (
          <button
            onClick={handleCloseAll}
            disabled={closingAll}
            className="rounded border px-3 py-1 text-[11px] uppercase tracking-widest transition hover:opacity-80 disabled:opacity-40"
            style={{
              borderColor: "var(--panel-border)",
              color: closingAll ? "var(--muted-text)" : "var(--brand-accent)",
            }}
          >
            {closingAll ? `${closeAllLabel}...` : closeAllLabel}
          </button>
        )}
      </div>

      {!hasPositions && (
        <div
          className="rounded border px-4 py-6 text-center text-sm"
          style={{ borderColor: "var(--panel-border)", color: "var(--muted-text)" }}
        >
          {positionsLoading ? loadingLabel : noPositionsLabel}
        </div>
      )}

      {hasPositions &&
        positionsData.map(({ agent, positions }) => {
          if (!positions.length) return null;
          const totalPnL = positions.reduce((sum, pos) => sum + (pos.unrealized_profit || 0), 0);
          const color = getAgentModelColor(agent);
          const brandBg = `linear-gradient(0deg, ${color}10, var(--panel-bg))`;
          const brandBorder = `${color}55`;

          return (
            <div
              key={agent.id}
              className="rounded-md border p-3 space-y-3"
              style={{ background: brandBg as any, borderColor: brandBorder as any }}
            >
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--foreground)" }}>
                    {getAgentModelName(agent) || agent.name || agent.id}
                  </div>
                  <div className="text-[10px]" style={{ color: "var(--muted-text)" }}>
                    {positions.length} {language === "zh" ? "笔持仓" : "positions"}
                  </div>
                </div>
                <div
                  className="text-xs font-bold tabular-nums"
                  style={{ color: totalPnL >= 0 ? "#22c55e" : "#ef4444" }}
                >
                  {totalPnL >= 0 ? "+" : ""}
                  {fmtUSD(totalPnL)}
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-[11px] terminal-text">
                  <thead style={{ color: "var(--muted-text)" }}>
                    <tr className="border-b" style={{ borderColor: "var(--panel-border)" }}>
                      <th className="py-1.5 pr-2 font-normal">{language === "zh" ? "合约" : "Symbol"}</th>
                      <th className="py-1.5 pr-2 font-normal">{language === "zh" ? "方向" : "Side"}</th>
                      <th className="py-1.5 pr-2 font-normal">{language === "zh" ? "杠杆" : "Lev"}</th>
                      <th className="py-1.5 pr-2 font-normal">{language === "zh" ? "开仓价" : "Entry"}</th>
                      <th className="py-1.5 pr-2 font-normal">{language === "zh" ? "标记价" : "Mark"}</th>
                      <th className="py-1.5 pr-2 font-normal text-right">{language === "zh" ? "盈亏" : "P&L"}</th>
                      <th className="py-1.5 pr-2 font-normal text-right">
                        {language === "zh" ? "操作" : "Actions"}
                      </th>
                    </tr>
                  </thead>
                  <tbody style={{ color: "var(--foreground)" }}>
                    {positions.map((position, index) => {
                      const pnlDenominator = position.entry_price * (position.position_amt || 1);
                      const pnlPct =
                        pnlDenominator === 0 ? 0 : (position.unrealized_profit / pnlDenominator) * 100;
                      const key = `${agent.id}-${position.symbol}-${position.side}-${index}`;
                      const isClosing = !!closingMap[key];

                      return (
                        <tr
                          key={key}
                          className="border-b"
                          style={{
                            borderColor: "color-mix(in oklab, var(--panel-border) 30%, transparent)",
                          }}
                        >
                          <td className="py-1.5 pr-2">
                            <div className="flex items-center gap-1">
                              {getCoinIcon(position.symbol) && (
                                <img
                                  src={getCoinIcon(position.symbol)}
                                  alt={position.symbol}
                                  className="w-3.5 h-3.5"
                                />
                              )}
                              <span className="font-bold">{position.symbol}</span>
                            </div>
                          </td>
                          <td
                            className="py-1.5 pr-2"
                            style={{ color: position.side === "long" ? "#22c55e" : "#ef4444" }}
                          >
                            {position.side.toUpperCase()}
                          </td>
                          <td className="py-1.5 pr-2">
                            <span style={{ color: "var(--brand-accent)" }}>{position.leverage}x</span>
                          </td>
                          <td className="py-1.5 pr-2 tabular-nums">{fmtUSD(position.entry_price)}</td>
                          <td className="py-1.5 pr-2 tabular-nums">{fmtUSD(position.mark_price)}</td>
                          <td
                            className="py-1.5 pr-2 text-right"
                            style={{ color: position.unrealized_profit >= 0 ? "#22c55e" : "#ef4444" }}
                          >
                            <div className="font-bold tabular-nums">{fmtUSD(position.unrealized_profit)}</div>
                            <div className="text-[10px] tabular-nums">
                              {pnlPct >= 0 ? "+" : ""}
                              {pnlPct.toFixed(2)}%
                            </div>
                          </td>
                          <td className="py-1.5 pr-2 text-right">
                            <button
                              onClick={() => handleClosePosition(agent.id, position, key)}
                              disabled={isClosing}
                              className="rounded border px-2 py-1 text-[10px] uppercase tracking-widest transition hover:opacity-80 disabled:opacity-40"
                              style={{ borderColor: "var(--panel-border)" }}
                            >
                              {isClosing ? `${closeLabel}...` : closeLabel}
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          );
        })}
    </section>
  );
}

