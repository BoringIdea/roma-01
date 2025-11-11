"use client";

import type { ConfigAgent } from "@/types";

interface PromptsSectionProps {
  language: string;
  agentsForm: ConfigAgent[];
  selectedAgentId: string | null;
  onSelectAgent: (agentId: string) => void;
  PromptEditorComponent: React.ComponentType<{ agentId: string }>;
}

export function PromptsSection({
  language,
  agentsForm,
  selectedAgentId,
  onSelectAgent,
  PromptEditorComponent,
}: PromptsSectionProps) {
  return (
    <section
      className="rounded-xl border p-5"
      style={{ borderColor: "var(--panel-border)", background: "var(--panel-bg)" }}
    >
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="text-sm font-semibold uppercase tracking-wider">
            {language === "zh" ? "智能体提示词" : "Agent Prompts"}
          </h2>
          <p className="text-[11px]" style={{ color: "var(--muted-text)" }}>
            {language === "zh"
              ? "选择需要编辑的智能体，自定义策略提示词内容。"
              : "Pick an agent to customize the strategy prompt content."}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-[10px] uppercase tracking-widest" style={{ color: "var(--muted-text)" }}>
            {language === "zh" ? "选择智能体" : "Select Agent"}
          </label>
          <select
            value={selectedAgentId ?? ""}
            onChange={(e) => onSelectAgent(e.target.value)}
            className="rounded border bg-transparent px-3 py-1 text-xs outline-none"
            style={{ borderColor: "var(--panel-border)" }}
          >
            {agentsForm.map((agent) => (
              <option key={agent.id} value={agent.id}>
                {agent.name || agent.id}
              </option>
            ))}
          </select>
        </div>
      </div>

      {agentsForm.length === 0 || !selectedAgentId ? (
        <div
          className="mt-4 flex h-48 items-center justify-center rounded border text-xs"
          style={{ borderColor: "var(--panel-border)", color: "var(--muted-text)" }}
        >
          {language === "zh" ? "暂无智能体可配置" : "No agents available"}
        </div>
      ) : (
        <div className="mt-4 rounded border" style={{ borderColor: "var(--panel-border)" }}>
          <PromptEditorComponent agentId={selectedAgentId} />
        </div>
      )}
    </section>
  );
}

