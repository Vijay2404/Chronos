"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { FlaskConical, Activity, ThumbsUp, ThumbsDown } from "lucide-react";

interface Evaluation {
  id: string;
  trace_id: string;
  name: string;
  score: number;
  label: string | null;
  comment: string | null;
  method: string;
  created_at: string;
}

export default function EvaluationsPage() {
  const [evals, setEvals] = useState<Evaluation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/evaluations").then(r => r.json()).then(d => { setEvals(d); setLoading(false); }).catch(() => setLoading(false));
  }, []);

  const avgScore = evals.length > 0 ? (evals.reduce((sum, e) => sum + e.score, 0) / evals.length).toFixed(2) : "—";

  return (
    <div className="flex-1 p-6 pt-12 overflow-y-auto">
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="max-w-5xl mx-auto flex flex-col gap-5">
        <div className="flex justify-between items-end">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <FlaskConical className="w-5 h-5 text-[var(--color-secondary)]" /> Evaluations
            </h1>
            <p className="text-sm text-[var(--color-text-muted)] mt-1">Score agent outputs for quality tracking over time.</p>
          </div>
          <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-4 py-2">
            <span className="text-xs text-[var(--color-text-muted)] uppercase tracking-wider">Avg Score</span>
            <span className="ml-2 text-lg font-bold text-[var(--color-secondary)]">{avgScore}</span>
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center p-16">
            <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1, ease: "linear" }}>
              <Activity className="w-6 h-6 text-[var(--color-secondary)] opacity-50" />
            </motion.div>
          </div>
        ) : evals.length === 0 ? (
          <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-12 flex flex-col items-center gap-3 text-[var(--color-text-muted)]">
            <FlaskConical className="w-10 h-10 opacity-20" />
            <p className="text-sm">No evaluations yet. Score a trace from the Trace Detail view to get started.</p>
          </div>
        ) : (
          <div className="bg-[var(--color-surface)] rounded-xl border border-[var(--color-border)] overflow-hidden">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-[var(--color-surface-hover)]/80 text-xs uppercase tracking-wider text-[var(--color-text-muted)] border-b border-[var(--color-border)]">
                  <th className="px-4 py-3 font-medium">Name</th>
                  <th className="px-4 py-3 font-medium">Trace</th>
                  <th className="px-4 py-3 font-medium">Score</th>
                  <th className="px-4 py-3 font-medium">Label</th>
                  <th className="px-4 py-3 font-medium">Method</th>
                  <th className="px-4 py-3 font-medium">Time</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--color-border)]">
                {evals.map(ev => (
                  <tr key={ev.id} className="hover:bg-[var(--color-surface-hover)] transition-colors">
                    <td className="px-4 py-3 text-sm font-medium">{ev.name}</td>
                    <td className="px-4 py-3 font-mono text-xs text-[var(--color-primary)]">{ev.trace_id.substring(0, 8)}…</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1.5">
                        {ev.score >= 0.7 ? <ThumbsUp className="w-3.5 h-3.5 text-green-400" /> : <ThumbsDown className="w-3.5 h-3.5 text-red-400" />}
                        <span className={`font-bold text-sm ${ev.score >= 0.7 ? "text-green-400" : ev.score >= 0.4 ? "text-yellow-400" : "text-red-400"}`}>
                          {ev.score.toFixed(2)}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-xs text-[var(--color-text-muted)]">{ev.label || "—"}</td>
                    <td className="px-4 py-3">
                      <span className="text-[10px] px-2 py-0.5 rounded-full border bg-[var(--color-surface-hover)] text-[var(--color-text-muted)] border-[var(--color-border)] uppercase font-bold tracking-wider">
                        {ev.method}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs text-[var(--color-text-muted)]">{new Date(ev.created_at).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}</td>
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
