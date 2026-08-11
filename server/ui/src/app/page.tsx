"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Activity, Clock, TerminalSquare, AlertCircle, CheckCircle2, Search, Filter, Zap, Check, Minus } from "lucide-react";

interface Trace {
  id: string;
  project: string;
  status: string;
  start_time: string;
  end_time: string | null;
  total_tokens: number;
  is_golden: boolean;
}

export default function Home() {
  const router = useRouter();
  const [traces, setTraces] = useState<Trace[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [selectedTraces, setSelectedTraces] = useState<Set<string>>(new Set());
  const [confirmModal, setConfirmModal] = useState<{isOpen: boolean, action: 'all' | 'selected' | null}>({isOpen: false, action: null});

  const toggleSelectAll = () => {
    if (selectedTraces.size === traces.length && traces.length > 0) setSelectedTraces(new Set());
    else setSelectedTraces(new Set(traces.map(t => t.id)));
  };

  const toggleSelect = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const next = new Set(selectedTraces);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setSelectedTraces(next);
  };

  const executeDelete = () => {
    setLoading(true);
    if (confirmModal.action === 'all') {
      fetch("/api/traces", { method: "DELETE" }).then(() => { fetchTraces(searchQuery, statusFilter); setSelectedTraces(new Set()); });
    } else if (confirmModal.action === 'selected') {
      fetch("/api/traces/batch", {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ids: Array.from(selectedTraces) })
      }).then(() => { fetchTraces(searchQuery, statusFilter); setSelectedTraces(new Set()); });
    }
  };

  const fetchTraces = (search?: string, status?: string) => {
    const params = new URLSearchParams();
    if (search) params.set("search", search);
    if (status) params.set("status", status);
    params.set("limit", "100");
    fetch(`/api/traces?${params.toString()}`)
      .then(r => r.json())
      .then(d => { setTraces(d); setLoading(false); })
      .catch(() => setLoading(false));
  };

  useEffect(() => { fetchTraces(); }, []);

  const handleSearch = () => { setLoading(true); fetchTraces(searchQuery, statusFilter); };

  useEffect(() => {
    const timer = setTimeout(() => { if (!loading) fetchTraces(searchQuery, statusFilter); }, 300);
    return () => clearTimeout(timer);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchQuery, statusFilter]);

  return (
    <div className="flex-1 p-6 pt-12 overflow-y-auto">
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }} className="max-w-6xl mx-auto flex flex-col gap-4">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <Activity className="w-5 h-5 text-[var(--color-primary)]" /> Traces
            </h1>
            <p className="text-sm text-[var(--color-text-muted)] mt-1">Agent execution telemetry</p>
          </div>
          <div className="flex gap-2">
            {selectedTraces.size > 0 && (
              <button
                onClick={() => setConfirmModal({ isOpen: true, action: 'selected' })}
                className="bg-red-500/10 text-red-500 hover:bg-red-500/20 px-3 py-1.5 rounded-lg border border-red-500/20 text-xs font-medium transition-colors flex items-center gap-1.5"
              >
                Delete Selected ({selectedTraces.size})
              </button>
            )}
            <button
              onClick={() => setConfirmModal({ isOpen: true, action: 'all' })}
              className="bg-red-500/10 text-red-500 hover:bg-red-500/20 px-3 py-1.5 rounded-lg border border-red-500/20 text-xs font-medium transition-colors"
            >
              Clear All Traces
            </button>
            <div className="bg-[var(--color-surface)] px-3 py-1.5 rounded-lg border border-[var(--color-border)] flex items-center gap-2 text-xs font-medium">
              <TerminalSquare className="w-3.5 h-3.5 text-[var(--color-primary)]" />
              {traces.length} runs
            </div>
          </div>
        </div>

        {/* Search & Filter Bar */}
        <div className="flex gap-2 items-center">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-text-muted)]" />
            <input
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              placeholder="Search by trace ID or project name…"
              className="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg pl-9 pr-3 py-2 text-sm placeholder:text-[var(--color-text-muted)]/50 focus:border-[var(--color-primary)] focus:outline-none transition-colors"
            />
          </div>
          <div className="relative">
            <Filter className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[var(--color-text-muted)]" />
            <select
              value={statusFilter}
              onChange={e => setStatusFilter(e.target.value)}
              className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg pl-8 pr-3 py-2 text-sm appearance-none cursor-pointer focus:border-[var(--color-primary)] focus:outline-none"
            >
              <option value="">All Status</option>
              <option value="success">Success</option>
              <option value="error">Error</option>
              <option value="running">Running</option>
            </select>
          </div>
        </div>

        {/* Traces Table */}
        {loading ? (
          <div className="flex items-center justify-center p-16">
            <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1, ease: "linear" }}>
              <Activity className="w-6 h-6 text-[var(--color-primary)] opacity-50" />
            </motion.div>
          </div>
        ) : (
          <div className="bg-[var(--color-surface)]/50 backdrop-blur-md rounded-xl border border-[var(--color-border)] overflow-hidden shadow-lg">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-[var(--color-surface-hover)]/80 text-xs uppercase tracking-wider text-[var(--color-text-muted)] border-b border-[var(--color-border)]">
                  <th className="px-4 py-3 font-medium w-8 text-center">
                    <CustomCheckbox 
                      checked={traces.length > 0 && selectedTraces.size === traces.length} 
                      indeterminate={selectedTraces.size > 0 && selectedTraces.size < traces.length}
                      onChange={toggleSelectAll} 
                    />
                  </th>
                  <th className="px-2 py-3 font-medium w-8"></th>
                  <th className="px-4 py-3 font-medium">Trace ID</th>
                  <th className="px-4 py-3 font-medium">Project</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium"><Zap className="w-3.5 h-3.5 inline mr-1" />Tokens</th>
                  <th className="px-4 py-3 font-medium"><Clock className="w-3.5 h-3.5 inline mr-1" />Time</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--color-border)]">
                {traces.map(trace => (
                  <tr key={trace.id} onClick={() => router.push(`/traces/${trace.id}`)} className="hover:bg-[var(--color-surface-hover)] transition-colors group cursor-pointer">
                    <td className="px-4 py-3 text-center">
                      <CustomCheckbox 
                        checked={selectedTraces.has(trace.id)} 
                        onChange={() => {
                          const next = new Set(selectedTraces);
                          if (next.has(trace.id)) next.delete(trace.id);
                          else next.add(trace.id);
                          setSelectedTraces(next);
                        }} 
                      />
                    </td>
                    <td className="px-2 py-3 text-center">
                      {trace.is_golden && <span className="text-yellow-400 text-xs">★</span>}
                    </td>
                    <td className="px-4 py-3">
                      <span className="font-mono text-sm text-[var(--color-primary)] group-hover:text-blue-400 font-bold">{trace.id.substring(0, 8)}…</span>
                    </td>
                    <td className="px-4 py-3 text-sm font-medium">{trace.project}</td>
                    <td className="px-4 py-3">
                      <div className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-semibold ${
                        trace.status === "success" ? "bg-green-500/10 text-green-400 border border-green-500/20"
                        : trace.status === "error" ? "bg-red-500/10 text-red-400 border border-red-500/20"
                        : "bg-yellow-500/10 text-yellow-500 border border-yellow-500/20"
                      }`}>
                        {trace.status === "success" ? <CheckCircle2 className="w-3 h-3" /> : <AlertCircle className="w-3 h-3" />}
                        {trace.status || "unknown"}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-[var(--color-text-muted)]">{(trace.total_tokens || 0).toLocaleString()}</td>
                    <td className="px-4 py-3 text-sm text-[var(--color-text-muted)]">
                      {new Date(trace.start_time).toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit", second: "2-digit" })}
                    </td>
                  </tr>
                ))}
                {traces.length === 0 && (
                  <tr>
                    <td colSpan={7} className="p-12 text-center">
                      <div className="flex flex-col items-center gap-2 text-[var(--color-text-muted)]">
                        <TerminalSquare className="w-8 h-8 opacity-20" />
                        <p className="text-sm">No traces found.</p>
                      </div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </motion.div>

      <ConfirmModal 
        isOpen={confirmModal.isOpen} 
        onClose={() => setConfirmModal({ isOpen: false, action: null })}
        onConfirm={executeDelete}
        title={confirmModal.action === 'all' ? "Clear All Traces" : "Delete Selected Traces"}
        message={confirmModal.action === 'all' 
          ? "Are you sure you want to completely wipe all traces from the database? This action cannot be undone." 
          : `Are you sure you want to delete ${selectedTraces.size} selected trace(s)?`}
        confirmText="Delete"
      />
    </div>
  );
}

function ConfirmModal({ isOpen, onClose, onConfirm, title, message, confirmText = "Confirm" }: any) {
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="bg-[var(--color-surface)] border border-[var(--color-border)] p-6 rounded-xl shadow-2xl max-w-md w-full">
        <h3 className="text-lg font-bold mb-2">{title}</h3>
        <p className="text-[var(--color-text-muted)] text-sm mb-6">{message}</p>
        <div className="flex justify-end gap-3">
          <button onClick={onClose} className="px-4 py-2 rounded-lg text-sm font-medium border border-[var(--color-border)] hover:bg-[var(--color-surface-hover)] transition-colors">Cancel</button>
          <button onClick={() => { onConfirm(); onClose(); }} className="px-4 py-2 rounded-lg text-sm font-medium bg-red-500 hover:bg-red-600 text-white transition-colors">{confirmText}</button>
        </div>
      </motion.div>
    </div>
  );
}

function CustomCheckbox({ checked, indeterminate, onChange }: any) {
  return (
    <div 
      onClick={(e) => { e.stopPropagation(); onChange(); }} 
      className={`w-4 h-4 rounded flex items-center justify-center cursor-pointer transition-colors border shadow-sm mx-auto ${
        checked || indeterminate 
          ? 'bg-[var(--color-primary)] border-[var(--color-primary)]' 
          : 'bg-black/20 border-[var(--color-text-muted)]/40 hover:border-[var(--color-primary)] hover:bg-[var(--color-surface-hover)]'
      }`}
    >
      {checked && <Check className="w-3 h-3 text-white stroke-[3.5]" />}
      {!checked && indeterminate && <Minus className="w-3 h-3 text-white stroke-[3.5]" />}
    </div>
  );
}
