import { useState } from "react";
import { NavLink, Route, Routes } from "react-router-dom";
import { getKey, setKey } from "./lib/api";
import { useLive } from "./lib/useLive";
import { useQuery } from "@tanstack/react-query";
import { api } from "./lib/api";
import Overview from "./pages/Overview";
import Portfolio from "./pages/Portfolio";
import Debates from "./pages/Debates";
import Agents from "./pages/Agents";
import Watchlist from "./pages/Watchlist";
import Timeline from "./pages/Timeline";
import Settings from "./pages/Settings";
import Scoreboard from "./pages/Scoreboard";
import Regime from "./pages/Regime";

const NAV = [["/", "Overview"], ["/portfolio", "Portfolio"], ["/debates", "Debates"], ["/agents", "Agents"],
  ["/watchlist", "Watchlist"], ["/timeline", "Timeline"], ["/scoreboard", "Scoreboard"], ["/regime", "Regime"], ["/settings", "Settings"]];

function KeyGate({ onSet }: { onSet: () => void }) {
  const [v, setV] = useState("");
  return (
    <div className="mx-auto mt-24 max-w-sm space-y-3 p-4">
      <h1 className="text-xl font-semibold">Enter engine API key</h1>
      <p className="text-sm text-slate-400">Printed in the engine log at startup, or set via API_KEY.</p>
      <input className="w-full rounded bg-slate-800 p-2" value={v} onChange={(e) => setV(e.target.value)} type="password" />
      <button className="rounded bg-emerald-700 px-4 py-2" onClick={() => { setKey(v); onSet(); }}>Connect</button>
    </div>
  );
}

export default function App() {
  const [, force] = useState(0);
  if (!getKey()) return <KeyGate onSet={() => force((n) => n + 1)} />;
  return <Shell />;
}

function Shell() {
  const { connected } = useLive();
  const status = useQuery({ queryKey: ["status"], queryFn: () => api("/status") });
  return (
    <div className="min-h-screen">
      <header className="flex flex-wrap items-center gap-4 border-b border-slate-800 px-4 py-2">
        <b>market-jury</b>
        <nav className="flex flex-wrap gap-3 text-sm">
          {NAV.map(([to, l]) => (
            <NavLink key={to} to={to} end className={({ isActive }) => (isActive ? "text-emerald-400" : "text-slate-400 hover:text-slate-200")}>{l}</NavLink>
          ))}
        </nav>
        <div className="ml-auto flex items-center gap-3 text-xs text-slate-400">
          <span>phase: {status.data?.phase ?? "…"}</span>
          <span className="rounded bg-amber-900 px-2 py-0.5 text-amber-200">PAPER ONLY</span>
          <span className={connected ? "text-emerald-400" : "text-rose-400"}>{connected ? "live" : "offline"}</span>
        </div>
      </header>
      <main className="mx-auto max-w-6xl space-y-4 p-4">
        <Routes>
          <Route path="/" element={<Overview />} /><Route path="/portfolio" element={<Portfolio />} />
          <Route path="/debates" element={<Debates />} /><Route path="/agents" element={<Agents />} />
          <Route path="/watchlist" element={<Watchlist />} /><Route path="/timeline" element={<Timeline />} />
          <Route path="/scoreboard" element={<Scoreboard />} /><Route path="/regime" element={<Regime />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
        <p className="pt-6 text-xs text-slate-500">Not investment advice. Paper trading only. Past verdicts do not predict future results.</p>
      </main>
    </div>
  );
}
