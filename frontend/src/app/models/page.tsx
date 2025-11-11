"use client";

import Header from "@/components/layout/Header";
import useSWR from "swr";
import { api } from "@/lib/api";
import { getAgentModelColor, getAgentModelName } from "@/lib/model/meta";
import Link from "next/link";
import { Activity, TrendingUp, DollarSign } from "lucide-react";

export default function ModelsPage() {
  const { data: agents, error } = useSWR("/agents", api.getAgents, {
    refreshInterval: 10000,
  });

  if (error) {
    return (
      <div className="min-h-screen flex flex-col" style={{ background: "var(--background)" }}>
        <Header />
        <div className="flex-1 flex items-center justify-center">
          <div className="p-6 rounded border" style={{ background: "var(--panel-bg)", borderColor: "var(--panel-border)" }}>
            <p className="font-semibold mb-2" style={{ color: "#ef4444" }}>Failed to load agents</p>
            <p className="text-sm" style={{ color: "var(--muted-text)" }}>{error.message}</p>
          </div>
        </div>
      </div>
    );
  }

  if (!agents) {
    return (
      <div className="min-h-screen flex flex-col" style={{ background: "var(--background)" }}>
        <Header />
        <div className="flex-1 flex items-center justify-center">
          <div className="flex flex-col items-center gap-4">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2" style={{ borderColor: "var(--brand-accent)" }}></div>
            <p style={{ color: "var(--muted-text)" }}>Loading agents...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col terminal-scan" style={{ background: "var(--background)" }}>
      <Header />
      
      <main className="flex-1 p-6">
        <div className="max-w-6xl mx-auto">
          <h1 className="text-3xl font-bold mb-2" style={{ color: "var(--foreground)" }}>
            Trading Agents
          </h1>
          <p className="mb-8" style={{ color: "var(--muted-text)" }}>
            AI-powered trading agents running on the platform
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {agents.map((agent: any) => (
              <Link
                key={agent.id}
                href={`/agent/${agent.id}`}
                className="block"
              >
                <div
                  className="rounded-lg border p-6 transition-all hover:shadow-lg"
                  style={{
                    background: "var(--panel-bg)",
                    borderColor: "var(--panel-border)",
                  }}
                >
                  {/* Model Header */}
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <div
                          className="w-3 h-3 rounded-full"
                          style={{ background: getAgentModelColor(agent) }}
                        />
                        <h3 className="font-bold text-lg" style={{ color: "var(--foreground)" }}>
                        {agent.name || getAgentModelName(agent) || agent.id}
                        </h3>
                      </div>
                      <p className="text-xs mb-2" style={{ color: "var(--muted-text)" }}>
                        {agent.id}
                      </p>
                    </div>
                    <span
                      className={`px-2 py-1 rounded text-xs font-medium ${
                        agent.is_running
                          ? "bg-green-500/20 text-green-400"
                          : "bg-gray-500/20"
                      }`}
                      style={{ color: agent.is_running ? "#22c55e" : "var(--muted-text)" }}
                    >
                      {agent.is_running ? "● Active" : "○ Idle"}
                    </span>
                  </div>

                  {/* Stats */}
                  <div className="space-y-3">
                    <div className="flex items-center gap-2 text-sm">
                      <Activity size={16} style={{ color: "var(--muted-text)" }} />
                      <span style={{ color: "var(--muted-text)" }}>Cycle:</span>
                      <span className="font-mono font-semibold" style={{ color: "var(--foreground)" }}>
                        #{agent.cycle_count}
                      </span>
                    </div>

                    <div className="flex items-center gap-2 text-sm">
                      <TrendingUp size={16} style={{ color: "var(--muted-text)" }} />
                      <span style={{ color: "var(--muted-text)" }}>Runtime:</span>
                      <span className="font-mono font-semibold" style={{ color: "var(--foreground)" }}>
                        {agent.runtime_minutes} min
                      </span>
                    </div>

                    <div className="pt-3 mt-3 border-t" style={{ borderColor: "var(--panel-border)" }}>
                      <button
                        className="w-full py-2 rounded text-sm font-medium transition-colors"
                        style={{
                          background: "var(--btn-active-bg)",
                          color: "var(--btn-active-fg)",
                        }}
                      >
                        View Details →
                      </button>
                    </div>
                  </div>
                </div>
              </Link>
            ))}
          </div>

          {agents.length === 0 && (
            <div className="text-center py-20">
              <div className="text-6xl mb-4">🤖</div>
            <p className="text-xl mb-2" style={{ color: "var(--foreground)" }}>No agents configured</p>
            <p style={{ color: "var(--muted-text)" }}>
              Configure trading agents in the backend to see them here
            </p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

