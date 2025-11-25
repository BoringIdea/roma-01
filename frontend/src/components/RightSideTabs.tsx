"use client";

import React, { useState, useMemo } from "react";
import Link from "next/link";
import useSWR from "swr";
import { api } from "@/lib/api";
import type { Agent, Position } from "@/types";
import { fmtUSD, fmtPercent } from "@/lib/utils/formatters";
import { getAgentModelColor, getAgentModelName } from "@/lib/model/meta";
import { getCoinIcon } from "@/lib/utils/coinIcons";
import { useLanguage } from "@/store/useLanguage";
import { getTranslation } from "@/lib/i18n";

interface RightSideTabsProps {
  agents: Agent[];
}

type TabType = "positions" | "trades" | "decisions" | "prompts" | "chat";

export function RightSideTabs({ agents }: RightSideTabsProps) {
  const language = useLanguage((s) => s.language);
  const t = getTranslation(language).tabs;
  
  const [activeTab, setActiveTab] = useState<TabType>("positions");
  const [filterAgent, setFilterAgent] = useState<string>("all");
  const [filterDex, setFilterDex] = useState<string>("all");
  const [filterAccount, setFilterAccount] = useState<string>("all");
  
  // Get unique DEX types and account IDs from agents
  const dexTypes = useMemo(() => {
    const types = new Set<string>();
    agents.forEach(a => {
      if (a.dex_type) types.add(a.dex_type);
    });
    return Array.from(types).sort();
  }, [agents]);
  
  const accountIds = useMemo(() => {
    const accounts = new Set<string>();
    agents.forEach(a => {
      if (a.account_id) accounts.add(a.account_id);
    });
    return Array.from(accounts).sort();
  }, [agents]);

  return (
    <div
      className="flex h-full flex-col rounded-md border p-3"
      style={{
        background: "var(--panel-bg)",
        borderColor: "var(--panel-border)",
      }}
    >
      {/* Tabs Header */}
      <div className="mb-3 flex items-center gap-2 text-[11px]">
        <div
          className="flex overflow-hidden rounded border"
          style={{ borderColor: "var(--chip-border)" }}
        >
          {(["positions", "trades", "decisions", "prompts", "chat"] as TabType[]).map((tab) => (
            <button
              key={tab}
              className="px-3 py-1.5 chip-btn uppercase"
              style={
                activeTab === tab
                  ? {
                      background: "var(--btn-active-bg)",
                      color: "var(--btn-active-fg)",
                    }
                  : { color: "var(--btn-inactive-fg)" }
              }
              onClick={() => setActiveTab(tab)}
            >
              {t[tab]}
            </button>
          ))}
        </div>
      </div>

      {/* Filters - Only show for non-prompts and non-chat tabs */}
      {activeTab !== "prompts" && activeTab !== "chat" && (
        <div className="mb-3 space-y-2">
          {/* DEX Filter */}
          {dexTypes.length > 1 && (
            <div>
              <label
                className="text-xs mb-1 block tracking-wider"
                style={{ color: "var(--muted-text)" }}
              >
                {t.filterDex}
              </label>
              <select
                value={filterDex}
                onChange={(e) => setFilterDex(e.target.value)}
                className="w-full px-2 py-1.5 rounded border text-xs chip-btn"
                style={{
                  background: "var(--panel-bg)",
                  borderColor: "var(--chip-border)",
                  color: "var(--foreground)",
                }}
              >
                <option value="all">{t.allDex}</option>
                {dexTypes.map((dex) => (
                  <option key={dex} value={dex}>
                    {dex === "aster" ? t.aster : dex === "hyperliquid" ? t.hyperliquid : dex}
                  </option>
                ))}
              </select>
            </div>
          )}
          
          {/* Account Filter */}
          {accountIds.length > 1 && (
            <div>
              <label
                className="text-xs mb-1 block tracking-wider"
                style={{ color: "var(--muted-text)" }}
              >
                {t.filterAccount}
              </label>
              <select
                value={filterAccount}
                onChange={(e) => setFilterAccount(e.target.value)}
                className="w-full px-2 py-1.5 rounded border text-xs chip-btn"
                style={{
                  background: "var(--panel-bg)",
                  borderColor: "var(--chip-border)",
                  color: "var(--foreground)",
                }}
              >
                <option value="all">{t.allAccounts}</option>
                {accountIds.map((accountId) => (
                  <option key={accountId} value={accountId}>
                    {accountId}
                  </option>
                ))}
              </select>
            </div>
          )}
          
          {/* Agent Filter */}
          <div>
            <label
              className="text-xs mb-1 block tracking-wider"
              style={{ color: "var(--muted-text)" }}
            >
              {t.filter}
            </label>
            <select
              value={filterAgent}
              onChange={(e) => setFilterAgent(e.target.value)}
              className="w-full px-2 py-1.5 rounded border text-xs chip-btn"
              style={{
                background: "var(--panel-bg)",
                borderColor: "var(--chip-border)",
                color: "var(--foreground)",
              }}
            >
              <option value="all">{t.allAgents}</option>
              {agents.map((agent) => (
                <option key={agent.id} value={agent.id}>
                  {agent.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      )}

      {/* Agent Selector - Only for prompts tab */}
      {activeTab === "prompts" && (
        <div className="mb-3">
          <label
            className="text-xs mb-1 block tracking-wider"
            style={{ color: "var(--muted-text)" }}
          >
            {t.selectAgent}
          </label>
          <select
            value={filterAgent}
            onChange={(e) => setFilterAgent(e.target.value)}
            className="w-full px-2 py-1.5 rounded border text-xs chip-btn"
            style={{
              background: "var(--panel-bg)",
              borderColor: "var(--chip-border)",
              color: "var(--foreground)",
            }}
          >
            {agents.filter(a => a.is_running).map((agent) => (
              <option key={agent.id} value={agent.id}>
                {agent.name}
              </option>
            ))}
          </select>
        </div>
      )}

          {/* Content */}
          <div className="flex-1 overflow-y-auto">
            {activeTab === "positions" ? (
              <PositionsContent agents={agents} filterAgent={filterAgent} filterDex={filterDex} filterAccount={filterAccount} />
            ) : activeTab === "trades" ? (
              <TradesContent agents={agents} filterAgent={filterAgent} filterDex={filterDex} filterAccount={filterAccount} />
            ) : activeTab === "decisions" ? (
              <DecisionsContent agents={agents} filterAgent={filterAgent} filterDex={filterDex} filterAccount={filterAccount} />
            ) : activeTab === "prompts" ? (
              <PromptsContent agents={agents} filterAgent={filterAgent} />
            ) : (
              <ChatContent />
            )}
          </div>
    </div>
  );
}

function PositionsContent({
  agents,
  filterAgent,
  filterDex,
  filterAccount,
}: {
  agents: Agent[];
  filterAgent: string;
  filterDex: string;
  filterAccount: string;
}) {
  // Only show running agents
  const runningAgents = agents.filter(a => a.is_running);
  
  // Apply filters
  let filteredAgents = runningAgents;
  
  // Filter by DEX
  if (filterDex !== "all") {
    filteredAgents = filteredAgents.filter(a => a.dex_type === filterDex);
  }
  
  // Filter by account
  if (filterAccount !== "all") {
    filteredAgents = filteredAgents.filter(a => a.account_id === filterAccount);
  }
  
  // Filter by agent
  if (filterAgent !== "all") {
    filteredAgents = filteredAgents.filter((a) => a.id === filterAgent);
  }

  // Fetch positions for filtered agents
  const visibleAgentKey = useMemo(
    () =>
      filteredAgents
        .map((agent) => agent.id)
        .sort()
        .join(","),
    [filteredAgents],
  );

  const { data: positionsMap } = useSWR(
    visibleAgentKey ? ["agent-positions", visibleAgentKey] : null,
    async ([, key]) => {
      const ids = key.split(",").filter(Boolean);
      if (ids.length === 0) {
        return new Map<string, Position[]>();
      }
      const results = await Promise.all(
        ids.map(async (id) => {
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
    { refreshInterval: 10000 },
  );

  const positionsData = filteredAgents.map((agent) => ({
    agent,
    positions: positionsMap?.get(agent.id) ?? [],
  }));

  // Calculate total positions
  const totalPositions = positionsData.reduce((sum, d) => sum + d.positions.length, 0);

  if (totalPositions === 0) {
    return (
      <div className="text-center py-12" style={{ color: "var(--muted-text)" }}>
        <div className="text-4xl mb-2 opacity-50">📊</div>
        <p className="text-sm">No active positions</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Total count */}
      <p className="text-xs" style={{ color: "var(--muted-text)" }}>
        {totalPositions} Position{totalPositions > 1 ? "s" : ""}
      </p>

      {/* Each Agent as a Card */}
      {positionsData.map(({ agent, positions }) => {
        if (positions.length === 0) return null;

        // Calculate total PnL for this agent
        const totalPnL = positions.reduce((sum, p) => sum + (p.unrealized_profit || 0), 0);
        
        // Get model color
        const color = getAgentModelColor(agent);
        const brandBg = `linear-gradient(0deg, ${color}10, var(--panel-bg))`;
        const brandBorder = `${color}55`;

        return (
          <div 
            key={agent.id} 
            className="rounded-md border p-3"
            style={{
              background: brandBg as any,
              borderColor: brandBorder as any,
            }}
          >
            {/* Model Header */}
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <span 
                  className="text-xs font-semibold uppercase tracking-wider" 
                  style={{ color: "var(--foreground)" }}
                >
                  {getAgentModelName(agent) || agent.name || agent.id}
                </span>
                <span 
                  className="text-[10px] px-1.5 py-0.5 rounded" 
                  style={{ 
                    background: "rgba(0, 0, 0, 0.2)",
                    color: "var(--muted-text)" 
                  }}
                >
                  {positions.length}
                </span>
              </div>
              <div
                className="text-xs font-bold tabular-nums"
                style={{ color: totalPnL >= 0 ? "#22c55e" : "#ef4444" }}
              >
                {totalPnL >= 0 ? "+" : ""}{fmtUSD(totalPnL)}
              </div>
            </div>

            {/* Positions Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-left text-[11px] terminal-text">
                <thead style={{ color: "var(--muted-text)" }}>
                  <tr className="border-b" style={{ borderColor: "var(--panel-border)" }}>
                    <th className="py-1.5 pr-2 font-normal">Symbol</th>
                    <th className="py-1.5 pr-2 font-normal">Side</th>
                    <th className="py-1.5 pr-2 font-normal">Lev</th>
                    <th className="py-1.5 pr-2 font-normal">Entry</th>
                    <th className="py-1.5 pr-2 font-normal">Mark</th>
                    <th className="py-1.5 pr-2 font-normal text-right">PnL</th>
                  </tr>
                </thead>
                <tbody style={{ color: "var(--foreground)" }}>
                  {positions.map((position, index) => {
                    const rawDenominator = position.entry_price * (position.position_amt || 0);
                    const pnlPct =
                      rawDenominator === 0
                        ? 0
                        : (position.unrealized_profit / rawDenominator) * 100;
                    const safePct = Number.isFinite(pnlPct) ? pnlPct : 0;

                    return (
                      <tr 
                        key={`${agent.id}-${position.symbol}-${index}`}
                        className="border-b"
                        style={{ 
                          borderColor: "color-mix(in oklab, var(--panel-border) 30%, transparent)" 
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
                          style={{ 
                            color: position.side === "long" ? "#22c55e" : "#ef4444" 
                          }}
                        >
                          {position.side.toUpperCase()}
                        </td>
                        <td className="py-1.5 pr-2">
                          <span style={{ color: "var(--brand-accent)" }}>
                            {position.leverage}x
                          </span>
                        </td>
                        <td className="py-1.5 pr-2 tabular-nums">
                          {fmtUSD(position.entry_price)}
                        </td>
                        <td className="py-1.5 pr-2 tabular-nums">
                          {fmtUSD(position.mark_price)}
                        </td>
                        <td 
                          className="py-1.5 pr-2 text-right"
                          style={{ 
                            color: position.unrealized_profit >= 0 ? "#22c55e" : "#ef4444" 
                          }}
                        >
                          <div className="font-bold tabular-nums">
                            {fmtUSD(position.unrealized_profit)}
                          </div>
                          <div className="text-[10px] tabular-nums">
                            {safePct >= 0 ? "+" : ""}
                            {safePct.toFixed(2)}%
                          </div>
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
    </div>
  );
}

function TradesContent({
  agents,
  filterAgent,
  filterDex,
  filterAccount,
}: {
  agents: Agent[];
  filterAgent: string;
  filterDex: string;
  filterAccount: string;
}) {
  // Only show running agents
  const runningAgents = agents.filter(a => a.is_running);
  
  // Apply filters
  let filteredAgents = runningAgents;
  
  // Filter by DEX
  if (filterDex !== "all") {
    filteredAgents = filteredAgents.filter(a => a.dex_type === filterDex);
  }
  
  // Filter by account
  if (filterAccount !== "all") {
    filteredAgents = filteredAgents.filter(a => a.account_id === filterAccount);
  }
  
  // Filter by agent
  if (filterAgent !== "all") {
    filteredAgents = filteredAgents.filter((a) => a.id === filterAgent);
  }

  // Fetch trades for filtered agents
  const tradesDataQueries = filteredAgents.map((agent) => {
    // eslint-disable-next-line react-hooks/rules-of-hooks
    const { data } = useSWR(`/agent/${agent.id}/trades`, () =>
      api.getTrades(agent.id), { refreshInterval: 30000 }
    );
    return { agent, trades: data || [] };
  });

  const allTrades = tradesDataQueries.flatMap((d) =>
    d.trades.map((t: any) => ({ ...t, agentName: d.agent.name, agentId: d.agent.id }))
  );

  // Sort by close time (most recent first)
  allTrades.sort((a, b) => {
    const timeA = new Date(a.close_time).getTime();
    const timeB = new Date(b.close_time).getTime();
    return timeB - timeA;
  });

  if (allTrades.length === 0) {
    return (
      <div className="text-center py-12" style={{ color: "var(--muted-text)" }}>
        <div className="text-4xl mb-2 opacity-50">📜</div>
        <p className="text-sm">No completed trades yet</p>
        <p className="text-xs mt-1">Trades will appear after positions are closed</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <p className="text-xs mb-2" style={{ color: "var(--muted-text)" }}>
        {allTrades.length} Trade{allTrades.length > 1 ? "s" : ""}
      </p>
      {allTrades.slice(0, 20).map((trade: any, index: number) => {
        const pnl = trade.pnl_usdt || 0;
        const pnlPct = trade.pnl_pct || 0;
        const isProfit = pnl >= 0;

        return (
          <div
            key={`${trade.agentId}-${trade.symbol}-${index}`}
            className="rounded border p-2.5 transition-colors hover:bg-opacity-50"
            style={{
              borderColor: "var(--chip-border)",
              background: "rgba(255, 255, 255, 0.02)",
            }}
          >
            {/* Header */}
            <div className="flex items-center justify-between mb-2">
              <div className="flex-1">
                <div className="flex items-center gap-1.5 mb-0.5">
                  {getCoinIcon(trade.symbol) && (
                    <img
                      src={getCoinIcon(trade.symbol)}
                      alt={trade.symbol}
                      className="w-4 h-4"
                    />
                  )}
                  <span className="font-bold terminal-text text-sm" style={{ color: "var(--foreground)" }}>
                    {trade.symbol}
                  </span>
                  <span
                    className="px-1.5 py-0.5 rounded text-[10px] font-bold uppercase"
                    style={{
                      background: trade.side === "long" ? "rgba(34, 197, 94, 0.15)" : "rgba(239, 68, 68, 0.15)",
                      color: trade.side === "long" ? "#22c55e" : "#ef4444",
                    }}
                  >
                    {trade.side}
                  </span>
                </div>
                <p className="text-[10px]" style={{ color: "var(--muted-text)" }}>
                  {trade.agentName}
                </p>
              </div>
              <div className="text-right">
                <div
                  className="text-sm font-bold tabular-nums"
                  style={{ color: isProfit ? "#22c55e" : "#ef4444" }}
                >
                  {isProfit ? "+" : ""}{fmtUSD(pnl)}
                </div>
                <div
                  className="text-[10px] tabular-nums"
                  style={{ color: isProfit ? "#22c55e" : "#ef4444" }}
                >
                  {isProfit ? "+" : ""}{pnlPct.toFixed(2)}%
                </div>
              </div>
            </div>

            {/* Trade Details */}
            <div className="grid grid-cols-2 gap-x-2 gap-y-1 text-[11px]">
              <div>
                <span style={{ color: "var(--muted-text)" }}>Entry:</span>
                <span className="ml-1 tabular-nums" style={{ color: "var(--foreground)" }}>
                  {fmtUSD(trade.entry_price)}
                </span>
              </div>
              <div>
                <span style={{ color: "var(--muted-text)" }}>Exit:</span>
                <span className="ml-1 tabular-nums" style={{ color: "var(--foreground)" }}>
                  {fmtUSD(trade.close_price)}
                </span>
              </div>
              <div>
                <span style={{ color: "var(--muted-text)" }}>Qty:</span>
                <span className="ml-1 tabular-nums" style={{ color: "var(--foreground)" }}>
                  {trade.quantity?.toFixed(4)}
                </span>
              </div>
              <div>
                <span style={{ color: "var(--muted-text)" }}>Lev:</span>
                <span className="ml-1 font-bold" style={{ color: "var(--brand-accent)" }}>
                  {trade.leverage}x
                </span>
              </div>
            </div>

            {/* Time */}
            <div className="mt-1.5 pt-1.5 border-t text-[10px]" style={{ borderColor: "var(--panel-border)" }}>
              <span style={{ color: "var(--muted-text)" }}>
                Closed: {new Date(trade.close_time).toLocaleString()}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function DecisionsContent({
  agents,
  filterAgent,
  filterDex,
  filterAccount,
}: {
  agents: Agent[];
  filterAgent: string;
  filterDex: string;
  filterAccount: string;
}) {
  const [expandedDecisions, setExpandedDecisions] = useState<Set<string>>(new Set());

  // Only show running agents
  const runningAgents = agents.filter(a => a.is_running);
  
  // Apply filters
  let filteredAgents = runningAgents;
  
  // Filter by DEX
  if (filterDex !== "all") {
    filteredAgents = filteredAgents.filter(a => a.dex_type === filterDex);
  }
  
  // Filter by account
  if (filterAccount !== "all") {
    filteredAgents = filteredAgents.filter(a => a.account_id === filterAccount);
  }
  
  // Filter by agent
  if (filterAgent !== "all") {
    filteredAgents = filteredAgents.filter((a) => a.id === filterAgent);
  }

  // Fetch decisions for filtered agents
  const decisionsDataQueries = filteredAgents.map((agent) => {
    // eslint-disable-next-line react-hooks/rules-of-hooks
    const { data } = useSWR(`/agent/${agent.id}/decisions`, () =>
      api.getDecisions(agent.id, 10), { refreshInterval: 10000 }
    );
    return { agent, decisions: data || [] };
  });

  const allDecisions = decisionsDataQueries.flatMap((d) =>
    d.decisions.map((dec: any) => ({ ...dec, agentName: d.agent.name, agentId: d.agent.id }))
  );

  // Sort by cycle_number (higher number = more recent)
  allDecisions.sort((a, b) => {
    const cycleA = a.cycle_number || 0;
    const cycleB = b.cycle_number || 0;
    return cycleB - cycleA;
  });

  const toggleExpanded = (key: string) => {
    setExpandedDecisions(prev => {
      const newSet = new Set(prev);
      if (newSet.has(key)) {
        newSet.delete(key);
      } else {
        newSet.add(key);
      }
      return newSet;
    });
  };

  if (allDecisions.length === 0) {
    return (
      <div className="text-center py-12" style={{ color: "var(--muted-text)" }}>
        <div className="text-4xl mb-2 opacity-50">🤖</div>
        <p className="text-sm">No decisions yet</p>
        <p className="text-xs mt-1">AI decisions will appear here</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <p className="text-xs mb-2" style={{ color: "var(--muted-text)" }}>
        {allDecisions.length} Decision{allDecisions.length > 1 ? "s" : ""}
      </p>
      {allDecisions.slice(0, 15).map((decision: any, index: number) => {
        const agentMeta = filteredAgents.find(a => a.id === decision.agentId);
        const color = getAgentModelColor(agentMeta);
        const brandBg = `linear-gradient(0deg, ${color}10, var(--panel-bg))`;
        const brandBorder = `${color}55`;
        const decisionKey = `${decision.agentId}-${decision.cycle_number}`;
        const isExpanded = expandedDecisions.has(decisionKey);

        return (
          <div
            key={`${decision.agentId}-${decision.cycle_number}-${index}`}
            className="rounded border p-2.5 transition-colors"
            style={{
              borderColor: brandBorder,
              background: brandBg as any,
            }}
          >
            {/* Header */}
            <div className="flex items-center justify-between mb-2">
              <div className="flex-1">
                <div className="flex items-center gap-1.5 mb-0.5">
                  <span
                    className="text-xs font-bold px-1.5 py-0.5 rounded"
                    style={{
                      background: "rgba(0, 0, 0, 0.2)",
                      color: color,
                    }}
                  >
                    #{decision.cycle_number}
                  </span>
                  <span className="text-[10px]" style={{ color: "var(--muted-text)" }}>
                    {decision.agentName}
                  </span>
                </div>
                <p className="text-[10px]" style={{ color: "var(--muted-text)" }}>
                  {new Date(decision.timestamp).toLocaleString('en-US', {
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                    hour12: false
                  })}
                </p>
              </div>
              {decision.account_state && (
                <div className="text-right">
                  <div className="text-[10px]" style={{ color: "var(--muted-text)" }}>
                    Balance
                  </div>
                  <div
                    className="text-xs font-bold tabular-nums"
                    style={{ color: "var(--foreground)" }}
                  >
                    ${decision.account_state.total_wallet_balance.toFixed(2)}
                  </div>
                </div>
              )}
            </div>

            {/* Actions */}
            {decision.decisions && decision.decisions.length > 0 && (
              <div className="space-y-1 mb-2">
                {decision.decisions.map((dec: any, decIdx: number) => (
                  <div
                    key={decIdx}
                    className="flex items-center gap-1.5 text-[11px]"
                  >
                    <span
                      className="px-1.5 py-0.5 rounded font-bold uppercase text-[10px] flex-shrink-0"
                      style={{
                        background:
                          dec.action === "open_long"
                            ? "rgba(34, 197, 94, 0.15)"
                            : dec.action === "open_short"
                            ? "rgba(239, 68, 68, 0.15)"
                            : dec.action === "close_position"
                            ? "rgba(245, 158, 11, 0.15)"
                            : "rgba(100, 116, 139, 0.15)",
                        color:
                          dec.action === "open_long"
                            ? "#22c55e"
                            : dec.action === "open_short"
                            ? "#ef4444"
                            : dec.action === "close_position"
                            ? "#f59e0b"
                            : "var(--muted-text)",
                      }}
                    >
                      {dec.action.replace("_", " ")}
                    </span>
                    {dec.symbol && (
                      <div className="flex items-center gap-1">
                        {getCoinIcon(dec.symbol) && (
                          <img
                            src={getCoinIcon(dec.symbol)}
                            alt={dec.symbol}
                            className="w-3 h-3"
                          />
                        )}
                        <span
                          className="font-bold"
                          style={{ color: "var(--foreground)" }}
                        >
                          {dec.symbol}
                        </span>
                      </div>
                    )}
                    {dec.leverage && (
                      <span style={{ color: "var(--brand-accent)" }}>
                        {dec.leverage}x
                      </span>
                    )}
                    {dec.position_size_usd && (
                      <span style={{ color: "var(--muted-text)" }}>
                        ${dec.position_size_usd.toFixed(0)}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Chain of Thought */}
            {decision.chain_of_thought && (
              <div className="relative">
                <div
                  className={`text-[11px] leading-relaxed terminal-text whitespace-pre-wrap ${
                    isExpanded ? "" : "line-clamp-3"
                  }`}
                  style={{
                    color: "var(--muted-text)",
                    ...(!isExpanded && {
                      display: "-webkit-box",
                      WebkitLineClamp: 3,
                      WebkitBoxOrient: "vertical",
                      overflow: "hidden",
                    }),
                  }}
                >
                  {decision.chain_of_thought}
                </div>
                {decision.chain_of_thought.length > 150 && (
                  <button
                    onClick={() => toggleExpanded(decisionKey)}
                    className="text-[10px] mt-1 italic hover:underline"
                    style={{ color: "var(--brand-accent)" }}
                  >
                    {isExpanded ? "Show less" : "Show more"}
                  </button>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function PromptsContent({
  agents,
  filterAgent,
}: {
  agents: Agent[];
  filterAgent: string;
}) {
  const language = useLanguage((s) => s.language);
  const t = getTranslation(language).prompts;
  
  // Get the selected agent or first running agent
  const selectedAgentId = filterAgent !== "all" 
    ? filterAgent 
    : agents.find(a => a.is_running)?.id;

  const { data: systemPrompt, isLoading, error } = useSWR(
    selectedAgentId ? ["system-prompt-preview", selectedAgentId, language] : null,
    ([, agentId, lang]) => api.getSystemPromptPreview(agentId, lang),
    {
      revalidateOnFocus: false,
    }
  );

  if (!selectedAgentId) {
    return (
      <div className="flex items-center justify-center h-full" style={{ color: "var(--muted-text)" }}>
        <div className="text-xs text-center">
          <div className="mb-2">{t.noRunningAgents}</div>
          <div className="text-[10px]">{t.startAgentPrompt}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col gap-3">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--foreground)" }}>
            {language === "zh" ? "提示词" : "Prompts"}
          </div>
          <div className="text-[10px]" style={{ color: "var(--muted-text)" }}>
            {language === "zh"
              ? "提示词编辑已迁移至 Settings 页面，以下为只读预览。"
              : "Prompt editing has moved to Settings. Preview below is read-only."}
          </div>
        </div>
        <Link
          href="/settings"
          className="text-[10px] uppercase tracking-widest font-semibold px-3 py-1 rounded border transition-all hover:opacity-80"
          style={{
            borderColor: "var(--panel-border)",
            color: "var(--brand-accent)",
          }}
        >
          {language === "zh" ? "前往设置" : "Open Settings"}
        </Link>
      </div>

      <div
        className="flex-1 overflow-y-auto rounded border p-3"
        style={{
          borderColor: "var(--panel-border)",
          background: "var(--panel-bg)",
          color: "var(--muted-text)",
        }}
      >
        {isLoading && (
          <div className="text-[11px]" style={{ color: "var(--muted-text)" }}>
            {language === "zh" ? "加载提示词..." : "Loading prompt..."}
          </div>
        )}
        {error && (
          <div className="text-[11px] text-red-500">
            {language === "zh" ? "加载提示词失败" : "Failed to load prompt preview"}
          </div>
        )}
        {!isLoading && !error && (
          <pre className="text-[11px] leading-relaxed whitespace-pre-wrap font-mono">
            {systemPrompt || (language === "zh" ? "暂无提示词预览" : "No prompt preview available")}
          </pre>
        )}
      </div>
    </div>
  );
}

function ChatContent() {
  const language = useLanguage((s) => s.language);
  const t = getTranslation(language).chat;
  const [messages, setMessages] = useState<Array<{ role: "user" | "assistant"; content: string; timestamp: Date }>>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMessage, timestamp: new Date() }]);
    setIsLoading(true);

    try {
      const response = await api.chat(userMessage, language);
      setMessages((prev) => [...prev, { role: "assistant", content: response.message, timestamp: new Date() }]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: t.errorMessage || "Failed to get response. Please try again.",
          timestamp: new Date(),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto mb-3 space-y-3">
        {messages.length === 0 ? (
          <div className="text-center py-12" style={{ color: "var(--muted-text)" }}>
            <div className="text-4xl mb-2 opacity-50">💬</div>
            <p className="text-sm mb-2">{t.welcome}</p>
            <p className="text-xs">{t.exampleQuestions}</p>
            <div className="mt-4 space-y-2 text-left max-w-md mx-auto">
              <button
                onClick={() => setInput(t.example1 || "What are some basic trading prompt suggestions?")}
                className="w-full text-left px-3 py-2 rounded border text-xs hover:opacity-80 transition-opacity"
                style={{
                  background: "var(--panel-bg)",
                  borderColor: "var(--chip-border)",
                  color: "var(--foreground)",
                }}
              >
                {t.example1 || "What are some basic trading prompt suggestions?"}
              </button>
              <button
                onClick={() => setInput(t.example2 || "How does risk management work in this platform?")}
                className="w-full text-left px-3 py-2 rounded border text-xs hover:opacity-80 transition-opacity"
                style={{
                  background: "var(--panel-bg)",
                  borderColor: "var(--chip-border)",
                  color: "var(--foreground)",
                }}
              >
                {t.example2 || "How does risk management work in this platform?"}
              </button>
              <button
                onClick={() => setInput(t.example3 || "Analyze BTC")}
                className="w-full text-left px-3 py-2 rounded border text-xs hover:opacity-80 transition-opacity"
                style={{
                  background: "var(--panel-bg)",
                  borderColor: "var(--chip-border)",
                  color: "var(--foreground)",
                }}
              >
                {t.example3 || "Analyze BTC"}
              </button>
              <button
                onClick={() => setInput(t.example4 || "What should I do with ETH?")}
                className="w-full text-left px-3 py-2 rounded border text-xs hover:opacity-80 transition-opacity"
                style={{
                  background: "var(--panel-bg)",
                  borderColor: "var(--chip-border)",
                  color: "var(--foreground)",
                }}
              >
                {t.example4 || "What should I do with ETH?"}
              </button>
            </div>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[80%] rounded-lg px-3 py-2 text-xs ${
                  msg.role === "user"
                    ? "rounded-br-none"
                    : "rounded-bl-none"
                }`}
                style={{
                  background: msg.role === "user" ? "var(--brand-accent)" : "var(--panel-bg)",
                  borderColor: "var(--chip-border)",
                  borderWidth: "1px",
                  color: msg.role === "user" ? "#fff" : "var(--foreground)",
                }}
              >
                <div className="whitespace-pre-wrap terminal-text">{msg.content}</div>
                <div
                  className="text-[10px] mt-1 opacity-70"
                  style={{ color: msg.role === "user" ? "rgba(255,255,255,0.7)" : "var(--muted-text)" }}
                >
                  {msg.timestamp.toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))
        )}
        {isLoading && (
          <div className="flex justify-start">
            <div
              className="rounded-lg px-3 py-2 text-xs rounded-bl-none"
              style={{
                background: "var(--panel-bg)",
                borderColor: "var(--chip-border)",
                borderWidth: "1px",
                color: "var(--foreground)",
              }}
            >
              <div className="flex items-center gap-2">
                <div className="animate-pulse">●</div>
                <span>{t.thinking || "Thinking..."}</span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="flex gap-2">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder={t.placeholder || "Type your message..."}
          className="flex-1 px-3 py-2 rounded border text-xs resize-none"
          style={{
            background: "var(--panel-bg)",
            borderColor: "var(--chip-border)",
            color: "var(--foreground)",
          }}
          rows={2}
          disabled={isLoading}
        />
        <button
          onClick={handleSend}
          disabled={!input.trim() || isLoading}
          className="px-4 py-2 rounded chip-btn uppercase text-xs font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
          style={{
            background: input.trim() && !isLoading ? "var(--btn-active-bg)" : "var(--panel-bg)",
            color: input.trim() && !isLoading ? "var(--btn-active-fg)" : "var(--btn-inactive-fg)",
            borderColor: "var(--chip-border)",
            borderWidth: "1px",
          }}
        >
          {t.send || "Send"}
        </button>
      </div>
    </div>
  );
}


