"use client";

import { useParams } from "next/navigation";
import useSWR from "swr";
import AgentStatsSummary from "@/components/agent/AgentStatsSummary";
import AgentPositionsTable from "@/components/agent/AgentPositionsTable";
import AgentTradesTable from "@/components/agent/AgentTradesTable";
import AgentDecisionsHistory from "@/components/agent/AgentDecisionsHistory";
import { getAgentModelColor } from "@/lib/model/meta";
import { api } from "@/lib/api";

export default function AgentDetailPage() {
  const params = useParams();
  const id = params.id as string;

  // Fetch agent info to get real name
  const { data: agentInfo } = useSWR(`/agent/${id}`, () => api.getAgentInfo(id), {
    refreshInterval: 10000,
  });

  const agentName = agentInfo?.name || id;
  const color = getAgentModelColor({
    model_id: agentInfo?.model_id,
    model_config_id: agentInfo?.model_config_id,
    llm_model: agentInfo?.llm_model,
    id,
  });

  return (
    <div 
      className="w-full terminal-scan px-3 py-3 sm:px-4 sm:py-4 lg:px-8 lg:py-6"
      style={{ background: "var(--bg)" }}
    >
      <div className="mx-auto w-full max-w-7xl space-y-3">
        {/* Model Header with brand color */}
        <div 
          className="rounded-md border p-4"
          style={{
            background: `linear-gradient(0deg, ${color}10, var(--panel-bg))`,
            borderColor: `${color}55`,
          }}
        >
          <div className="flex items-center gap-3">
            <div 
              className="w-3 h-3 rounded-full"
              style={{ background: color }}
            />
            <h1 
              className="text-xl font-bold uppercase tracking-wide terminal-text"
              style={{ color: "var(--foreground)" }}
            >
              {agentName}
            </h1>
          </div>
        </div>

        {/* Stats Summary */}
        <AgentStatsSummary agentId={id} />

        {/* Positions & Trades */}
        <div className="space-y-3">
          <div
            className="rounded-md border p-3"
            style={{
              background: "var(--panel-bg)",
              borderColor: "var(--panel-border)",
            }}
          >
            <AgentPositionsTable agentId={id} />
          </div>

          <div
            className="rounded-md border p-3"
            style={{
              background: "var(--panel-bg)",
              borderColor: "var(--panel-border)",
            }}
          >
            <AgentTradesTable agentId={id} />
          </div>

          {/* Decision History */}
          <div
            className="rounded-md border p-3"
            style={{
              background: "var(--panel-bg)",
              borderColor: "var(--panel-border)",
            }}
          >
            <AgentDecisionsHistory agentId={id} />
          </div>
        </div>
      </div>
    </div>
  );
}

