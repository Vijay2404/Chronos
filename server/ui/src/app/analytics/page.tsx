"use client";

import { useEffect, useState } from "react";
import { BarChart, Bar, AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, PieChart, Pie } from "recharts";
import { motion } from "framer-motion";
import { BarChart3, Coins, Zap, Clock, Layers, Activity } from "lucide-react";

interface Stats {
  traces_count: number;
  success_count: number;
  error_count: number;
  total_tokens: number;
  total_spans: number;
  avg_duration_ms: number;
  model_usage: { model: string; prompt_tokens: number; completion_tokens: number; total_tokens: number; calls: number }[];
  activity: { hour: string; count: number; tokens: number }[];
}

function StatCard({ icon: Icon, label, value, color }: { icon: any; label: string; value: string | number; color: string }) {
  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-4 flex items-center gap-4">
      <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${color}`}>
        <Icon className="w-5 h-5" />
      </div>
      <div>
        <div className="text-2xl font-bold">{value}</div>
        <div className="text-xs text-[var(--color-text-muted)] uppercase tracking-wider">{label}</div>
      </div>
    </div>
  );
}

export default function AnalyticsPage() {
  const [stats, setStats] = useState<Stats | null>(null);

  useEffect(() => {
    fetch("/api/stats").then(r => r.json()).then(setStats).catch(console.error);
  }, []);

  if (!stats) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1, ease: "linear" }}>
          <Activity className="w-6 h-6 text-[var(--color-primary)] opacity-50" />
        </motion.div>
      </div>
    );
  }

  const pieData = [
    { name: "Success", value: stats.success_count, color: "var(--color-success)" },
    { name: "Error", value: stats.error_count, color: "var(--color-error)" },
    { name: "Other", value: stats.traces_count - stats.success_count - stats.error_count, color: "#eab308" },
  ].filter(d => d.value > 0);

  return (
    <div className="flex-1 p-6 pt-12 overflow-y-auto">
      <div className="max-w-6xl mx-auto flex flex-col gap-6">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-[var(--color-primary)]" /> Analytics
          </h1>
          <p className="text-sm text-[var(--color-text-muted)] mt-1">Token usage, cost breakdown, and performance metrics</p>
        </div>

        {/* Stat Cards */}
        <div className="grid grid-cols-4 gap-4">
          <StatCard icon={Layers} label="Total Traces" value={stats.traces_count} color="bg-blue-500/10 text-blue-400" />
          <StatCard icon={Zap} label="Total Tokens" value={stats.total_tokens.toLocaleString()} color="bg-orange-500/10 text-orange-400" />
          <StatCard icon={Clock} label="Avg Latency" value={`${Math.round(stats.avg_duration_ms)}ms`} color="bg-purple-500/10 text-purple-400" />
          <StatCard icon={Coins} label="Total Spans" value={stats.total_spans} color="bg-green-500/10 text-green-400" />
        </div>

        <div className="grid grid-cols-2 gap-4">
          {/* Activity Over Time */}
          <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-5">
            <h3 className="text-xs font-bold uppercase tracking-widest text-[var(--color-text-muted)] mb-4">Activity (24h)</h3>
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={stats.activity}>
                  <defs>
                    <linearGradient id="actGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="var(--color-primary)" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="var(--color-primary)" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="hour" hide />
                  <YAxis hide />
                  <Tooltip contentStyle={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)', borderRadius: '8px', fontSize: '12px' }} />
                  <Area type="monotone" dataKey="count" stroke="var(--color-primary)" strokeWidth={2} fill="url(#actGrad)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Success Rate Pie */}
          <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-5">
            <h3 className="text-xs font-bold uppercase tracking-widest text-[var(--color-text-muted)] mb-4">Success Rate</h3>
            <div className="h-48 flex items-center justify-center">
              {pieData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={pieData} cx="50%" cy="50%" innerRadius={50} outerRadius={70} paddingAngle={3} dataKey="value">
                      {pieData.map((entry, i) => (
                        <Cell key={i} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)', borderRadius: '8px', fontSize: '12px' }} />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <p className="text-sm text-[var(--color-text-muted)]">No data</p>
              )}
            </div>
            <div className="flex justify-center gap-4 mt-2">
              {pieData.map((d, i) => (
                <div key={i} className="flex items-center gap-1.5 text-xs">
                  <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: d.color }} />
                  {d.name}: {d.value}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Model Usage Table */}
        {stats.model_usage.length > 0 && (
          <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl overflow-hidden">
            <div className="p-5 border-b border-[var(--color-border)]">
              <h3 className="text-xs font-bold uppercase tracking-widest text-[var(--color-text-muted)]">Token Usage by Model</h3>
            </div>
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs uppercase text-[var(--color-text-muted)] border-b border-[var(--color-border)]">
                  <th className="px-5 py-3 text-left">Model</th>
                  <th className="px-5 py-3 text-right">Calls</th>
                  <th className="px-5 py-3 text-right">Prompt Tokens</th>
                  <th className="px-5 py-3 text-right">Completion Tokens</th>
                  <th className="px-5 py-3 text-right">Total</th>
                </tr>
              </thead>
              <tbody>
                {stats.model_usage.map((m, i) => (
                  <tr key={i} className="border-b border-[var(--color-border)] last:border-0">
                    <td className="px-5 py-3 font-mono text-[var(--color-primary)]">{m.model || "unknown"}</td>
                    <td className="px-5 py-3 text-right">{m.calls}</td>
                    <td className="px-5 py-3 text-right text-[var(--color-text-muted)]">{m.prompt_tokens.toLocaleString()}</td>
                    <td className="px-5 py-3 text-right text-[var(--color-text-muted)]">{m.completion_tokens.toLocaleString()}</td>
                    <td className="px-5 py-3 text-right font-bold">{m.total_tokens.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
