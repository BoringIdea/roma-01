"use client";

import { useMemo, useState, useEffect, useRef, useCallback } from "react";
import useSWR from "swr";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  ReferenceLine,
} from "recharts";
import { format } from "date-fns";
import { api } from "@/lib/api";
import { getAgentModelColor, getAgentModelIcon } from "@/lib/model/meta";
import { adjustLuminance } from "@/lib/utils/color";
import type { Agent, EquityPoint } from "@/types";
import { useLanguage } from "@/store/useLanguage";
import { getTranslation } from "@/lib/i18n";

interface AccountValueChartProps {
  agents: Agent[];
}

type Range = "ALL" | "72H";
type Mode = "$" | "%";

// Custom hook to fetch equity data for multiple agents
function useAgentsEquityData(agentIds: string[]) {
  // Create a stable key for the agents list
  const agentsKey = agentIds.sort().join(',');
  
  // Fetch all equity data in a single SWR call
  // Use agentsKey as the cache key to ensure cache is invalidated when agent list changes
  const { data: allEquityData } = useSWR(
    agentsKey ? `/agents/equity-batch?ids=${agentsKey}` : null,
    async () => {
      // Fetch all agents' equity data in parallel
      const results = await Promise.all(
        agentIds.map(async (id) => {
          try {
            const [equityData, accountData] = await Promise.all([
              api.getEquityHistory(id).catch(() => []),
              api.getAccount(id).catch(() => null),
            ]);
            
            // If equity history is empty but account data exists, create initial point
            if ((!equityData || equityData.length === 0) && accountData) {
              const now = new Date().toISOString();
              const adjustedEquity = accountData.adjusted_total_balance ?? accountData.total_wallet_balance ?? 0;
              const grossEquity = accountData.gross_total_balance ?? accountData.total_wallet_balance ?? adjustedEquity;
              return {
                agentId: id,
                data: [{
                  timestamp: now,
                  cycle: 0,
                  equity: adjustedEquity,
                  adjusted_equity: adjustedEquity,
                  gross_equity: grossEquity,
                  pnl: accountData.total_unrealized_profit || 0,
                  unrealized_pnl: accountData.total_unrealized_profit || 0,
                  net_deposits: accountData.net_deposits || 0,
                  external_cash_flow: accountData.external_cash_flow || 0,
                }],
              };
            }
            
            return { agentId: id, data: equityData || [] };
          } catch (error) {
            // Silently handle 404s (agent not found) - this is expected when agents are removed
            if (error instanceof Error && error.message.includes('404')) {
              console.debug(`Agent ${id} not found, skipping`);
              return { agentId: id, data: [] };
            }
            console.error(`Failed to fetch equity for ${id}:`, error);
            return { agentId: id, data: [] };
          }
        })
      );
      return results;
    },
    { 
      refreshInterval: 30000, // Refresh every 30 seconds
      revalidateOnFocus: false, // Don't revalidate on window focus to avoid stale agent requests
      revalidateOnReconnect: true, // Revalidate when network reconnects
      dedupingInterval: 5000, // Dedupe requests within 5 seconds
    }
  );

  return allEquityData || [];
}

export function AccountValueChart({ agents }: AccountValueChartProps) {
  const language = useLanguage((s) => s.language);
  const translations = getTranslation(language);
  const tLeaderboard = translations.leaderboard;
  const tCharts = translations.charts;
  const [range, setRange] = useState<Range>("ALL");
  const [mode, setMode] = useState<Mode>("$");
  const [vw, setVw] = useState<number>(0);
  
  // Use running agents directly for legend, not predefined models
  // Include model_id for getting correct color and icon
  const runningAgents = useMemo(() => {
    const result = agents.filter(a => a.is_running).map(a => ({
      id: a.id,
      name: a.name || a.id,
      is_running: true,
      model_id: a.model_id,
      model_config_id: a.model_config_id,
      model_provider: a.model_provider,
      llm_model: a.llm_model,
    }));
    
    return result;
  }, [agents]);

  const [active, setActive] = useState<Set<string>>(new Set(runningAgents.map(a => a.id)));

  // Fetch equity history for running agents only
  const runningAgentIds = useMemo(() => runningAgents.map(a => a.id), [runningAgents]);
  const equityDataQueries = useAgentsEquityData(runningAgentIds);
  
  // Track viewport width for responsive sizing
  useEffect(() => {
    const upd = () => setVw(typeof window !== "undefined" ? window.innerWidth : 0);
    upd();
    let timeout: ReturnType<typeof setTimeout>;
    const debouncedUpd = () => {
      clearTimeout(timeout);
      timeout = setTimeout(upd, 150);
    };
    window.addEventListener("resize", debouncedUpd);
    return () => {
      clearTimeout(timeout);
      window.removeEventListener("resize", debouncedUpd);
    };
  }, []);

  // Combine equity history from all agents into chart data
  const { chartDataGross, chartDataAdjusted, chartDataNetDeposits } = useMemo(() => {
    const timestampMap = new Map<number, {
      timestamp: Date;
      gross: Record<string, number>;
      adjusted: Record<string, number>;
      net: Record<string, number>;
    }>();

    equityDataQueries.forEach(({ agentId, data }) => {
      if (!data || data.length === 0) return;

      data.forEach((point: EquityPoint) => {
        const timestampMs = new Date(point.timestamp).getTime();
        if (!timestampMap.has(timestampMs)) {
          timestampMap.set(timestampMs, {
            timestamp: new Date(point.timestamp),
            gross: {},
            adjusted: {},
            net: {},
          });
        }
        const bucket = timestampMap.get(timestampMs)!;
        const gross = point.gross_equity ?? point.equity;
        const adjusted = point.adjusted_equity ?? point.equity;
        const netDeposits = point.net_deposits;
        if (typeof gross === "number") bucket.gross[agentId] = gross;
        if (typeof adjusted === "number") bucket.adjusted[agentId] = adjusted;
        if (typeof netDeposits === "number") bucket.net[agentId] = netDeposits;
      });
    });

    let buckets = Array.from(timestampMap.values()).sort(
      (a, b) => a.timestamp.getTime() - b.timestamp.getTime()
    );

    if (range === "72H" && buckets.length > 0) {
      const cutoff = Date.now() - 72 * 60 * 60 * 1000;
      buckets = buckets.filter((bucket) => bucket.timestamp.getTime() >= cutoff);
    }

    const grossPoints = buckets.map((bucket) => ({
      timestamp: bucket.timestamp,
      ...bucket.gross,
    }));

    const adjustedPoints = buckets.map((bucket) => ({
      timestamp: bucket.timestamp,
      ...bucket.adjusted,
    }));

    const netDepositPoints = buckets.map((bucket) => ({
      timestamp: bucket.timestamp,
      ...bucket.net,
    }));

    return {
      chartDataGross: grossPoints,
      chartDataAdjusted: adjustedPoints,
      chartDataNetDeposits: netDepositPoints,
    };
  }, [equityDataQueries, range]);

  const initialEquityStats = useMemo(() => {
    const map: Record<string, { adjusted: number; net: number }> = {};
    equityDataQueries.forEach(({ agentId, data }) => {
      if (!data || data.length === 0) return;
      const first = data[0];
      const initialAdjusted =
        typeof first.adjusted_equity === "number"
          ? first.adjusted_equity
          : typeof first.equity === "number"
          ? first.equity
          : 0;
      const initialNet =
        typeof first.net_deposits === "number" ? first.net_deposits : 0;
      map[agentId] = {
        adjusted: initialAdjusted,
        net: initialNet,
      };
    });
    return map;
  }, [equityDataQueries]);

  // Convert to display data (gross for $, adjusted percentage for %)
  const displayData = useMemo(() => {
    if (mode === "%") {
      return chartDataAdjusted.map((point, idx) => {
        const newPoint: Record<string, any> = { timestamp: point.timestamp };
        runningAgentIds.forEach((id) => {
          const value = (point as any)[id];
          const netPoint = chartDataNetDeposits[idx] as any;
          const perAgentInitial = initialEquityStats[id];
          if (!perAgentInitial || typeof value !== "number") return;
          const initialAdjusted = perAgentInitial.adjusted;
          const initialNet = perAgentInitial.net;
          const netValue =
            typeof netPoint?.[id] === "number" ? netPoint[id] : initialNet;
          const netDelta = netValue - initialNet;
          const positiveContrib = Math.max(netDelta, 0);
          const capitalBase =
            (typeof initialAdjusted === "number" ? initialAdjusted : 0) +
            positiveContrib;
          const denominator =
            capitalBase > 0
              ? capitalBase
              : Math.max(
                  typeof initialAdjusted === "number" && initialAdjusted !== 0
                    ? initialAdjusted
                    : 1,
                  1,
                );
          const pnl = value - initialAdjusted;
          newPoint[id] = (pnl / denominator) * 100;
        });
        return newPoint;
      });
    }
    return chartDataGross;
  }, [
    chartDataAdjusted,
    chartDataGross,
    chartDataNetDeposits,
    initialEquityStats,
    mode,
    runningAgentIds,
  ]);

  const yAxisDomain = useMemo<[number | "auto", number | "auto"]>(() => {
    const visibleIds = runningAgentIds.filter((id) =>
      active.size ? active.has(id) : true
    );
    let min = Number.POSITIVE_INFINITY;
    let max = Number.NEGATIVE_INFINITY;

    if (visibleIds.length === 0 || displayData.length === 0) {
      return ["auto", "auto"];
    }

    for (const point of displayData) {
      for (const id of visibleIds) {
        const value = (point as any)[id];
        if (typeof value === "number" && Number.isFinite(value)) {
          if (value < min) min = value;
          if (value > max) max = value;
        }
      }
    }

    if (!Number.isFinite(min) || !Number.isFinite(max)) {
      return ["auto", "auto"];
    }

    const range = max - min;
    const base = range !== 0 ? range : Math.max(Math.abs(max), 1);
    const padding = base * 0.1;

    const upper = max + padding;
    let lower = min - padding * 0.6;

    if (mode !== "%" && lower < 0) {
      lower = 0;
    }

    return [lower, upper];
  }, [active, displayData, mode, runningAgentIds]);

  // Calculate last index and value per model for end dot rendering
  const lastIdxById = useMemo(() => {
    const m: Record<string, number> = {};
    for (const id of runningAgentIds) {
      for (let i = displayData.length - 1; i >= 0; i--) {
        const v = (displayData[i] as any)[id];
        if (typeof v === "number") {
          m[id] = i;
          break;
        }
      }
    }
    return m;
  }, [runningAgentIds, displayData]);

  const lastValById = useMemo(() => {
    const m: Record<string, number | undefined> = {};
    for (const id of runningAgentIds) {
      const idx = lastIdxById[id];
      if (typeof idx === "number") {
        const v = (displayData[idx] as any)?.[id];
        if (typeof v === "number") m[id] = v;
      }
    }
    return m;
  }, [runningAgentIds, displayData, lastIdxById]);

  const formatValue = (v: number | undefined) => {
    if (typeof v !== "number") return "--";
    if (mode === "%") return `${v >= 0 ? "+" : ""}${v.toFixed(1)}%`;
    try {
      return `$${Number(v).toLocaleString(undefined, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      })}`;
    } catch {
      const n = Math.round(Number(v) * 100) / 100;
      return `$${n}`;
    }
  };

  const formatYAxisTick = useCallback(
    (value: number) => {
      if (mode === "%") {
        return `${value.toFixed(1)}%`;
      }
      if (!Number.isFinite(value)) {
        return "";
      }
      const abs = Math.abs(value);
      if (abs >= 1_000_000_000) {
        return `$${(value / 1_000_000_000).toFixed(1)}B`;
      }
      if (abs >= 1_000_000) {
        return `$${(value / 1_000_000).toFixed(1)}M`;
      }
      if (abs >= 10_000) {
        return `$${(value / 1_000).toFixed(1)}K`;
      }
      return `$${Number(value).toLocaleString(undefined, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      })}`;
    },
    [mode],
  );

  // End-logo size and dynamic right margin
  const endLogoBaseSize = vw < 380 ? 21 : vw < 640 ? 27 : vw < 1024 ? 42 : 44;
  const endLogoSize = Math.round((endLogoBaseSize * 2) / 3);
  const marginFactor = vw < 380 ? 1.2 : vw < 640 ? 1.35 : vw < 1024 ? 1.6 : 1.7;
  const chartRightMargin = Math.max(64, Math.round(endLogoSize * marginFactor));

  // Render model icon at the end of the line
  const renderEndDot = (id: string) => (p: any) => {
    const { cx, cy, index } = p || {};
    if (cx == null || cy == null) return <g key={`empty-${id}-${index}`} />;
    if (typeof lastIdxById[id] !== "number" || index !== lastIdxById[id])
      return <g key={`empty-${id}-${index}`} />;
    if (active.size && !active.has(id))
      return <g key={`empty-${id}-${index}`} />;
    
    // Get model_id from agent to find correct icon and color
    const agent = runningAgents.find(a => a.id === id);
    const icon = getAgentModelIcon(agent);
    const color = getAgentModelColor(agent);
    const bg = color || "var(--chart-logo-bg)";
    const ring = typeof bg === "string" && bg.startsWith("#")
      ? adjustLuminance(bg, -0.15)
      : "var(--chart-logo-ring)";
    const size = endLogoSize;
    const haloR = Math.round((endLogoBaseSize / 3) * (2 / 3));
    const valueStr = formatValue(lastValById[id]);
    const isVisible = active.size ? active.has(id) : true;
    const showValueChip = isVisible;
    const fontSize = vw < 380 ? 11 : vw < 640 ? 12 : 13;
    const chipPadX = 8;
    const charW = Math.round(fontSize * 0.62);
    const chipTextW = valueStr.length * charW;
    const chipH = fontSize + 8;
    const chipW = chipTextW + chipPadX * 2;

    return (
      <g
        key={`${id}-dot-${index}`}
        transform={`translate(${cx}, ${cy})`}
        style={{ cursor: "pointer" }}
      >
        <g
          style={{
            transform: `scale(1)`,
            transformBox: "fill-box",
            transformOrigin: "50% 50%",
            transition: "transform 160ms ease",
          }}
        >
          {/* Continuous soft pulse halo */}
          <circle
            r={haloR}
            className="animate-ping"
            fill={color}
            opacity={0.075}
          />
          {/* Solid chip behind logo */}
          <circle
            r={Math.round(size * 0.55)}
            fill={bg as any}
            stroke={ring as any}
            strokeWidth={1}
          />
          {icon ? (
            <image
              href={icon}
              x={-size / 2}
              y={-size / 2}
              width={size}
              height={size}
              preserveAspectRatio="xMidYMid meet"
              style={{
                filter: "drop-shadow(0 0 2px rgba(0,0,0,0.6))",
                pointerEvents: "none",
              }}
            />
          ) : (
            <circle r={Math.max(6, Math.round(size * 0.38))} fill={color} />
          )}
        </g>
        {/* Right value chip */}
        {showValueChip && (
          <g
            key={`chip-${id}-${valueStr}`}
            transform={`translate(${Math.round(size * 0.7) + 8}, ${-Math.round(chipH / 2)})`}
            style={{ pointerEvents: "none" }}
          >
            <rect
              rx={6}
              ry={6}
              width={chipW}
              height={chipH}
              fill={color}
              opacity={0.9}
            />
            <text
              x={chipW / 2}
              y={Math.round(chipH * 0.68)}
              textAnchor="middle"
              fontSize={fontSize}
              className="tabular-nums"
              fill="#fff"
              fontWeight={700}
            >
              {valueStr}
            </text>
          </g>
        )}
      </g>
    );
  };

  return (
    <div
      className="flex h-full flex-col rounded-md border p-3"
      style={{
        background: "var(--panel-bg)",
        borderColor: "var(--panel-border)",
      }}
    >
      {/* Header */}
      <div className="mb-2 flex items-center justify-between">
        <div
          className="text-xs font-semibold tracking-wider"
          style={{ color: "var(--muted-text)" }}
        >
          {tCharts?.accountValue ?? tLeaderboard.accountValue}
        </div>
        <div className="hidden sm:flex items-center gap-2 text-[11px]">
          {/* Range Toggle */}
          <div
            className="flex overflow-hidden rounded border"
            style={{ borderColor: "var(--chip-border)" }}
          >
            {(["ALL", "72H"] as Range[]).map((r) => (
              <button
                key={r}
                className="px-2 py-1 chip-btn"
                style={
                  range === r
                    ? {
                        background: "var(--btn-active-bg)",
                        color: "var(--btn-active-fg)",
                      }
                    : { color: "var(--btn-inactive-fg)" }
                }
                onClick={() => setRange(r)}
              >
                {r}
              </button>
            ))}
          </div>
          {/* Mode Toggle */}
          <div
            className="flex overflow-hidden rounded border"
            style={{ borderColor: "var(--chip-border)" }}
          >
            {(["$", "%"] as Mode[]).map((m) => (
              <button
                key={m}
                className="px-2 py-1 chip-btn"
                style={
                  mode === m
                    ? {
                        background: "var(--btn-active-bg)",
                        color: "var(--btn-active-fg)",
                      }
                    : { color: "var(--btn-inactive-fg)" }
                }
                onClick={() => setMode(m)}
              >
                {m}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="w-full flex-1 min-h-0 flex flex-col">
        <div className="min-h-0 flex-1">
          <div className="chart-container relative h-full w-full no-tap-highlight select-none">
            {displayData.length === 0 ? (
              <div className="flex h-full items-center justify-center" style={{ color: "var(--muted-text)" }}>
                <div className="text-center">
                  <div className="text-2xl mb-2">📈</div>
                  <p className="text-sm">{tCharts.noEquityData}</p>
                  <p className="text-xs mt-1">{tCharts.tradingNotStarted}</p>
                </div>
              </div>
            ) : (
              <ResponsiveContainer>
                <LineChart 
                  data={displayData} 
                  margin={{ 
                    top: 8, 
                    right: (() => {
                      // Increase right margin if value chip could overflow
                      const visibleIds = runningAgentIds.filter((id) =>
                        active.size ? active.has(id) : true
                      );
                      let maxW = 0;
                      for (const id of visibleIds) {
                        const s = formatValue(lastValById[id]);
                        const fs = vw < 380 ? 11 : vw < 640 ? 12 : 13;
                        const cW = Math.round(fs * 0.62);
                        const est = s.length * cW + 16 + Math.round(endLogoSize * 0.7) + 10;
                        if (est > maxW) maxW = est;
                      }
                      return Math.max(chartRightMargin, maxW);
                    })(),
                    bottom: 8, 
                    left: 0 
                  }}
                >
                <CartesianGrid stroke="var(--grid-stroke)" strokeDasharray="3 3" />
                <XAxis
                  dataKey="timestamp"
                  tickFormatter={(v: Date) => format(v, "MM-dd HH:mm")}
                  tick={{ fill: "var(--axis-tick)", fontSize: 11 }}
                />
                <YAxis
                  tickFormatter={formatYAxisTick}
                  tick={{ fill: "var(--axis-tick)", fontSize: 11 }}
                  width={60}
                  domain={yAxisDomain}
                />
                <Tooltip
                  contentStyle={{
                    background: "var(--tooltip-bg)",
                    border: "1px solid var(--tooltip-border)",
                    color: "var(--tooltip-fg)",
                  }}
                  labelFormatter={(v) => format(new Date(v), "yyyy-MM-dd HH:mm")}
                  formatter={(val: number) =>
                    mode === "%" ? `${Number(val).toFixed(2)}%` : `$${Number(val).toFixed(2)}`
                  }
                />
                <ReferenceLine
                  y={mode === "$" ? 10000 : 0}
                  stroke="var(--ref-line)"
                  strokeDasharray="4 4"
                />
                {runningAgentIds.map((id) => {
                  // Get model_id from agent to find correct color
                  const agent = runningAgents.find(a => a.id === id);
                  const color = getAgentModelColor(agent);
                  const agentName = agent?.name || id;
                  
                  return (
                    <Line
                      key={id}
                      type="monotone"
                      dataKey={id}
                      stroke={color}
                      strokeWidth={2.5}
                      dot={renderEndDot(id)}
                      name={agentName}
                      hide={active.size > 0 && !active.has(id)}
                      connectNulls
                      className="series"
                    />
                  );
                })}
              </LineChart>
            </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Legend - Show only running agents */}
        {runningAgents.length > 0 && (
          <div className="mt-3">
            {/* Small screens: horizontal scrollable legend */}
            <div className="block md:hidden">
              <div
                className="flex flex-nowrap gap-2 overflow-x-auto whitespace-nowrap pr-1"
                style={{ WebkitOverflowScrolling: "touch" }}
              >
                {runningAgents.map((agent) => {
                  const activeOn = active.size === 0 || active.has(agent.id);
                  // Use model_id to get correct icon and color
                  const icon = getAgentModelIcon(agent);
                  const displayColor = getAgentModelColor(agent);
                  
                  return (
                    <button
                      key={agent.id}
                      className="inline-flex min-w-[110px] flex-shrink-0 flex-col items-center justify-center gap-1 rounded border px-2 py-2 text-[11px] chip-btn"
                      style={{
                        borderColor: "var(--chip-border)",
                        background: activeOn ? "var(--btn-active-bg)" : "transparent",
                        color: activeOn ? "var(--btn-active-fg)" : "var(--btn-inactive-fg)",
                        cursor: "pointer",
                      }}
                      onClick={() => {
                        setActive((prev) => {
                          if (prev.size === 1 && prev.has(agent.id)) return new Set(runningAgentIds);
                          return new Set([agent.id]);
                        });
                      }}
                    >
                      <div className="flex flex-col items-center gap-0.5 w-full">
                        <div className="flex items-center gap-1">
                          {icon ? (
                            <span
                              className="inline-flex h-3.5 w-3.5 items-center justify-center rounded-full flex-shrink-0"
                              style={{
                                background: displayColor,
                                padding: '2px',
                              }}
                            >
                              <img
                                src={icon}
                                alt=""
                                className="h-full w-full object-contain"
                              />
                            </span>
                          ) : (
                            <span
                              className="inline-block h-2.5 w-2.5 rounded-full flex-shrink-0"
                              style={{ background: displayColor }}
                            />
                          )}
                          <span className="px-1 py-0.5 rounded text-[8px] font-semibold leading-none" style={{ background: "#10b981", color: "#fff" }}>
                            LIVE
                          </span>
                        </div>
                        <span className="text-[9px] text-center leading-tight max-w-full break-words px-1" style={{ wordBreak: "break-word" }}>
                          {agent.name}
                        </span>
                      </div>
                      <div className="font-semibold leading-tight tabular-nums text-[11px] mt-0.5">
                        {formatValue(lastValById[agent.id])}
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Desktop: equal-width grid legend */}
            <div className="hidden md:grid gap-2" style={{ gridTemplateColumns: `repeat(${runningAgents.length}, minmax(0, 1fr))` }}>
              {runningAgents.map((agent) => {
                const activeOn = active.size === 0 || active.has(agent.id);
                // Use model_id to get correct icon and color
                const modelId = agent.model_id || agent.id;
                const icon = getAgentModelIcon(agent);
                const displayColor = getAgentModelColor(agent);
                
                return (
                  <button
                    key={agent.id}
                    className="w-full inline-flex flex-col items-center justify-center gap-1 rounded border px-2 py-2 text-[11px] chip-btn"
                    style={{
                      borderColor: "var(--chip-border)",
                      background: activeOn ? "var(--btn-active-bg)" : "transparent",
                      color: activeOn ? "var(--btn-active-fg)" : "var(--btn-inactive-fg)",
                      cursor: "pointer",
                    }}
                    onClick={() => {
                      setActive((prev) => {
                        if (prev.size === 1 && prev.has(agent.id)) return new Set(runningAgentIds);
                        return new Set([agent.id]);
                      });
                    }}
                  >
                    <div className="flex flex-col items-center gap-0.5 w-full">
                      <div className="flex items-center gap-1">
                        {icon ? (
                          <span
                            className="inline-flex h-3.5 w-3.5 items-center justify-center rounded-full flex-shrink-0"
                            style={{
                              background: displayColor,
                              padding: '2px',
                            }}
                          >
                            <img
                              src={icon}
                              alt=""
                              className="h-full w-full object-contain"
                            />
                          </span>
                        ) : (
                          <span
                            className="inline-block h-2.5 w-2.5 rounded-full flex-shrink-0"
                            style={{ background: displayColor }}
                          />
                        )}
                        <span className="px-1 py-0.5 rounded text-[8px] font-semibold leading-none" style={{ background: "#10b981", color: "#fff" }}>
                          LIVE
                        </span>
                      </div>
                      <span className="text-[9px] text-center leading-tight max-w-full break-words px-1" style={{ wordBreak: "break-word" }}>
                        {agent.name}
                      </span>
                    </div>
                    <div className="font-semibold leading-tight tabular-nums text-[11px] mt-0.5">
                      {formatValue(lastValById[agent.id])}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default AccountValueChart;
