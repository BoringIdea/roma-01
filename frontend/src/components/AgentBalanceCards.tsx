"use client";

import { useRouter } from "next/navigation";
import useSWR from "swr";
import { TrendingUp, TrendingDown } from "lucide-react";
import { api } from "@/lib/api";
import type { Agent, Account } from "@/types";

interface AgentBalanceCardsProps {
  agents: Agent[];
  onAgentClick?: (agentId: string) => void;
}

const AGENT_COLORS = [
  "bg-blue-500",
  "bg-green-500",
  "bg-amber-500",
  "bg-red-500",
  "bg-purple-500",
  "bg-pink-500",
];

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
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
      {agents.map((agent, index) => (
        <AgentCard
          key={agent.id}
          agent={agent}
          color={AGENT_COLORS[index % AGENT_COLORS.length]}
          icon={AGENT_ICONS[index % AGENT_ICONS.length]}
          onClick={() => handleCardClick(agent.id)}
        />
      ))}
    </div>
  );
}

function AgentCard({
  agent,
  color,
  icon,
  onClick,
}: {
  agent: Agent;
  color: string;
  icon: string;
  onClick: () => void;
}) {
  const { data: account } = useSWR(`/agent/${agent.id}/account`, () =>
    api.getAccount(agent.id), { refreshInterval: 10000 }
  );

  if (!account) {
    return (
      <div className="bg-white border border-gray-200 rounded-xl p-4 animate-pulse">
        <div className="h-20 bg-gray-100 rounded"></div>
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
      className="bg-white border border-gray-200 rounded-xl p-4 hover:shadow-lg transition-all hover:scale-105 text-left group"
    >
      {/* Agent Icon */}
      <div className="flex items-center justify-between mb-3">
        <div className={`w-10 h-10 ${color} rounded-lg flex items-center justify-center text-lg shadow-sm group-hover:shadow-md transition-shadow`}>
          {icon}
        </div>
        <div
          className={`px-2 py-1 rounded-full text-xs font-medium ${
            agent.is_running
              ? "bg-green-100 text-green-700"
              : "bg-gray-100 text-gray-500"
          }`}
        >
          {agent.is_running ? "● LIVE" : "○ OFF"}
        </div>
      </div>

      {/* Agent Name */}
      <h3 className="font-bold text-gray-900 mb-1 truncate group-hover:text-blue-600 transition-colors">
        {agent.name}
      </h3>
      <p className="text-xs text-gray-500 mb-3">
        Cycles: {agent.cycle_count} • Runtime: {agent.runtime_minutes}m
      </p>

      {/* Balance */}
      <div className="mb-2">
        <p className="text-xs text-gray-500 mb-1">Balance</p>
        <p className="text-lg font-bold font-mono text-gray-900">
          ${adjustedBalance.toFixed(2)}
        </p>
      </div>

      {/* P&L */}
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs text-gray-500 mb-1">Return</p>
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
          <p className="text-xs text-gray-500 mb-1">USDT</p>
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
