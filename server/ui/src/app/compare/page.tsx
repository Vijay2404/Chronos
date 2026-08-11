"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Columns2, Activity, ArrowRight } from "lucide-react";
import { JsonViewer } from "@/components/JsonViewer";

interface Trace { id: string; project: string; status: string; start_time: string; }
interface Span { id: string; name: string; start_time: string; duration_ms: number; inputs?: any; outputs?: any; prompt_tokens: number; completion_tokens: number; }

export default function ComparePage() {
  const [traces, setTraces] = useState<Trace[]>([]);
  const [traceA, setTraceA] = useState<string>("");
  const [traceB, setTraceB] = useState<string>("");
  const [spansA, setSpansA] = useState<Span[]>([]);
  const [spansB, setSpansB] = useState<Span[]>([]);
  const [comparing, setComparing] = useState(false);

  useEffect(() => {
    fetch("/api/traces?limit=50").then(r => r.json()).then(setTraces);
  }, []);

  const doCompare = async () => {
    if (!traceA || !traceB) return;
    setComparing(true);
    const [a, b] = await Promise.all([
      fetch(`/api/traces/${traceA}/spans`).then(r => r.json()),
      fetch(`/api/traces/${traceB}/spans`).then(r => r.json()),
    ]);
    setSpansA(a);
    setSpansB(b);
    setComparing(false);
  };

  return (
    <div className="flex-1 p-6 pt-12 overflow-y-auto">
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="max-w-6xl mx-auto flex flex-col gap-5">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Columns2 className="w-5 h-5 text-[var(--color-primary)]" /> Trace Comparison
          </h1>
          <p className="text-sm text-[var(--color-text-muted)] mt-1">Select two traces to diff their spans, prompts, and outputs side-by-side.</p>
        </div>

        {/* Selectors */}
        <div className="flex items-center gap-3">
          <select value={traceA} onChange={e => setTraceA(e.target.value)} className="flex-1 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-sm font-mono text-[var(--color-text)]">
            <option value="">Select Trace A</option>
            {traces.map(t => <option key={t.id} value={t.id}>{t.id.substring(0, 8)}… · {t.project} · {t.status}</option>)}
          </select>
          <ArrowRight className="w-5 h-5 text-[var(--color-text-muted)] shrink-0" />
          <select value={traceB} onChange={e => setTraceB(e.target.value)} className="flex-1 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-sm font-mono text-[var(--color-text)]">
            <option value="">Select Trace B</option>
            {traces.map(t => <option key={t.id} value={t.id}>{t.id.substring(0, 8)}… · {t.project} · {t.status}</option>)}
          </select>
          <button onClick={doCompare} disabled={!traceA || !traceB || comparing} className="px-4 py-2 bg-[var(--color-primary)] text-white rounded-lg text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-40">
            {comparing ? "Loading…" : "Compare"}
          </button>
        </div>

        {/* Side-by-side comparison */}
        {spansA.length > 0 && spansB.length > 0 && (
          <div className="grid grid-cols-2 gap-4">
            {/* Headers */}
            <div className="text-xs font-bold uppercase tracking-widest text-blue-400 px-1">Trace A · {traceA.substring(0, 8)}…</div>
            <div className="text-xs font-bold uppercase tracking-widest text-purple-400 px-1">Trace B · {traceB.substring(0, 8)}…</div>

            {/* Render spans aligned by index */}
            {Array.from({ length: Math.max(spansA.length, spansB.length) }).map((_, i) => {
              const sa = spansA[i];
              const sb = spansB[i];
              const nameMatch = sa && sb && sa.name === sb.name;
              return (
                <motion.div key={i} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.05 }} className="contents">
                  <SpanCard span={sa} highlight={!nameMatch} />
                  <SpanCard span={sb} highlight={!nameMatch} />
                </motion.div>
              );
            })}
          </div>
        )}
      </motion.div>
    </div>
  );
}

function SpanCard({ span, highlight }: { span?: Span; highlight: boolean }) {
  const [expanded, setExpanded] = useState(false);
  if (!span) return <div className="bg-[var(--color-surface)]/30 border border-dashed border-[var(--color-border)] rounded-lg p-4 flex items-center justify-center text-xs text-[var(--color-text-muted)]">—</div>;
  return (
    <div className={`bg-[var(--color-surface)] border rounded-lg p-4 cursor-pointer transition-colors ${highlight ? "border-yellow-500/50" : "border-[var(--color-border)]"}`} onClick={() => setExpanded(!expanded)}>
      <div className="flex justify-between items-center">
        <span className="font-mono text-sm font-bold text-[var(--color-primary)]">{span.name}</span>
        <span className="text-xs text-[var(--color-text-muted)]">{span.duration_ms ? `${Math.round(span.duration_ms)}ms` : "—"}</span>
      </div>
      {span.prompt_tokens > 0 && (
        <div className="text-[10px] text-[var(--color-text-muted)] mt-1">
          {span.prompt_tokens} in / {span.completion_tokens} out tokens
        </div>
      )}
      {expanded && (
        <div className="mt-3 space-y-2">
          {span.inputs && <><div className="text-[10px] uppercase tracking-wider text-[var(--color-text-muted)]">Input</div><JsonViewer data={span.inputs} /></>}
          {span.outputs && <><div className="text-[10px] uppercase tracking-wider text-[var(--color-text-muted)]">Output</div><JsonViewer data={span.outputs} /></>}
        </div>
      )}
    </div>
  );
}
