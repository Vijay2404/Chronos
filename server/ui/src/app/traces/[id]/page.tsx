"use client";

import { useEffect, useState, use, useCallback } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowLeft, Box, Code, Database, Clock, Terminal } from "lucide-react";
import { 
  ReactFlow, 
  Background, 
  Controls, 
  MiniMap,
  useNodesState,
  useEdgesState,
  MarkerType
} from '@xyflow/react';

interface Span {
  id: string;
  name: string;
  start_time: string;
  end_time: string | null;
  inputs?: any;
  outputs?: any;
}

interface Checkpoint {
  id: string;
  node: string;
  timestamp: string;
  is_binary: boolean;
  state?: any;
}

// A simple custom JSON viewer component with basic syntax highlighting
const JsonViewer = ({ data }: { data: any }) => {
  if (!data) return <span className="text-[var(--color-text-muted)]">null</span>;
  const jsonStr = JSON.stringify(data, null, 2);
  
  // Basic Regex for coloring
  const highlighted = jsonStr
    .replace(/(".*?"|'.*?')(?=\s*:)/g, '<span class="text-blue-400">$1</span>') // Keys
    .replace(/:\s*(".*?"|'.*?')/g, ': <span class="text-green-400">$1</span>') // Strings
    .replace(/:\s*(-?\d+\.?\d*)/g, ': <span class="text-orange-400">$1</span>') // Numbers
    .replace(/:\s*(true|false|null)/g, ': <span class="text-purple-400">$1</span>'); // Booleans

  return (
    <pre 
      className="text-xs font-mono p-4 rounded-xl bg-[#0a0a0f] border border-[var(--color-border)] shadow-inner overflow-auto whitespace-pre-wrap leading-relaxed"
      dangerouslySetInnerHTML={{ __html: highlighted }}
    />
  );
};

export default function TraceDetail({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const [spans, setSpans] = useState<Span[]>([]);
  const [checkpoints, setCheckpoints] = useState<Checkpoint[]>([]);
  
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  
  const [selectedItem, setSelectedItem] = useState<{type: 'span'|'checkpoint', data: any} | null>(null);

  useEffect(() => {
    Promise.all([
      fetch(`/api/traces/${resolvedParams.id}/spans`).then(res => res.json()),
      fetch(`/api/traces/${resolvedParams.id}/checkpoints`).then(res => res.json())
    ]).then(([spansData, checkpointsData]) => {
      setSpans(spansData);
      setCheckpoints(checkpointsData);
      
      // Build React Flow graph
      const newNodes = spansData.map((span: Span, index: number) => ({
        id: span.id,
        position: { x: 250, y: index * 120 + 50 },
        data: { 
          label: (
            <div className="flex flex-col gap-1 items-center justify-center p-2 w-48">
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[var(--color-primary)]">
                <Box className="w-3 h-3" /> {span.name}
              </div>
              <div className="text-[10px] text-gray-400">
                {new Date(span.start_time).toLocaleTimeString()}
              </div>
            </div>
          ) 
        },
        style: {
          background: 'var(--color-surface)',
          border: '1px solid var(--color-border)',
          borderRadius: '8px',
          color: 'white',
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
        }
      }));
      
      const newEdges = spansData.slice(1).map((span: Span, index: number) => ({
        id: `e-${spansData[index].id}-${span.id}`,
        source: spansData[index].id,
        target: span.id,
        animated: true,
        style: { stroke: 'var(--color-primary)', strokeWidth: 2 },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: 'var(--color-primary)',
        },
      }));
      
      setNodes(newNodes);
      setEdges(newEdges);
    });
  }, [resolvedParams.id, setNodes, setEdges]);

  const onNodeClick = useCallback((_: any, node: any) => {
    const span = spans.find(s => s.id === node.id);
    if (span) setSelectedItem({ type: 'span', data: span });
  }, [spans]);

  return (
    <div className="flex flex-col h-full bg-[var(--color-background)]">
      {/* Header */}
      <div className="h-16 border-b border-[var(--color-border)] flex items-center px-6 gap-4 shrink-0 bg-[var(--color-surface)]/50 backdrop-blur-md z-10">
        <Link href="/">
          <motion.div whileHover={{ x: -3 }} className="p-2 rounded-lg hover:bg-[var(--color-surface-hover)] transition-colors cursor-pointer text-[var(--color-text-muted)]">
            <ArrowLeft className="w-5 h-5" />
          </motion.div>
        </Link>
        <div>
          <h1 className="text-xl font-bold flex items-center gap-2">
            Trace Visualizer 
            <span className="text-sm font-mono text-[var(--color-primary)] bg-[var(--color-primary)]/10 px-2 py-0.5 rounded border border-[var(--color-primary)]/20">
              {resolvedParams.id.split('-')[0]}
            </span>
          </h1>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Left: React Flow Graph */}
        <div className="w-1/2 border-r border-[var(--color-border)] relative bg-black/20">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={onNodeClick}
            fitView
            colorMode="dark"
          >
            <Background gap={12} size={1} color="rgba(255,255,255,0.05)" />
            <Controls className="bg-[var(--color-surface)] border-[var(--color-border)] fill-white" />
            <MiniMap 
              className="bg-[var(--color-surface)] border-[var(--color-border)]" 
              nodeColor="var(--color-primary)"
              maskColor="rgba(0,0,0,0.5)"
            />
          </ReactFlow>
          
          <div className="absolute top-4 left-4 pointer-events-none">
            <div className="bg-[var(--color-surface)]/80 backdrop-blur px-3 py-1.5 rounded-full border border-[var(--color-border)] text-xs font-medium flex items-center gap-2">
              <Terminal className="w-3 h-3 text-[var(--color-primary)]" />
              Agent Execution Graph
            </div>
          </div>
        </div>

        {/* Right: Inspector & Checkpoints Timeline */}
        <div className="w-1/2 flex flex-col bg-[var(--color-surface)]/30">
          {/* Top Half: State Checkpoints Timeline */}
          <div className="h-1/2 border-b border-[var(--color-border)] p-6 overflow-y-auto">
            <h2 className="text-sm font-bold uppercase tracking-widest text-[var(--color-text-muted)] mb-6 flex items-center gap-2">
              <Database className="w-4 h-4" /> State Checkpoints
            </h2>
            
            <div className="relative pl-4 border-l-2 border-[var(--color-border)] space-y-6">
              {checkpoints.map((cp, i) => (
                <motion.div 
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.1 }}
                  key={cp.id}
                  onClick={() => setSelectedItem({ type: 'checkpoint', data: cp })}
                  className="relative cursor-pointer group"
                >
                  <div className="absolute -left-[23px] top-1.5 w-3 h-3 rounded-full bg-[var(--color-background)] border-2 border-[var(--color-secondary)] group-hover:scale-125 transition-transform" />
                  
                  <div className="bg-[var(--color-surface)] border border-[var(--color-border)] p-4 rounded-xl shadow-sm group-hover:border-[var(--color-secondary)] transition-colors">
                    <div className="flex justify-between items-center mb-2">
                      <span className="font-mono text-sm text-[var(--color-secondary)] font-bold">Node: {cp.node}</span>
                      <span className="text-xs text-[var(--color-text-muted)] flex items-center gap-1">
                        <Clock className="w-3 h-3" /> {new Date(cp.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    {cp.is_binary ? (
                      <span className="text-[10px] px-2 py-0.5 bg-yellow-500/10 text-yellow-500 rounded-full border border-yellow-500/20 uppercase font-bold tracking-wider">
                        Cloudpickle Binary
                      </span>
                    ) : (
                      <span className="text-[10px] px-2 py-0.5 bg-blue-500/10 text-blue-400 rounded-full border border-blue-500/20 uppercase font-bold tracking-wider">
                        JSON State
                      </span>
                    )}
                  </div>
                </motion.div>
              ))}
              {checkpoints.length === 0 && (
                <div className="text-sm text-[var(--color-text-muted)] italic">No state checkpoints recorded.</div>
              )}
            </div>
          </div>

          {/* Bottom Half: Inspector */}
          <div className="h-1/2 p-6 overflow-y-auto">
             <h2 className="text-sm font-bold uppercase tracking-widest text-[var(--color-text-muted)] mb-4 flex items-center gap-2">
              <Code className="w-4 h-4" /> Payload Inspector
            </h2>
            
            {selectedItem ? (
              <motion.div 
                key={selectedItem.data.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="h-full"
              >
                <div className="mb-3 flex gap-2">
                  <span className={`text-xs px-2 py-1 rounded font-bold uppercase tracking-wider ${
                    selectedItem.type === 'span' 
                      ? 'bg-[var(--color-primary)]/20 text-[var(--color-primary)]' 
                      : 'bg-[var(--color-secondary)]/20 text-[var(--color-secondary)]'
                  }`}>
                    {selectedItem.type}
                  </span>
                  <span className="text-xs text-[var(--color-text-muted)] font-mono py-1">
                    {selectedItem.data.id}
                  </span>
                </div>
                <JsonViewer data={selectedItem.data.inputs || selectedItem.data.state || selectedItem.data} />
              </motion.div>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-[var(--color-text-muted)] gap-3 opacity-50">
                <Box className="w-12 h-12" />
                <p className="text-sm">Select a Node from the graph or a Checkpoint from the timeline to inspect its payload.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
