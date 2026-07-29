"use client";

import { useEffect, useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Activity, Clock, TerminalSquare, AlertCircle, CheckCircle2, BarChart3 } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

interface Trace {
  id: string;
  project: string;
  status: string;
  start_time: string;
  end_time: string | null;
}

export default function Home() {
  const router = useRouter();
  const [traces, setTraces] = useState<Trace[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/traces")
      .then((res) => res.json())
      .then((data) => {
        setTraces(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to fetch traces", err);
        setLoading(false);
      });
  }, []);

  const chartData = useMemo(() => {
    const grouped: Record<string, number> = {};
    traces.forEach(t => {
      const d = new Date(t.start_time);
      const key = `${d.getHours()}:${d.getMinutes().toString().padStart(2, '0')}`;
      grouped[key] = (grouped[key] || 0) + 1;
    });
    return Object.entries(grouped)
      .map(([time, count]) => ({ time, count }))
      .sort((a, b) => a.time.localeCompare(b.time));
  }, [traces]);

  return (
    <div className="flex-1 p-6 overflow-y-auto">
      <motion.div 
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="max-w-6xl mx-auto flex flex-col gap-5"
      >
        {/* Compact Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <Activity className="w-5 h-5 text-[var(--color-primary)]" />
              Traces
            </h1>
            <p className="text-[var(--color-text-muted)] text-sm mt-1">
              Agent execution telemetry
            </p>
          </div>
          <div className="flex gap-3">
            <div className="bg-[var(--color-surface)] px-3 py-1.5 rounded-lg border border-[var(--color-border)] flex items-center gap-2 text-xs font-medium">
              <TerminalSquare className="w-3.5 h-3.5 text-[var(--color-primary)]" />
              {traces.length} runs
            </div>
            <div className="bg-[var(--color-surface)] px-3 py-1.5 rounded-lg border border-[var(--color-border)] flex items-center gap-2 text-xs font-medium">
              <CheckCircle2 className="w-3.5 h-3.5 text-[var(--color-success)]" />
              {traces.filter(t => t.status === 'success').length} ok
            </div>
          </div>
        </div>

        {/* Compact Spark Bar Chart */}
        {!loading && chartData.length > 0 && (
          <div className="bg-[var(--color-surface)]/50 border border-[var(--color-border)] px-5 py-4 rounded-xl flex items-center gap-6">
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-[var(--color-text-muted)] shrink-0">
              <BarChart3 className="w-3.5 h-3.5" /> Activity
            </div>
            <div className="h-16 flex-1">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} barCategoryGap="20%">
                  <XAxis dataKey="time" hide />
                  <YAxis hide />
                  <Tooltip
                    contentStyle={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)', borderRadius: '8px', fontSize: '12px' }}
                    itemStyle={{ color: 'var(--color-primary)' }}
                    cursor={{ fill: 'rgba(59,130,246,0.08)' }}
                  />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                    {chartData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill="var(--color-primary)" fillOpacity={0.7} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* Traces Table */}
        {loading ? (
          <div className="flex items-center justify-center p-16">
            <motion.div 
              animate={{ rotate: 360 }}
              transition={{ repeat: Infinity, duration: 1, ease: "linear" }}
            >
              <Activity className="w-6 h-6 text-[var(--color-primary)] opacity-50" />
            </motion.div>
          </div>
        ) : (
          <div className="bg-[var(--color-surface)]/50 backdrop-blur-md rounded-xl border border-[var(--color-border)] overflow-hidden shadow-lg">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-[var(--color-surface-hover)]/80 text-xs uppercase tracking-wider text-[var(--color-text-muted)] border-b border-[var(--color-border)]">
                  <th className="px-4 py-3 font-medium">Trace ID</th>
                  <th className="px-4 py-3 font-medium">Project</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5" /> Time
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--color-border)]">
                {traces.map((trace, i) => (
                  <tr 
                    key={trace.id} 
                    onClick={() => router.push(`/traces/${trace.id}`)}
                    className="hover:bg-[var(--color-surface-hover)] transition-colors group cursor-pointer"
                  >
                    <td className="px-4 py-3">
                      <span className="font-mono text-sm text-[var(--color-primary)] group-hover:text-blue-400 font-bold">
                        {trace.id.substring(0, 8)}…
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm font-medium">{trace.project}</td>
                    <td className="px-4 py-3">
                      <div className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-xs font-semibold ${
                        trace.status === 'success'
                          ? 'bg-[var(--color-success)]/10 text-[var(--color-success)] border border-[var(--color-success)]/20'
                          : trace.status === 'error' 
                          ? 'bg-[var(--color-error)]/10 text-[var(--color-error)] border border-[var(--color-error)]/20'
                          : 'bg-yellow-500/10 text-yellow-500 border border-yellow-500/20'
                      }`}>
                        {trace.status === 'success' ? <CheckCircle2 className="w-3 h-3" /> : <AlertCircle className="w-3 h-3" />}
                        {trace.status || 'unknown'}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-[var(--color-text-muted)]">
                      {new Date(trace.start_time).toLocaleString(undefined, { 
                        month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' 
                      })}
                    </td>
                  </tr>
                ))}
                {traces.length === 0 && (
                  <tr>
                    <td colSpan={4} className="p-12 text-center">
                      <div className="flex flex-col items-center gap-2 text-[var(--color-text-muted)]">
                        <TerminalSquare className="w-8 h-8 opacity-20" />
                        <p className="text-sm">No traces found. Run an agent to see data here.</p>
                      </div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </motion.div>
    </div>
  );
}
