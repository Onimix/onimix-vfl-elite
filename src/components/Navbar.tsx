import Link from "next/link";

export function Navbar() {
  return (
    <nav className="border-b border-neutral-800 bg-neutral-950/80 backdrop-blur-sm sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2">
          <span className="text-lg font-black text-white tracking-tight">ONIMIX</span>
          <span className="text-xs text-emerald-400 font-mono bg-emerald-950/40 border border-emerald-800/30 px-1.5 py-0.5 rounded">ELITE</span>
        </Link>
        <div className="flex items-center gap-1">
          <Link
            href="/"
            className="px-3 py-1.5 text-sm text-neutral-400 hover:text-white hover:bg-neutral-800 rounded-lg transition-colors"
          >
            Home
          </Link>
          <Link
            href="/analyze"
            className="px-3 py-1.5 text-sm text-neutral-400 hover:text-white hover:bg-neutral-800 rounded-lg transition-colors"
          >
            Analyze
          </Link>
          <Link
            href="/elite"
            className="px-3 py-1.5 text-sm text-emerald-400 hover:text-emerald-300 hover:bg-emerald-950/30 rounded-lg transition-colors font-semibold"
          >
            🎯 ELITE
          </Link>
          <Link
            href="/tracker"
            className="px-3 py-1.5 text-sm text-neutral-400 hover:text-white hover:bg-neutral-800 rounded-lg transition-colors"
          >
            Tracker
          </Link>
        </div>
      </div>
    </nav>
  );
}
