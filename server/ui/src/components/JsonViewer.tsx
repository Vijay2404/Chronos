"use client";

// A simple JSON viewer with syntax highlighting
export function JsonViewer({ data }: { data: any }) {
  if (data === null || data === undefined) {
    return <span className="text-[var(--color-text-muted)] italic text-xs">null</span>;
  }

  const jsonStr = typeof data === "string" ? data : JSON.stringify(data, null, 2);

  // Truncate very large payloads for performance
  const maxLen = 50000;
  const truncated = jsonStr.length > maxLen;
  const displayStr = truncated ? jsonStr.substring(0, maxLen) + "\n\n... (truncated)" : jsonStr;

  const highlighted = displayStr
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/("(?:[^"\\]|\\.)*")(\s*:)/g, '<span class="text-blue-400">$1</span>$2') // Keys
    .replace(/:\s*("(?:[^"\\]|\\.)*")/g, ': <span class="text-green-400">$1</span>') // String values
    .replace(/:\s*(-?\d+\.?\d*(?:[eE][+-]?\d+)?)\b/g, ': <span class="text-orange-400">$1</span>') // Numbers
    .replace(/:\s*(true|false|null)\b/g, ': <span class="text-purple-400">$1</span>'); // Booleans/null

  return (
    <div className="relative group">
      <button
        onClick={() => navigator.clipboard.writeText(jsonStr)}
        className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity bg-[var(--color-surface)] px-2 py-1 rounded text-[10px] text-[var(--color-text-muted)] hover:text-white border border-[var(--color-border)]"
      >
        Copy
      </button>
      <pre
        className="text-xs font-mono p-4 rounded-lg bg-[#0a0a0f] border border-[var(--color-border)] shadow-inner overflow-auto max-h-96 whitespace-pre-wrap leading-relaxed"
        dangerouslySetInnerHTML={{ __html: highlighted }}
      />
    </div>
  );
}
