/**
 * API client for ROMA-01 Trading backend
 */

import type {
  Agent,
  AgentStatus,
  Account,
  Position,
  Performance,
  Decision,
  EquityPoint,
  Trade,
} from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

async function fetcher<T>(url: string): Promise<T> {
  const response = await fetch(`${API_BASE}${url}`);
  
  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }
  
  return response.json();
}

export const api = {
  // Get all agents
  getAgents: (): Promise<Agent[]> => fetcher("/api/agents"),
  
  // Get agent info
  getAgentInfo: (agentId: string): Promise<AgentStatus> => 
    fetcher(`/api/agents/${agentId}`),
  
  // Get account balance
  getAccount: (agentId: string): Promise<Account> => 
    fetcher(`/api/agents/${agentId}/account`),
  
  // Get positions
  getPositions: (agentId: string): Promise<Position[]> => 
    fetcher(`/api/agents/${agentId}/positions`),
  
  // Get performance metrics
  getPerformance: (agentId: string, lookback: number = 20): Promise<Performance> => 
    fetcher(`/api/agents/${agentId}/performance?lookback=${lookback}`),
  
  // Get detailed analytics
  getAnalytics: (agentId: string): Promise<any> => 
    fetcher(`/api/agents/${agentId}/analytics`),
  
  // Get decision logs
  getDecisions: (agentId: string, limit: number = 10): Promise<Decision[]> => 
    fetcher(`/api/agents/${agentId}/decisions?limit=${limit}`),
  
  // Get equity history
  getEquityHistory: (agentId: string, limit?: number): Promise<EquityPoint[]> => {
    const url = limit 
      ? `/api/agents/${agentId}/equity-history?limit=${limit}`
      : `/api/agents/${agentId}/equity-history`;
    return fetcher(url);
  },
  
  // Get trade history
  getTrades: (agentId: string, limit?: number): Promise<Trade[]> => {
    const url = limit
      ? `/api/agents/${agentId}/trades?limit=${limit}`
      : `/api/agents/${agentId}/trades`;
    return fetcher(url);
  },
  
  // Get market prices
  getMarketPrices: (symbols?: string[] | string): Promise<Array<{ symbol: string; fullSymbol: string; price: number }>> => {
    // Handle case where SWR passes the key as first argument
    if (typeof symbols === 'string' || !symbols || !Array.isArray(symbols)) {
      return fetcher('/api/market/prices');
    }
    const url = `/api/market/prices?symbols=${symbols.join(",")}`;
    return fetcher(url);
  },
  
  // Get custom prompts for an agent
  getCustomPrompts: async (agentId: string): Promise<any> => {
    const response = await fetch(`${API_BASE}/api/agents/${agentId}/prompts`);
    const data = await response.json();
    if (data.status === "success") {
      return data.data;
    }
    throw new Error("Failed to load custom prompts");
  },
  
  // Update custom prompts for an agent
  updateCustomPrompts: async (agentId: string, prompts: any): Promise<any> => {
    const response = await fetch(`${API_BASE}/api/agents/${agentId}/prompts`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(prompts),
    });
    const data = await response.json();
    if (data.status !== "success") {
      throw new Error(data.message || "Failed to save prompts");
    }
    return data;
  },
  
  // Get full prompt preview (core rules + custom prompts)
  getFullPromptPreview: async (agentId: string): Promise<string> => {
    const response = await fetch(`${API_BASE}/api/agents/${agentId}/prompts/preview`);
    const data = await response.json();
    if (data.status === "success") {
      return data.data.full_prompt;
    }
    throw new Error("Failed to load prompt preview");
  },
  
  // Chat with AI assistant
  chat: async (message: string): Promise<{ message: string }> => {
    const response = await fetch(`${API_BASE}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    
    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }
    
    const data = await response.json();
    return data;
  },
};

// WebSocket connection for real-time updates
export function createWebSocket(agentId: string, onMessage: (data: any) => void) {
  const wsUrl = `${API_BASE.replace('http', 'ws')}/ws/agents/${agentId}`;
  const ws = new WebSocket(wsUrl);
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    onMessage(data);
  };
  
  ws.onerror = (error) => {
    console.error("WebSocket error:", error);
  };
  
  return ws;
}

