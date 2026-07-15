import { useState } from "react";
import { NavLink } from "react-router-dom";
import {
  LayoutDashboard, MessageCircle, Users2, ShieldAlert, ShieldCheck, ScrollText,
  HelpCircle, ChevronLeft, ChevronRight, Bot,
} from "lucide-react";
import { useZoom } from "./useZoom";

const nav = [
  { to: "/", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/chat", icon: MessageCircle, label: "Chat" },
  { to: "/personas", icon: Users2, label: "Personas" },
  { to: "/safety", icon: ShieldAlert, label: "Safety" },
  { to: "/compliance", icon: ShieldCheck, label: "Compliance" },
  { to: "/audit", icon: ScrollText, label: "Audit" },
  { to: "/help", icon: HelpCircle, label: "Help" },
];

export function Layout({ children }: { children: React.ReactNode }) {
  useZoom();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="flex h-screen">
      <aside
        className={`flex flex-col bg-zinc-900 border-r border-zinc-800 transition-all duration-200 ${
          collapsed ? "w-16" : "w-56"
        }`}
      >
        <div className="flex items-center gap-2 p-3 border-b border-zinc-800">
          <Bot className="w-6 h-6 text-amber-500 shrink-0" />
          {!collapsed && <span className="font-semibold text-sm">ChatBot MCP</span>}
        </div>
        <nav className="flex-1 p-2 space-y-1">
          {nav.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-2 py-2 rounded-lg text-sm transition-colors ${
                  isActive
                    ? "bg-amber-500/10 text-amber-500"
                    : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800"
                }`
              }
            >
              <Icon className="w-5 h-5 shrink-0" />
              {!collapsed && <span>{label}</span>}
            </NavLink>
          ))}
        </nav>
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="flex items-center justify-center p-3 border-t border-zinc-800 text-zinc-500 hover:text-zinc-300"
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </aside>
      <main className="flex-1 overflow-auto p-6">{children}</main>
    </div>
  );
}
