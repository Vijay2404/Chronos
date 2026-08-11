"use client";

import { useEffect, useState, use, useCallback } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowLeft, Box, Code, Database, Clock, Terminal, Star, ThumbsUp, ThumbsDown, MessageSquare, GitBranch } from "lucide-react";
import { ReactFlow, Background, Controls, MiniMap, useNodesState, useEdgesState, MarkerType, Handle, Position } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { JsonViewer } from "@/components/JsonViewer";

interface Span { id: string; name: string; start_time: string; end_time: string | null; duration_ms: number; inputs?: any; outputs?: any; prompt_tokens: number; completion_tokens: number; model: string; }
interface Checkpoint { id: string; node: string; timestamp: string; is_binary: boolean; state?: any; step_index: number; }
interface TraceInfo { id: string; project: string; status: string; is_golden: boolean; total_tokens: number; }

function CustomNode({ data }: { data: any }) {
  return (
    <div className="group relative flex flex-col items-center justify-center min-w-[55px] max-w-[85px] bg-[var(--color-surface)] border border-[var(--color-border)] rounded-md px-1 py-1 shadow-sm transition-colors hover:border-[var(--color-primary)]">
      <Handle type="target" position={Position.Top} className="!w-1 !h-1 !bg-[var(--color-primary)] !border-[var(--color-border)]" />
      
      <div className="font-medium text-[7px] tracking-wide text-white mb-0.5 whitespace-nowrap overflow-hidden text-ellipsis w-full text-center">
        {data.name}
      </div>
      
      <div className="flex items-center justify-center flex-wrap gap-0.5 text-[6px] font-mono w-full">
        {data.duration_ms > 0 && (
          <span className="text-[var(--color-text-muted)] bg-[var(--color-background)] px-0.5 py-px rounded border border-[var(--color-border)] flex items-center gap-0.5">
            <Clock className="w-1.5 h-1.5" />
            {Math.round(data.duration_ms)}ms
          </span>
        )}
        {data.tokens > 0 && (
          <span className="text-orange-400 bg-orange-500/10 px-0.5 py-px rounded border border-orange-500/20">
            {data.tokens}t
          </span>
        )}
      </div>

      <Handle type="source" position={Position.Bottom} className="!w-1 !h-1 !bg-[var(--color-secondary)] !border-[var(--color-border)]" />
    </div>
  );
}

const nodeTypes = { custom: CustomNode };

export default function TraceDetail({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [trace, setTrace] = useState<TraceInfo | null>(null);
  const [spans, setSpans] = useState<Span[]>([]);
  const [checkpoints, setCheckpoints] = useState<Checkpoint[]>([]);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedItem, setSelectedItem] = useState<{ type: "span" | "checkpoint"; data: any } | null>(null);

  // State diffing
  const [diffA, setDiffA] = useState<number | null>(null);
  const [diffB, setDiffB] = useState<number | null>(null);
  const [diffResult, setDiffResult] = useState<any>(null);

  // Panels
  const [showScorePanel, setShowScorePanel] = useState(false);
  const [showAnnotatePanel, setShowAnnotatePanel] = useState(false);

  useEffect(() => {
    Promise.all([
      fetch(`/api/traces/${id}`).then(r => r.json()),
      fetch(`/api/traces/${id}/spans`).then(r => r.json()),
      fetch(`/api/traces/${id}/checkpoints`).then(r => r.json()),
    ]).then(([traceData, spansData, checkpointsData]) => {
      setTrace(traceData);
      setSpans(spansData);
      setCheckpoints(checkpointsData);

      const newNodes = spansData.map((span: Span, index: number) => ({
        id: span.id,
        position: { x: 250, y: index * 100 + 50 },
        type: 'custom',
        data: {
          name: span.name,
          duration_ms: span.duration_ms,
          tokens: span.prompt_tokens + span.completion_tokens
        },
      }));

      const newEdges = spansData.slice(1).map((span: Span, index: number) => ({
        id: `e-${spansData[index].id}-${span.id}`,
        source: spansData[index].id,
        target: span.id,
        animated: true,
        style: { stroke: "var(--color-border)", strokeWidth: 2 },
        markerEnd: { type: MarkerType.ArrowClosed, color: "var(--color-border)" },
      }));

      setNodes(newNodes);
      setEdges(newEdges);
    });
  }, [id, setNodes, setEdges]);

  const onNodeClick = useCallback((_: any, node: any) => {
    const span = spans.find(s => s.id === node.id);
    if (span) setSelectedItem({ type: "span", data: span });
  }, [spans]);

  const toggleGolden = async () => {
    if (!trace) return;
    const endpoint = trace.is_golden ? "unpin" : "pin";
    await fetch(`/api/traces/${id}/${endpoint}`, { method: "POST" });
    setTrace({ ...trace, is_golden: !trace.is_golden });
  };

  // Compute state diff between two checkpoints
  useEffect(() => {
    if (diffA !== null && diffB !== null) {
      const cpA = checkpoints[diffA];
      const cpB = checkpoints[diffB];
      if (cpA?.state && cpB?.state) {
        // Simple deep diff: find keys that changed
        const diff: Record<string, { before: any; after: any }> = {};
        const allKeys = new Set([...Object.keys(cpA.state), ...Object.keys(cpB.state)]);
        allKeys.forEach(key => {
          const a = JSON.stringify(cpA.state[key]);
          const b = JSON.stringify(cpB.state[key]);
          if (a !== b) {
            diff[key] = { before: cpA.state[key], after: cpB.state[key] };
          }
        });
        setDiffResult(diff);
      } else {
        setDiffResult(null);
      }
    }
  }, [diffA, diffB, checkpoints]);

  return (
    <div className="flex flex-col flex-1 h-full bg-[var(--color-background)] overflow-hidden">
      {/* Header */}
      <div className="h-14 border-b border-[var(--color-border)] flex items-center px-5 gap-3 shrink-0 bg-[var(--color-surface)]/50 backdrop-blur-md z-10">
        <Link href="/">
          <motion.div whileHover={{ x: -3 }} className="p-1.5 rounded-lg hover:bg-[var(--color-surface-hover)] transition-colors cursor-pointer text-[var(--color-text-muted)]">
            <ArrowLeft className="w-4 h-4" />
          </motion.div>
        </Link>
        <h1 className="text-base font-bold">Trace</h1>
        <span className="font-mono text-xs text-[var(--color-primary)] bg-[var(--color-primary)]/10 px-2 py-0.5 rounded border border-[var(--color-primary)]/20">{id.substring(0, 8)}</span>
        {trace && (
          <>
            <span className="text-xs px-2 py-0.5 rounded font-semibold bg-[var(--color-surface)] border border-[var(--color-border)] text-[var(--color-text-muted)] flex items-center gap-1.5">
              <Box className="w-3 h-3 text-[var(--color-secondary)]" /> {trace.project}
            </span>
            <span className={`text-xs px-2 py-0.5 rounded font-semibold ${trace.status === "success" ? "bg-green-500/10 text-green-400 border border-green-500/20" : "bg-red-500/10 text-red-400 border border-red-500/20"}`}>{trace.status}</span>
            {trace.total_tokens > 0 && <span className="text-xs text-orange-400">{trace.total_tokens.toLocaleString()} tokens</span>}
          </>
        )}
        <div className="flex-1" />
        {/* Actions */}
        <button onClick={toggleGolden} className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${trace?.is_golden ? "bg-yellow-500/10 text-yellow-400 border-yellow-500/30" : "bg-[var(--color-surface)] text-[var(--color-text-muted)] border-[var(--color-border)] hover:text-yellow-400"}`}>
          <Star className="w-3.5 h-3.5" /> {trace?.is_golden ? "Pinned" : "Pin as Golden"}
        </button>
        <button onClick={() => setShowScorePanel(!showScorePanel)} className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-[var(--color-surface)] text-[var(--color-text-muted)] border border-[var(--color-border)] hover:text-[var(--color-secondary)] transition-colors">
          <ThumbsUp className="w-3.5 h-3.5" /> Score
        </button>
        <button onClick={() => setShowAnnotatePanel(!showAnnotatePanel)} className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-[var(--color-surface)] text-[var(--color-text-muted)] border border-[var(--color-border)] hover:text-blue-400 transition-colors">
          <MessageSquare className="w-3.5 h-3.5" /> Annotate
        </button>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Left Column: Checkpoints Timeline */}
        <div className="w-[20%] h-full p-4 overflow-y-auto bg-[var(--color-surface)]/20 flex flex-col border-r border-[var(--color-border)]">
          <div className="flex items-center justify-between mb-4 shrink-0">
            <h2 className="text-xs font-bold uppercase tracking-widest text-[var(--color-text-muted)] flex items-center gap-1.5">
              <Database className="w-3.5 h-3.5" /> Checkpoints
            </h2>
          </div>
          
          {checkpoints.length >= 2 && (
            <div className="mb-4 shrink-0 flex flex-col gap-2 bg-[var(--color-surface)] p-2 rounded-lg border border-[var(--color-border)]">
              <div className="flex items-center gap-2 text-[10px]">
                <GitBranch className="w-3 h-3 text-[var(--color-text-muted)]" />
                <span className="text-[var(--color-text-muted)] font-medium">Diff Checkpoints:</span>
              </div>
              <div className="flex items-center justify-between gap-1">
                <select value={diffA ?? ""} onChange={e => setDiffA(e.target.value ? parseInt(e.target.value) : null)} className="bg-[var(--color-background)] border border-[var(--color-border)] rounded px-1.5 py-1 text-[10px] w-[45%]">
                  <option value="">A</option>
                  {checkpoints.map((cp, i) => <option key={i} value={i}>#{i} {cp.node}</option>)}
                </select>
                <span className="text-[10px] text-[var(--color-text-muted)]">→</span>
                <select value={diffB ?? ""} onChange={e => setDiffB(e.target.value ? parseInt(e.target.value) : null)} className="bg-[var(--color-background)] border border-[var(--color-border)] rounded px-1.5 py-1 text-[10px] w-[45%]">
                  <option value="">B</option>
                  {checkpoints.map((cp, i) => <option key={i} value={i}>#{i} {cp.node}</option>)}
                </select>
              </div>
            </div>
          )}

          {/* Diff Result */}
          {diffResult && Object.keys(diffResult).length > 0 && (
            <div className="mb-4 bg-[#0a0a0f] border border-blue-500/20 rounded-lg p-3 space-y-2 shrink-0">
              <div className="text-[10px] uppercase tracking-wider text-[var(--color-text-muted)] font-bold">State Changes</div>
              {Object.entries(diffResult).map(([key, val]: [string, any]) => (
                <div key={key} className="text-[10px] font-mono break-all">
                  <div className="text-blue-400 font-bold mb-0.5">{key}:</div>
                  <div className="pl-2 text-red-400/80 line-through">{JSON.stringify(val.before, null, 1)?.substring(0, 100)}</div>
                  <div className="pl-2 text-green-400">{JSON.stringify(val.after, null, 1)?.substring(0, 100)}</div>
                </div>
              ))}
            </div>
          )}
          {diffResult && Object.keys(diffResult).length === 0 && diffA !== null && diffB !== null && (
            <div className="mb-4 text-xs text-[var(--color-text-muted)] italic shrink-0">No state changes between these checkpoints.</div>
          )}

          <div className="relative space-y-3 flex-1 overflow-y-auto pt-1 pl-1">
            <div className="absolute left-[11px] top-1 bottom-0 w-[2px] bg-[var(--color-border)] z-0" />
            {checkpoints.map((cp, i) => (
              <div key={cp.id} onClick={() => setSelectedItem({ type: "checkpoint", data: cp })} className="relative cursor-pointer group pl-6">
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.05 }} className="absolute left-[4px] top-3 w-2 h-2 rounded-full bg-[var(--color-background)] border-[1.5px] border-[var(--color-secondary)] group-hover:scale-150 transition-transform z-10 origin-center" />
                <motion.div initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.05, duration: 0.2 }} className={`bg-[var(--color-surface)] border p-2.5 rounded-md transition-colors ${selectedItem?.data?.id === cp.id ? 'border-[var(--color-secondary)]' : 'border-[var(--color-border)] group-hover:border-[var(--color-text-muted)]'}`}>
                  <div className="flex justify-between items-center gap-2">
                    <span className="font-mono text-[11px] text-white font-medium break-all">#{cp.step_index} {cp.node}</span>
                    <span className="text-[9px] text-[var(--color-text-muted)] flex items-center gap-1 shrink-0"><Clock className="w-2 h-2" />{new Date(cp.timestamp).toLocaleTimeString()}</span>
                  </div>
                  {cp.is_binary ? (
                    <span className="text-[8px] px-1 py-0.5 bg-yellow-500/10 text-yellow-500 rounded border border-yellow-500/20 uppercase font-bold mt-1.5 inline-block">binary</span>
                  ) : (
                    <span className="text-[8px] px-1 py-0.5 bg-blue-500/10 text-blue-400 rounded border border-blue-500/20 uppercase font-bold mt-1.5 inline-block">json</span>
                  )}
                </motion.div>
              </div>
            ))}
            {checkpoints.length === 0 && <div className="text-xs text-[var(--color-text-muted)] italic">No checkpoints.</div>}
          </div>
        </div>

        {/* Center Column: Inspector */}
        <div className="w-[40%] h-full p-4 overflow-y-auto bg-[var(--color-surface)]/20 border-r border-[var(--color-border)]">
          <h2 className="text-xs font-bold uppercase tracking-widest text-[var(--color-text-muted)] mb-4 flex items-center gap-1.5">
            <Code className="w-3.5 h-3.5" /> Inspector
          </h2>

          {selectedItem ? (
            <motion.div key={selectedItem.data.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
              <div className="flex gap-2 mb-4">
                <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold uppercase tracking-wider ${selectedItem.type === "span" ? "bg-[var(--color-primary)]/10 text-[var(--color-primary)] border border-[var(--color-primary)]/20" : "bg-[var(--color-secondary)]/10 text-[var(--color-secondary)] border border-[var(--color-secondary)]/20"}`}>{selectedItem.type}</span>
                <span className="text-[11px] text-white font-mono py-0.5 break-all">{selectedItem.data.name || selectedItem.data.node}</span>
              </div>

              {selectedItem.type === "span" && selectedItem.data.inputs && (
                <div className="mb-4">
                  <div className="text-[10px] uppercase tracking-wider text-[var(--color-text-muted)] mb-1.5 font-bold">Input</div>
                  <div className="bg-[#0a0a0f] border border-[var(--color-border)] rounded-md overflow-hidden"><JsonViewer data={selectedItem.data.inputs} /></div>
                </div>
              )}
              {selectedItem.type === "span" && selectedItem.data.outputs && (
                <div className="mb-4">
                  <div className="text-[10px] uppercase tracking-wider text-[var(--color-text-muted)] mb-1.5 font-bold">Output</div>
                  <div className="bg-[#0a0a0f] border border-[var(--color-border)] rounded-md overflow-hidden"><JsonViewer data={selectedItem.data.outputs} /></div>
                </div>
              )}

              {selectedItem.type === "checkpoint" && (
                <div>
                  <div className="text-[10px] uppercase tracking-wider text-[var(--color-text-muted)] mb-1.5 font-bold">State</div>
                  <div className="bg-[#0a0a0f] border border-[var(--color-border)] rounded-md overflow-hidden"><JsonViewer data={selectedItem.data.state || { note: "Binary state (cloudpickle) — not displayable in UI" }} /></div>
                </div>
              )}
            </motion.div>
          ) : (
            <div className="h-[200px] flex flex-col items-center justify-center text-[var(--color-text-muted)] gap-2 opacity-50">
              <Box className="w-8 h-8" />
              <p className="text-xs">Select a node or checkpoint.</p>
            </div>
          )}
        </div>

        {/* Right Column: React Flow Graph */}
        <div className="w-[40%] h-full flex flex-col bg-[var(--color-background)]">
          <div className="flex items-center justify-between px-4 pt-4 mb-4 shrink-0">
            <h2 className="text-xs font-bold uppercase tracking-widest text-[var(--color-text-muted)] flex items-center gap-1.5">
              <Terminal className="w-3.5 h-3.5" /> Execution Graph
            </h2>
          </div>
          <div className="flex-1 relative">
            <ReactFlow style={{ width: "100%", height: "100%" }} nodes={nodes} edges={edges} nodeTypes={nodeTypes} onNodesChange={onNodesChange} onEdgesChange={onEdgesChange} onNodeClick={onNodeClick} fitView colorMode="dark">
              <Background gap={16} size={1} color="var(--color-border)" />
              <Controls className="bg-[var(--color-surface)] border-[var(--color-border)] fill-white" />
            </ReactFlow>
          </div>
        </div>
      </div>

      {/* Score Panel Overlay */}
      <AnimatePresence>
        {showScorePanel && <ScorePanel traceId={id} onClose={() => setShowScorePanel(false)} />}
      </AnimatePresence>

      {/* Annotate Panel Overlay */}
      <AnimatePresence>
        {showAnnotatePanel && <AnnotatePanel traceId={id} onClose={() => setShowAnnotatePanel(false)} />}
      </AnimatePresence>
    </div>
  );
}

function ScorePanel({ traceId, onClose }: { traceId: string; onClose: () => void }) {
  const [name, setName] = useState("quality");
  const [score, setScore] = useState("1.0");
  const [label, setLabel] = useState("");
  const [comment, setComment] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const submit = async () => {
    setSubmitting(true);
    await fetch("/api/evaluations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ trace_id: traceId, name, score: parseFloat(score), label: label || null, comment: comment || null }),
    });
    setSubmitting(false);
    onClose();
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="absolute inset-0 z-50 bg-black/50 flex items-center justify-center" onClick={onClose}>
      <motion.div initial={{ scale: 0.95 }} animate={{ scale: 1 }} exit={{ scale: 0.95 }} className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-6 w-96 space-y-4" onClick={e => e.stopPropagation()}>
        <h3 className="text-base font-bold flex items-center gap-2"><ThumbsUp className="w-4 h-4 text-[var(--color-secondary)]" /> Score This Trace</h3>
        <input value={name} onChange={e => setName(e.target.value)} placeholder="Metric name" className="w-full bg-[var(--color-background)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-sm" />
        <input type="number" step="0.1" min="0" max="1" value={score} onChange={e => setScore(e.target.value)} className="w-full bg-[var(--color-background)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-sm" />
        <input value={label} onChange={e => setLabel(e.target.value)} placeholder="Label (optional)" className="w-full bg-[var(--color-background)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-sm" />
        <textarea value={comment} onChange={e => setComment(e.target.value)} placeholder="Comment (optional)" rows={2} className="w-full bg-[var(--color-background)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-sm resize-none" />
        <div className="flex gap-2">
          <button onClick={onClose} className="flex-1 px-3 py-2 rounded-lg text-sm border border-[var(--color-border)] text-[var(--color-text-muted)]">Cancel</button>
          <button onClick={submit} disabled={submitting} className="flex-1 px-3 py-2 rounded-lg text-sm bg-[var(--color-secondary)] text-white font-medium disabled:opacity-50">{submitting ? "Saving…" : "Save Score"}</button>
        </div>
      </motion.div>
    </motion.div>
  );
}

function AnnotatePanel({ traceId, onClose }: { traceId: string; onClose: () => void }) {
  const [rating, setRating] = useState(1);
  const [label, setLabel] = useState("");
  const [comment, setComment] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const submit = async () => {
    setSubmitting(true);
    await fetch("/api/annotations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ trace_id: traceId, rating, label: label || null, comment: comment || null }),
    });
    setSubmitting(false);
    onClose();
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="absolute inset-0 z-50 bg-black/50 flex items-center justify-center" onClick={onClose}>
      <motion.div initial={{ scale: 0.95 }} animate={{ scale: 1 }} exit={{ scale: 0.95 }} className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-6 w-96 space-y-4" onClick={e => e.stopPropagation()}>
        <h3 className="text-base font-bold flex items-center gap-2"><MessageSquare className="w-4 h-4 text-blue-400" /> Annotate This Trace</h3>
        <div className="flex gap-2 items-center">
          <span className="text-sm text-[var(--color-text-muted)]">Rating:</span>
          <button onClick={() => setRating(1)} className={`p-1.5 rounded ${rating === 1 ? "bg-green-500/20 text-green-400" : "text-[var(--color-text-muted)]"}`}><ThumbsUp className="w-4 h-4" /></button>
          <button onClick={() => setRating(-1)} className={`p-1.5 rounded ${rating === -1 ? "bg-red-500/20 text-red-400" : "text-[var(--color-text-muted)]"}`}><ThumbsDown className="w-4 h-4" /></button>
        </div>
        <input value={label} onChange={e => setLabel(e.target.value)} placeholder="Label (e.g. hallucination, correct)" className="w-full bg-[var(--color-background)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-sm" />
        <textarea value={comment} onChange={e => setComment(e.target.value)} placeholder="Notes…" rows={3} className="w-full bg-[var(--color-background)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-sm resize-none" />
        <div className="flex gap-2">
          <button onClick={onClose} className="flex-1 px-3 py-2 rounded-lg text-sm border border-[var(--color-border)] text-[var(--color-text-muted)]">Cancel</button>
          <button onClick={submit} disabled={submitting} className="flex-1 px-3 py-2 rounded-lg text-sm bg-blue-500 text-white font-medium disabled:opacity-50">{submitting ? "Saving…" : "Save"}</button>
        </div>
      </motion.div>
    </motion.div>
  );
}
