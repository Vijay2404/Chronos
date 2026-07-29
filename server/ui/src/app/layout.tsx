import type { Metadata } from "next";
import "./globals.css";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Chronos DevTools",
  description: "Chronos Agent Visualization",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="flex h-screen bg-[var(--color-background)] text-[var(--color-text)]">
        {/* Sidebar */}
        <div className="w-64 border-r border-[var(--color-border)] flex flex-col bg-[var(--color-surface)]">
          <div className="p-4 border-b border-[var(--color-border)] flex items-center justify-center">
            <h1 className="text-xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
              Chronos
            </h1>
          </div>
          <nav className="flex-1 p-4 flex flex-col gap-2">
            <Link 
              href="/" 
              className="p-2 rounded hover:bg-[var(--color-surface-hover)] transition-colors text-sm font-medium"
            >
              Traces
            </Link>
          </nav>
        </div>
        
        {/* Main Content */}
        <main className="flex-1 flex flex-col overflow-hidden">
          {children}
        </main>
      </body>
    </html>
  );
}
