"use client";

import { useRouter } from "next/navigation";
import useSWR from "swr";
import { TrendingUp, TrendingDown } from "lucide-react";
import { api } from "@/lib/api";
import type { Agent } from "@/types";

interface AgentBalanceCardsProps {
  agents: Agent[];
  onAgentClick?: (agentId: string) => void;
}

const AGENT_ICONS = ["🤖", "🧠", "⚡", "🚀", "💎", "🎯"];

export function AgentBalanceCards({ agents, onAgentClick }: AgentBalanceCardsProps) {
  const router = useRouter();

  const handleCardClick = (agentId: string) => {
    if (onAgentClick) {
      onAgentClick(agentId);
    } else {
      router.push(`/agent/${agentId}`);
    }
  };

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
      {agents.map((agent, index) => (
        <AgentCard
          key={agent.id}
          agent={agent}
          icon={AGENT_ICONS[index % AGENT_ICONS.length]}
          onClick={() => handleCardClick(agent.id)}
        />
      ))}
    </div>
  );
}

function AgentCard({
  agent,
  icon,
  onClick,
}: {
  agent: Agent;
  icon: string;
  onClick: () => void;
}) {
  const { data: account } = useSWR(`/agent/${agent.id}/account`, () =>
    api.getAccount(agent.id), { refreshInterval: 10000 }
  );

  if (!account) {
    return (
      <div className="border border-black p-4 animate-pulse">
        <div className="h-20 bg-black/5" />
      </div>
    );
  }

  // Calculate return rate using adjusted balance and initial balance
  const adjustedBalance = account.adjusted_total_balance ?? account.total_wallet_balance ?? 0;
  const initialBalance = account.initial_balance ?? 10000;
  const netDeposits = account.net_deposits ?? 0;
  const investedCapital = initialBalance + Math.max(netDeposits, 0);
  const denominator = investedCapital > 0 ? investedCapital : Math.max(initialBalance, 1);
  const totalPnl = adjustedBalance - initialBalance;
  const returnRate = denominator > 0 ? (totalPnl / denominator) * 100 : 0;
  const isProfit = returnRate >= 0;

  return (
    <button
      onClick={onClick}
      className="border border-black bg-white p-4 text-left font-bold hover:bg-black hover:text-white transition-colors"
    >
      {/* Agent Icon */}
      <div className="flex items-center justify-between mb-3">
        <div className="w-10 h-10 border border-black flex items-center justify-center text-lg bg-white">
          {icon}
        </div>
        <div
          className="px-2 py-1 border border-black text-xs font-black uppercase"
        >
          {agent.is_running ? "LIVE" : "OFF"}
        </div>
      </div>

      {/* Agent Name */}
      <h3 className="font-bold mb-1 truncate">{agent.name}</h3>
      <p className="text-xs font-bold mb-3">
        Cycles: {agent.cycle_count} • Runtime: {agent.runtime_minutes}m
      </p>

      {/* Balance */}
      <div className="mb-2">
        <p className="text-xs font-bold uppercase mb-1">Balance</p>
        <p className="text-lg font-bold font-mono">
          ${adjustedBalance.toFixed(2)}
        </p>
      </div>

      {/* P&L */}
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-bold uppercase mb-1">Return</p>
          <div className="flex items-center gap-1">
            {isProfit ? (
              <TrendingUp size={14} className="text-green-600" />
            ) : (
              <TrendingDown size={14} className="text-red-600" />
            )}
            <span
              className={`text-sm font-bold ${
                isProfit ? "text-green-600" : "text-red-600"
              }`}
            >
              {isProfit ? "+" : ""}
              {returnRate.toFixed(2)}%
            </span>
          </div>
        </div>
        <div className="text-right">
          <p className="text-xs font-bold uppercase mb-1">USDT</p>
          <p
            className={`text-sm font-mono font-medium ${
              isProfit ? "text-green-600" : "text-red-600"
            }`}
          >
            {isProfit ? "+" : ""}${totalPnl.toFixed(2)}
          </p>
        </div>
      </div>
    </button>
  );
}
