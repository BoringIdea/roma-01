"use client";

import { useState, useMemo } from "react";
import useSWR from "swr";
import { api } from "@/lib/api";
import { getAgentModelColor } from "@/lib/model/meta";
import { fmtUSD } from "@/lib/utils/formatters";
import { getCoinIcon } from "@/lib/utils/coinIcons";
import LeaderboardTable from "./LeaderboardTable";
import { useLanguage } from "@/store/useLanguage";
import { getTranslation } from "@/lib/i18n";
import type { Agent } from "@/types";

export default function LeaderboardOverview() {
  const language = useLanguage((s) => s.language);
  const t = getTranslation(language).leaderboard;
  
  const [tab, setTab] = useState<"overall" | "advanced">("overall");
  
  // Fetch running agents from API
  const { data: runningAgents } = useSWR("/agents", api.getAgents, {
    refreshInterval: 10000,
  });

  // Use agents directly from API, no need to merge with predefined models
  const agents = useMemo<Agent[]>(() => {
    return (runningAgents || []).map((a): Agent => {
      const dexTypeRaw = (a.dex_type || "").toLowerCase();
      const dexTypeNorm: Agent["dex_type"] =
        dexTypeRaw === "hyperliquid"
          ? "hyperliquid"
          : dexTypeRaw === "aster"
          ? "aster"
          : undefined;

      return {
        id: a.id,
        name: a.name || a.id,
        is_running: a.is_running || false,
        cycle_count: a.cycle_count || 0,
        runtime_minutes: a.runtime_minutes || 0,
        // Multi-DEX fields from API
        dex_type: dexTypeNorm,
        account_id: a.account_id,
        model_id: a.model_id,
        model_provider: a.model_provider,
        model_config_id: a.model_config_id,
        llm_model: a.llm_model,
      };
    });
  }, [runningAgents]);

  // Fetch account data for all running agents using a single aggregated endpoint approach
  // We'll create a stable key for all running agents
  const runningAgentIds = useMemo(() => 
    agents.filter(a => a.is_running).map(a => a.id).sort().join(','), 
    [agents]
  );

  // Fetch all accounts data
  const { data: allAccountsData } = useSWR(
    runningAgentIds ? `/agents/accounts/${runningAgentIds}` : null,
    async () => {
      const ids = runningAgentIds.split(',');
      const results = await Promise.all(
        ids.map(async (id) => {
          try {
            const data = await api.getAccount(id);
            return { agentId: id, data };
          } catch (error) {
            console.error(`Failed to fetch account for ${id}:`, error);
            return { agentId: id, data: null };
          }
        })
      );
      return results;
    },
    { refreshInterval: 10000 }
  );

  // Get winning model (highest equity) and its equity value
  const { winningModel, winningEquity } = useMemo(() => {
    if (!allAccountsData || allAccountsData.length === 0) {
      return { winningModel: null as typeof agents[0] | null, winningEquity: 0 };
    }
    
    let maxEquity = -Infinity;
    let winner: typeof agents[0] | null = null;
    
    allAccountsData.forEach(({ agentId, data }) => {
      const equityValue = data?.adjusted_total_balance ?? data?.total_wallet_balance;
      if (equityValue && equityValue > maxEquity) {
        maxEquity = equityValue;
        winner = agents.find(a => a.id === agentId) || null;
      }
    });
    
    return { 
      winningModel: winner, 
      winningEquity: maxEquity > -Infinity ? maxEquity : 0 
    };
  }, [allAccountsData, agents]);

  // Fetch positions for the winning model
  const { data: winningPositions } = useSWR(
    winningModel ? `/agent/${winningModel.id}/positions` : null,
    winningModel ? () => api.getPositions(winningModel.id) : null,
    { refreshInterval: 10000 }
  );

  // Get active positions symbols from winning model
  const activeSymbols = useMemo(() => {
    if (!winningPositions || winningPositions.length === 0) {
      return [];
    }
    // Extract unique symbols from positions
    const symbols = new Set<string>();
    winningPositions.forEach((pos: any) => {
      if (pos.symbol) {
        symbols.add(pos.symbol);
      }
    });
    return Array.from(symbols);
  }, [winningPositions]);

  return (
    <div className="space-y-4">
      {/* Tab Controls */}
      <div className="flex items-center gap-3">
        <TabButton active={tab === "overall"} onClick={() => setTab("overall")}>
          {t.overallStats}
        </TabButton>
        <TabButton active={tab === "advanced"} onClick={() => setTab("advanced")}>
          {t.advancedAnalytics}
        </TabButton>
      </div>

      {/* Leaderboard Table */}
      <LeaderboardTable mode={tab} agents={agents || []} />

      {/* Summary Card */}
      <WinnerCard agent={winningModel} symbols={activeSymbols} />

      {/* Model Bars Chart */}
      {agents && agents.length > 0 && <ModelBarsChart agents={agents} />}
    </div>
  );
}

function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className="rounded border px-4 py-1.5 text-xs font-medium uppercase tracking-wider transition-all"
      style={{
        background: active ? "var(--panel-bg)" : "transparent",
        borderColor: active ? "var(--brand-accent)" : "var(--panel-border)",
        color: active ? "var(--foreground)" : "var(--muted-text)",
      }}
    >
      {children}
    </button>
  );
}

function WinnerCard({ agent, symbols }: { agent: any; symbols: string[] }) {
  const language = useLanguage((s) => s.language);
  const t = getTranslation(language).leaderboard;
  const { data: account } = useSWR(
    agent ? `/agent/${agent.id}/account` : null,
    agent ? () => api.getAccount(agent.id) : null,
    { refreshInterval: 10000 }
  );

  const color = agent ? getAgentModelColor(agent) : undefined;
  const equityRaw = account?.gross_total_balance ?? account?.total_wallet_balance ?? 0;
  const equityAdjusted = account?.adjusted_total_balance ?? equityRaw;
  const netDeposits = account?.net_deposits ?? 0;

  return (
    <div
      className="rounded-md border p-4"
      style={{
        background: agent ? `linear-gradient(0deg, ${color}10, var(--panel-bg))` : "var(--panel-bg)",
        borderColor: "var(--panel-border)",
      }}
    >
      <div className="text-xs uppercase tracking-wider mb-3" style={{ color: "var(--muted-text)" }}>
        {t.winningModel}
      </div>
      {agent ? (
        <div className="space-y-3">
          {/* Model Info */}
          <div className="flex items-center gap-3">
            <div 
              className="w-4 h-4 rounded-full"
              style={{ background: color }}
            />
            <div className="flex-1">
              <div className="text-base font-bold" style={{ color: "var(--foreground)" }}>
                {agent.name || agent.id}
              </div>
            </div>
          </div>

          {/* Total Equity */}
          <div className="border-t pt-3" style={{ borderColor: "var(--panel-border)" }}>
            <div className="text-xs uppercase tracking-wider mb-1" style={{ color: "var(--muted-text)" }}>
              {t.totalEquity}
            </div>
            <div className="text-xl font-bold tabular-nums" style={{ color: "var(--foreground)" }}>
              {fmtUSD(equityRaw)}
            </div>
            <div className="mt-2 grid gap-1 text-xs" style={{ color: "var(--muted-text)" }}>
              <div className="flex items-center justify-between">
                <span>{t.netDeposits}</span>
                <span style={{ color: "var(--foreground)" }}>{fmtUSD(netDeposits)}</span>
              </div>
              <div className="flex items-center justify-between">
                <span>{t.adjustedEquity}</span>
                <span style={{ color: "var(--foreground)" }}>{fmtUSD(equityAdjusted)}</span>
              </div>
            </div>
          </div>

          {/* Active Positions */}
          <div className="border-t pt-3" style={{ borderColor: "var(--panel-border)" }}>
            <div className="text-xs uppercase tracking-wider mb-2" style={{ color: "var(--muted-text)" }}>
              {t.activePositions}
            </div>
            <div className="flex flex-wrap gap-2">
              {symbols.length > 0 ? (
                symbols.map((symbol) => {
                  const coinIcon = getCoinIcon(symbol);
                  return (
                    <span
                      key={symbol}
                      className="inline-flex items-center gap-1.5 rounded border px-2 py-1 text-xs"
                      style={{
                        borderColor: "var(--panel-border)",
                        color: "var(--foreground)",
                      }}
                    >
                      {coinIcon && (
                        <img
                          src={coinIcon}
                          alt={symbol}
                          className="w-4 h-4"
                        />
                      )}
                      <span className="font-medium">{symbol}</span>
                    </span>
                  );
                })
              ) : (
                <div className="text-sm" style={{ color: "var(--muted-text)" }}>
                  {t.noActivePositions}
                </div>
              )}
            </div>
          </div>
        </div>
      ) : (
        <div className="text-sm" style={{ color: "var(--muted-text)" }}>
          {t.noData}
        </div>
      )}
    </div>
  );
}

function ModelBarsChart({ agents }: { agents: any[] }) {
  const language = useLanguage((s) => s.language);
  const t = getTranslation(language).leaderboard;
  
  const FULL = 120;
  const SCALE = 15000; // Max scale for chart

  // Fetch account data for all running agents
  const runningAgentIds = useMemo(() => 
    agents.filter(a => a.is_running).map(a => a.id).sort().join(','), 
    [agents]
  );

  const { data: allAccountsData } = useSWR(
    runningAgentIds ? `/agents/bars/${runningAgentIds}` : null,
    async () => {
      const ids = runningAgentIds.split(',');
      const results = await Promise.all(
        ids.map(async (id) => {
          try {
            const data = await api.getAccount(id);
            return { agentId: id, equity: data?.total_wallet_balance || 0 };
          } catch (error) {
            console.error(`Failed to fetch account for ${id}:`, error);
            return { agentId: id, equity: 0 };
          }
        })
      );
      return results;
    },
    { refreshInterval: 10000 }
  );

  // Create a map of agent equity
  const equityMap = useMemo(() => {
    if (!allAccountsData) return new Map();
    return new Map(allAccountsData.map(({ agentId, equity }) => [agentId, equity]));
  }, [allAccountsData]);

  // Combine agents with their equity data
  const agentsWithAccounts = useMemo(() => {
    return agents.map(agent => ({
      agent,
      equity: agent.is_running ? (equityMap.get(agent.id) || 0) : 0,
    }));
  }, [agents, equityMap]);

  return (
    <div
      className="rounded-md border p-4"
      style={{
        background: "var(--panel-bg)",
        borderColor: "var(--panel-border)",
      }}
    >
        <div className="text-xs uppercase tracking-wider mb-4" style={{ color: "var(--muted-text)" }}>
          {t.accountValue}
        </div>
      <div className="grid grid-cols-3 gap-4 sm:grid-cols-6">
        {agentsWithAccounts.map(({ agent, equity }) => {
          const color = getAgentModelColor(agent);
          const pct = Math.max(0, Math.min(equity / SCALE, 1));
          const fill = Math.max(4, Math.round(pct * FULL));

          return (
            <div key={agent.id} className="flex flex-col items-center gap-2">
              <div className="text-[11px] tabular-nums font-medium" style={{ color: "var(--foreground)" }}>
                {fmtUSD(equity)}
              </div>
              <div className="relative w-12" style={{ height: FULL }}>
                {/* Background bar */}
                <div
                  className="absolute inset-0 rounded border"
                  style={{
                    background: "color-mix(in oklab, var(--panel-border) 20%, transparent)",
                    borderColor: "var(--panel-border)",
                  }}
                />
                {/* Fill bar */}
                <div
                  className="absolute bottom-0 left-0 right-0 rounded-b"
                  style={{
                    height: fill,
                    background: color,
                  }}
                />
              </div>
              <div className="text-[11px] text-center" style={{ color: "var(--muted-text)" }}>
                {agent.name || agent.id}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

