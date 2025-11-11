"use client";

import Link from "next/link";
import { useTheme } from "@/store/useTheme";
import { useLanguage } from "@/store/useLanguage";
import { getTranslation } from "@/lib/i18n";
import { useState, useEffect, useRef } from "react";
import useSWR from "swr";
import { api } from "@/lib/api";
import { getAgentModelColor } from "@/lib/model/meta";

export function Header() {
  const theme = useTheme((s) => s.theme);
  const setTheme = useTheme((s) => s.setTheme);
  const language = useLanguage((s) => s.language);
  const setLanguage = useLanguage((s) => s.setLanguage);
  const t = getTranslation(language);
  
  const [agentsOpen, setAgentsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Fetch agents
  const { data: agents } = useSWR("/agents", api.getAgents, {
    refreshInterval: 30000,
  });

  // Close dropdown when clicking outside
  useEffect(() => {
    if (!agentsOpen) return;
    
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setAgentsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [agentsOpen]);

  return (
    <header
      className="sticky top-0 z-50 w-full border-b backdrop-blur"
      style={{
        background: "var(--header-bg)",
        borderColor: "var(--header-border)",
      }}
    >
      <div
        className="relative flex h-[var(--header-h)] w-full items-center px-3 text-xs"
        style={{ color: "var(--foreground)" }}
      >
        {/* Left: Brand */}
        <div className="flex min-w-0 flex-1">
          <Link
            href="/"
            className="text-2xl font-black tracking-widest hover:opacity-80 transition-all hover:scale-105"
            style={{ 
              fontFamily: "var(--font-orbitron)",
              background: "linear-gradient(135deg, var(--brand-accent) 0%, #60a5fa 50%, #a78bfa 100%)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              backgroundClip: "text",
              letterSpacing: "0.2em",
              textShadow: "0 0 30px rgba(96, 165, 250, 0.3)"
            }}
          >
            ROMA-01
          </Link>
        </div>

            {/* Center: Navigation */}
            <nav
              className="absolute left-1/2 -translate-x-1/2 flex items-center gap-6"
              aria-label="Primary"
            >
              <Link href="/" className="font-semibold hover:opacity-70 transition-opacity uppercase tracking-wider" style={{ color: "inherit" }}>
                {t.header.live}
              </Link>
              <Link href="/leaderboard" className="font-semibold hover:opacity-70 transition-opacity uppercase tracking-wider" style={{ color: "inherit" }}>
                {t.header.leaderboard}
              </Link>
          
          {/* Agents Dropdown */}
          <div ref={dropdownRef} className="relative">
            <button
              onClick={() => setAgentsOpen(!agentsOpen)}
              className="font-semibold hover:opacity-70 transition-opacity flex items-center gap-1 uppercase tracking-wider"
              style={{ color: "inherit" }}
            >
              {t.header.agents}
              <svg 
                className={`w-3 h-3 transition-transform ${agentsOpen ? "rotate-180" : ""}`}
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            {/* Dropdown Menu */}
            {agentsOpen && agents && agents.length > 0 && (
              <div
                className="absolute top-full mt-2 min-w-[200px] rounded-md border shadow-lg"
                style={{
                  background: "var(--panel-bg)",
                  borderColor: "var(--panel-border)",
                  left: "50%",
                  transform: "translateX(-50%)",
                }}
              >
                <div className="py-1">
                  {agents.map((agent) => {
                    const color = getAgentModelColor(agent);
                    return (
                      <Link
                        key={agent.id}
                        href={`/agent/${agent.id}`}
                        onClick={() => setAgentsOpen(false)}
                        className="block px-3 py-2 hover:bg-opacity-50 transition-colors"
                        style={{
                          color: "var(--foreground)",
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.background = `${color}15`;
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.background = "transparent";
                        }}
                      >
                        <div className="flex items-center justify-between gap-3">
                          <div className="flex items-center gap-2">
                            <div 
                              className="w-2 h-2 rounded-full"
                              style={{ background: color }}
                            />
                            <span className="text-xs font-medium">
                              {agent.name || agent.id}
                            </span>
                          </div>
                          {agent.is_running && (
                            <span 
                              className="text-[10px] px-1.5 py-0.5 rounded"
                              style={{ 
                                background: "rgba(34, 197, 94, 0.15)",
                              color: "#22c55e"
                            }}
                          >
                            {t.header.running}
                          </span>
                          )}
                        </div>
                      </Link>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
          
          {/* Settings Link */}
          <Link href="/settings" className="font-semibold hover:opacity-70 transition-opacity uppercase tracking-wider" style={{ color: "inherit" }}>
            {t.header.settings}
          </Link>

          {/* About Link */}
          <Link href="/about" className="font-semibold hover:opacity-70 transition-opacity uppercase tracking-wider" style={{ color: "inherit" }}>
            {t.header.about}
          </Link>
        </nav>

        {/* Right: Theme toggle + External links */}
        <div className="flex min-w-0 flex-1 justify-end">
          <div className="flex items-center gap-2">
            {/* GitHub */}
            <a
              href="https://github.com/lukema95/roma-01"
              target="_blank"
              rel="noopener noreferrer"
              aria-label="Open GitHub repository"
              className="inline-flex items-center justify-center w-7 h-7 rounded border chip-btn"
              style={{
                borderColor: "var(--chip-border)",
                color: "var(--btn-inactive-fg)",
              }}
              title="GitHub"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                width="16"
                height="16"
                fill="currentColor"
                aria-hidden="true"
              >
                <path d="M12 .5C5.73.5.97 5.26.97 11.54c0 4.86 3.15 8.98 7.52 10.43.55.1.75-.24.75-.53 0-.26-.01-1.13-.02-2.05-3.06.67-3.71-1.3-3.71-1.3-.5-1.28-1.22-1.63-1.22-1.63-.99-.68.08-.67.08-.67 1.09.08 1.66 1.12 1.66 1.12.98 1.67 2.56 1.19 3.19.91.1-.71.38-1.19.69-1.46-2.44-.28-5.01-1.22-5.01-5.42 0-1.2.43-2.18 1.12-2.95-.11-.28-.49-1.42.11-2.96 0 0 .93-.3 3.05 1.13.89-.25 1.84-.38 2.79-.38.95 0 1.9.13 2.79.38 2.12-1.43 3.05-1.13 3.05-1.13.6 1.54.22 2.68.11 2.96.69.77 1.12 1.75 1.12 2.95 0 4.21-2.57 5.14-5.02 5.41.39.34.73 1.01.73 2.03 0 1.46-.01 2.63-.01 2.98 0 .29.19.64.75.53 4.37-1.45 7.52-5.57 7.52-10.43C23.03 5.26 18.27.5 12 .5z" />
              </svg>
            </a>

            {/* Language Toggle */}
            <div className="flex items-center gap-1 text-[11px]">
              <div
                className="flex overflow-hidden rounded border"
                style={{ borderColor: "var(--chip-border)" }}
              >
                <button
                  title="English"
                  className="px-2 py-1 chip-btn"
                  style={
                    language === "en"
                      ? {
                          background: "var(--btn-active-bg)",
                          color: "var(--btn-active-fg)",
                        }
                      : { color: "var(--btn-inactive-fg)" }
                  }
                  onClick={() => setLanguage("en")}
                >
                  EN
                </button>
                <button
                  title="中文"
                  className="px-2 py-1 chip-btn"
                  style={
                    language === "zh"
                      ? {
                          background: "var(--btn-active-bg)",
                          color: "var(--btn-active-fg)",
                        }
                      : { color: "var(--btn-inactive-fg)" }
                  }
                  onClick={() => setLanguage("zh")}
                >
                  中文
                </button>
              </div>
            </div>

            {/* Theme Toggle */}
            <div className="hidden sm:flex items-center gap-1 text-[11px]">
              <div
                className="flex overflow-hidden rounded border"
                style={{ borderColor: "var(--chip-border)" }}
              >
                {(["dark", "light", "system"] as const).map((themeOption) => (
                  <button
                    key={themeOption}
                    title={themeOption}
                    className="px-2 py-1 capitalize chip-btn"
                    style={
                      theme === themeOption
                        ? {
                            background: "var(--btn-active-bg)",
                            color: "var(--btn-active-fg)",
                          }
                        : { color: "var(--btn-inactive-fg)" }
                    }
                    onClick={() => setTheme(themeOption)}
                  >
                    {themeOption}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}

export default Header;

