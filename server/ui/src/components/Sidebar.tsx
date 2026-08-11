"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Activity, BarChart3, Star, MessageSquare, FlaskConical, Columns2, Timer } from "lucide-react";
import { motion } from "framer-motion";

const navItems = [
  { href: "/", label: "Traces", icon: Activity },
  { href: "/compare", label: "Compare", icon: Columns2 },
  { href: "/golden", label: "Golden Tests", icon: Star },
  { href: "/evaluations", label: "Evaluations", icon: FlaskConical },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <div className="w-[220px] border-r border-[var(--color-border)] flex flex-col bg-[#030304] shrink-0">
      <div className="pt-8 pb-6 px-6 flex items-center gap-3">
        <div className="w-6 h-6 rounded bg-gradient-to-b from-white to-white/60 flex items-center justify-center shadow-lg shadow-white/10">
          <Timer className="w-4 h-4 text-black" />
        </div>
        <h1 className="text-sm font-bold tracking-widest uppercase text-white">
          Chronos
        </h1>
      </div>
      
      <div className="px-4 mb-4">
        <div className="h-px w-full bg-gradient-to-r from-[var(--color-border)] to-transparent" />
      </div>

      <nav className="flex-1 px-3 flex flex-col gap-1">
        {navItems.map((item) => {
          const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all relative group ${
                isActive
                  ? "text-white bg-white/5"
                  : "text-[var(--color-text-muted)] hover:bg-white/5 hover:text-white"
              }`}
            >
              {isActive && (
                <motion.div 
                  layoutId="sidebar-active" 
                  className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-4 bg-[var(--color-primary)] rounded-r-full shadow-[0_0_8px_var(--color-primary)]" 
                />
              )}
              <item.icon className={`w-4 h-4 transition-colors ${isActive ? "text-[var(--color-primary)]" : "text-[var(--color-text-muted)] group-hover:text-white"}`} />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="p-6">
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/[0.02] border border-white/5 shadow-inner">
          <div className="w-1.5 h-1.5 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)] animate-pulse" />
          <span className="text-[10px] uppercase tracking-widest text-[var(--color-text-muted)] font-medium">
            Local v0.2.0
          </span>
        </div>
      </div>
    </div>
  );
}
