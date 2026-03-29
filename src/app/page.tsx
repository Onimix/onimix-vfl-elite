import Link from "next/link";
import { Navbar } from "@/components/Navbar";

const rules = [
  { code: "A1", name: "Home Zero Trap", desc: "Skip if home team scored 0 at home yesterday same slot" },
  { code: "A2", name: "Away Zero Trap", desc: "Skip if away team scored 0 away yesterday same slot" },
  { code: "A3", name: "Position Switch Zero", desc: "Zero energy transfers even when positions switch" },
  { code: "A4", name: "Cooldown / Repair", desc: "Skip teams that scored 3+ (cooldown) or conceded 4+ (repair)" },
  { code: "A5", name: "New Opponent Override", desc: "Strong opponent can override a trap — must pass 4 conditions" },
  { code: "A6", name: "Same Pair Repeat", desc: "Same fixture yesterday with ≤1 total goals = skip" },
  { code: "A7", name: "Both Teams Home Yesterday", desc: "Both played home yesterday — both must have scored" },
  { code: "A8", name: "Both Teams Away Yesterday", desc: "Both played away yesterday — both must have scored" },
  { code: "B1", name: "Over 0.5 Minimum", desc: "JSON Over 0.5 must be above 93% for full points" },
  { code: "B2", name: "Over 1.5 Threshold", desc: "JSON Over 1.5 must be above 70%" },
  { code: "B3", name: "farNearOdds Spotlight", desc: "Most reliable JSON signal — farNearOdds:1 on Over line" },
  { code: "B4", name: "Both Teams Scoring", desc: "Home & Away Over 0.5 both above 65%" },
  { code: "B5", name: "First Half Signal", desc: "H1 Over 0.5 above 60% for confidence" },
  { code: "B6", name: "GG/NG Check", desc: "GG Yes above 40% for both teams scoring" },
  { code: "B7", name: "Correct Score Safety", desc: "0:0 probability below 8%, combined 1:0+0:1 below 15%" },
];

export default function Home() {
  return (
    <div className="min-h-screen bg-neutral-950 text-white">
      <Navbar />

      {/* Hero */}
      <section className="max-w-6xl mx-auto px-4 pt-16 pb-12 text-center">
        <div className="inline-flex items-center gap-2 bg-blue-950/40 border border-blue-800/40 rounded-full px-4 py-1.5 text-xs text-blue-400 mb-6">
          <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
          ONIMIX Refined Filter System
        </div>
        <h1 className="text-4xl sm:text-5xl font-black tracking-tight mb-4">
          Virtual Football<br />
          <span className="text-blue-400">Analysis Engine</span>
        </h1>
        <p className="text-neutral-400 text-lg max-w-xl mx-auto mb-8">
          Apply the ONIMIX dual-signal framework. Yesterday&apos;s results carry 60% weight.
          Pre-match JSON carries 40%. Both must agree before a pick is locked.
        </p>
        <div className="flex gap-3 justify-center flex-wrap">
          <Link
            href="/analyze"
            className="px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-xl transition-colors text-sm"
          >
            Analyze a Slot →
          </Link>
          <Link
            href="/tracker"
            className="px-6 py-3 bg-neutral-800 hover:bg-neutral-700 text-neutral-200 font-bold rounded-xl transition-colors text-sm border border-neutral-700"
          >
            View Tracker
          </Link>
        </div>
      </section>

      {/* Decision table */}
      <section className="max-w-6xl mx-auto px-4 pb-12">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-8">
          {[
            { label: "LOCK", desc: "Yesterday 15+ & JSON 10+", color: "border-emerald-700 bg-emerald-950/20 text-emerald-300" },
            { label: "PICK", desc: "Yesterday 12+ & JSON 8+", color: "border-blue-700 bg-blue-950/20 text-blue-300" },
            { label: "CONSIDER", desc: "Yesterday 12+ & JSON 7", color: "border-yellow-700 bg-yellow-950/20 text-yellow-300" },
            { label: "SKIP", desc: "Any instant trigger or low score", color: "border-red-800 bg-red-950/20 text-red-300" },
          ].map((d) => (
            <div key={d.label} className={`border rounded-xl p-4 ${d.color}`}>
              <div className="font-black text-lg mb-1">{d.label}</div>
              <div className="text-xs opacity-70">{d.desc}</div>
            </div>
          ))}
        </div>

        {/* Scoring weights */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-10">
          <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5">
            <div className="text-sm font-bold text-neutral-400 uppercase tracking-wider mb-3">Yesterday Results — 60%</div>
            <div className="flex items-end gap-2 mb-1">
              <span className="text-3xl font-black text-white">18</span>
              <span className="text-neutral-500 text-sm mb-1">max points</span>
            </div>
            <div className="text-xs text-neutral-500">Minimum 12 pts to proceed. Below 12 = instant skip regardless of JSON.</div>
          </div>
          <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5">
            <div className="text-sm font-bold text-neutral-400 uppercase tracking-wider mb-3">Pre-match JSON — 40%</div>
            <div className="flex items-end gap-2 mb-1">
              <span className="text-3xl font-black text-white">12</span>
              <span className="text-neutral-500 text-sm mb-1">max points</span>
            </div>
            <div className="text-xs text-neutral-500">Minimum 8 pts to proceed. JSON is optional — analysis runs without it.</div>
          </div>
        </div>

        {/* Rules grid */}
        <h2 className="text-xl font-bold text-white mb-4">All 15 Rules</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {rules.map((rule) => (
            <div key={rule.code} className="bg-neutral-900 border border-neutral-800 rounded-lg p-4 flex gap-3">
              <span className="text-xs font-mono bg-neutral-800 text-neutral-400 px-2 py-0.5 rounded h-fit shrink-0">
                {rule.code}
              </span>
              <div>
                <div className="text-sm font-semibold text-white mb-0.5">{rule.name}</div>
                <div className="text-xs text-neutral-500">{rule.desc}</div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-neutral-800 py-6 text-center text-xs text-neutral-600">
        ONIMIX Virtual Football Analysis Engine · Built for pattern tracking & validation
      </footer>
    </div>
  );
}
