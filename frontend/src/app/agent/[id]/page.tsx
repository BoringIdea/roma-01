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
      className="w-full terminal-scan p-6"
    >
      <div className="mx-auto w-full max-w-7xl space-y-6">
        {/* Model Header */}
        <div
          className="border p-6"
          style={{
            borderColor: "var(--panel-border)",
            background: "var(--panel-bg)",
          }}
        >
          <div className="flex items-center gap-4">
            <div
              className="w-4 h-4"
              style={{ background: color }}
            />
            <h1
              className="text-2xl font-black uppercase tracking-tighter italic"
              style={{ color: "var(--foreground)" }}
            >
              {agentName}
            </h1>
          </div>
        </div>

        {/* Stats Summary */}
        <AgentStatsSummary agentId={id} />

        {/* Positions & Trades */}
        <div className="space-y-6">
          <div
            className="border p-6"
            style={{
              background: "var(--panel-bg)",
              borderColor: "var(--panel-border)",
            }}
          >
            <AgentPositionsTable agentId={id} />
          </div>

          <div
            className="border p-6"
            style={{
              background: "var(--panel-bg)",
              borderColor: "var(--panel-border)",
            }}
          >
            <AgentTradesTable agentId={id} />
          </div>

          {/* Decision History */}
          <div
            className="border p-6"
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

