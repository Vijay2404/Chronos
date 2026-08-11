"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Star, Activity, CheckCircle2, AlertCircle, Clock, Pin } from "lucide-react";

interface Trace {
  id: string;
  project: string;
  status: string;
  start_time: string;
  total_tokens: number;
}

export default function GoldenPage() {
  const router = useRouter();
  const [traces, setTraces] = useState<Trace[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/golden").then(r => r.json()).then(d => { setTraces(d); setLoading(false); }).catch(() => setLoading(false));
  }, []);

  return (
    <div className="flex-1 p-6 pt-12 overflow-y-auto">
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="max-w-5xl mx-auto flex flex-col gap-5">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Star className="w-5 h-5 text-yellow-400" /> Golden Test Cases
          </h1>
          <p className="text-sm text-[var(--color-text-muted)] mt-1">
            Pinned traces used as regression baselines. Re-run agents against these to detect quality drift.
          </p>
        </div>

        {loading ? (
          <div className="flex items-center justify-center p-16">
            <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1, ease: "linear" }}>
              <Activity className="w-6 h-6 text-yellow-400 opacity-50" />
            </motion.div>
          </div>
        ) : traces.length === 0 ? (
          <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-12 flex flex-col items-center gap-3 text-[var(--color-text-muted)]">
            <Pin className="w-10 h-10 opacity-20" />
            <p className="text-sm">No golden traces yet. Open a trace and click "Pin as Golden" to save it as a regression test baseline.</p>
          </div>
        ) : (
          <div className="bg-[var(--color-surface)] rounded-xl border border-[var(--color-border)] overflow-hidden">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-[var(--color-surface-hover)]/80 text-xs uppercase tracking-wider text-[var(--color-text-muted)] border-b border-[var(--color-border)]">
                  <th className="px-4 py-3 font-medium">Trace ID</th>
                  <th className="px-4 py-3 font-medium">Project</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium">Tokens</th>
                  <th className="px-4 py-3 font-medium"><Clock className="w-3.5 h-3.5 inline mr-1" />Time</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--color-border)]">
                {traces.map(trace => (
                  <tr key={trace.id} onClick={() => router.push(`/traces/${trace.id}`)} className="hover:bg-[var(--color-surface-hover)] transition-colors cursor-pointer">
                    <td className="px-4 py-3 font-mono text-sm text-yellow-400 font-bold">{trace.id.substring(0, 8)}…</td>
                    <td className="px-4 py-3 text-sm">{trace.project}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-semibold ${trace.status === "success" ? "bg-green-500/10 text-green-400 border border-green-500/20" : "bg-red-500/10 text-red-400 border border-red-500/20"}`}>
                        {trace.status === "success" ? <CheckCircle2 className="w-3 h-3" /> : <AlertCircle className="w-3 h-3" />}
                        {trace.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-[var(--color-text-muted)]">{(trace.total_tokens || 0).toLocaleString()}</td>
                    <td className="px-4 py-3 text-sm text-[var(--color-text-muted)]">{new Date(trace.start_time).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </motion.div>
    </div>
  );
}
