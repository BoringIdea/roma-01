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
  ConfigResponse,
  ConfigUpdatePayload,
} from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";
const CONFIG_TOKEN_STORAGE_KEY = "roma-settings-token";

let configAuthToken: string | null = null;
const isBrowser = typeof window !== "undefined";

function buildHeaders(initHeaders?: HeadersInit, includeAuth = true): Headers {
  const headers = new Headers(initHeaders);
  if (includeAuth && configAuthToken && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${configAuthToken}`);
  }
  return headers;
}

async function fetcher<T>(url: string, init?: RequestInit): Promise<T> {
  const headers = buildHeaders(init?.headers, true);
  const response = await fetch(`${API_BASE}${url}`, {
    ...init,
    headers,
  });
  
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `API error: ${response.statusText}`);
  }
  
  return response.json();
}

function configRequired() {
  if (!configAuthToken) {
    throw new Error("CONFIG_AUTH_REQUIRED");
  }
}

async function configFetcher<T>(url: string, init?: RequestInit): Promise<T> {
  configRequired();
  const headers = buildHeaders(init?.headers, true);
  if (init?.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE}${url}`, {
    ...init,
    headers,
  });

  if (response.status === 401) {
    setConfigAuthToken(null);
    const message = await response.text();
    throw new Error(message || "CONFIG_AUTH_EXPIRED");
  }

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `API error: ${response.statusText}`);
  }

  return response.json();
}

export function initializeConfigAuthTokenFromStorage(): string | null {
  if (!isBrowser) return null;
  if (configAuthToken) return configAuthToken;
  const stored = window.localStorage.getItem(CONFIG_TOKEN_STORAGE_KEY);
  configAuthToken = stored || null;
  return configAuthToken;
}

export function setConfigAuthToken(token: string | null): void {
  configAuthToken = token;
  if (!isBrowser) return;
  if (token) {
    window.localStorage.setItem(CONFIG_TOKEN_STORAGE_KEY, token);
  } else {
    window.localStorage.removeItem(CONFIG_TOKEN_STORAGE_KEY);
  }
}

export function getConfigAuthToken(): string | null {
  return configAuthToken;
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
    const data = await fetcher<{ status: string; data: any }>(`/api/agents/${agentId}/prompts`);
    if (data.status === "success") {
      return data.data;
    }
    throw new Error("Failed to load custom prompts");
  },
  
  // Update custom prompts for an agent
  updateCustomPrompts: async (agentId: string, prompts: any): Promise<any> => {
    const data = await fetcher<{ status: string; message?: string }>(`/api/agents/${agentId}/prompts`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(prompts),
    });
    if (data.status !== "success") {
      throw new Error(data.message || "Failed to save prompts");
    }
    return data;
  },

  // Get system-only prompt preview (no custom sections)
  getSystemPromptPreview: async (agentId: string, language?: string): Promise<string> => {
    const qs = language ? `?language=${encodeURIComponent(language)}` : "";
    const data = await fetcher<{ status: string; data: { system_prompt: string } }>(
      `/api/agents/${agentId}/prompts/system${qs}`,
    );
    if (data.status === "success") {
      return data.data.system_prompt;
    }
    throw new Error("Failed to load system prompt");
  },
 
  // Get full prompt preview (core rules + custom prompts)
  getFullPromptPreview: async (agentId: string, language?: string): Promise<string> => {
    const qs = language ? `?language=${encodeURIComponent(language)}` : "";
    const data = await fetcher<{ status: string; data: { full_prompt: string } }>(
      `/api/agents/${agentId}/prompts/preview${qs}`
    );
    if (data.status === "success") {
      return data.data.full_prompt;
    }
    throw new Error("Failed to load prompt preview");
  },
  
  // Chat with AI assistant
  chat: async (message: string, language?: string): Promise<{ message: string }> => {
    const qs = language ? `?language=${encodeURIComponent(language)}` : "";
    const response = await fetch(`${API_BASE}/api/chat${qs}`, {
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

  // Close a specific position (admin only)
  closeAgentPosition: async (
    agentId: string,
    payload: { symbol: string; side: "long" | "short"; quantity?: number; quantity_pct?: number },
  ): Promise<any> => {
    return configFetcher(`/api/admin/agents/${agentId}/positions/close`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  // Close all positions across agents (admin only)
  closeAllPositions: async (agentIds?: string[]): Promise<any> => {
    const body =
      agentIds && agentIds.length > 0
        ? { agent_ids: agentIds }
        : {};
    return configFetcher("/api/admin/positions/close-all", {
      method: "POST",
      body: JSON.stringify(body),
    });
  },
};

export const configApi = {
  login: async (username: string, password: string) => {
    const response = await fetch(`${API_BASE}/api/config/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });

    if (!response.ok) {
      const message = await response.text();
      throw new Error(message || "Failed to login");
    }

    const data = await response.json();
    setConfigAuthToken(data.access_token);
    return data;
  },

  getConfig: async (): Promise<ConfigResponse> => {
    return configFetcher("/api/config");
  },

  updateConfig: async (payload: ConfigUpdatePayload): Promise<ConfigResponse> => {
    return configFetcher("/api/config", {
      method: "PUT",
      body: JSON.stringify(payload),
    });
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

