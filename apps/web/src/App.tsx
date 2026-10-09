import { useState } from "react";
import { NavLink, Route, Routes } from "react-router-dom";
import { getKey, setKey, clearKey, validateKey } from "./lib/api";
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
import Workbench from "./pages/Workbench";

const NAV = [["/", "Overview"], ["/portfolio", "Portfolio"], ["/debates", "Debates"], ["/agents", "Agents"],
  ["/watchlist", "Watchlist"], ["/timeline", "Timeline"], ["/scoreboard", "Scoreboard"], ["/regime", "Regime"], ["/workbench", "Workbench"], ["/settings", "Settings"]];

function KeyGate({ onSet }: { onSet: () => void }) {
  const [v, setV] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const connect = async () => {
    setError(""); setBusy(true);
    try { await validateKey(v); setKey(v); onSet(); }
    catch (e) { setError(e instanceof Error ? e.message : "Could not connect to engine"); }
    finally { setBusy(false); }
  };
  return (
    <div className="mx-auto mt-24 max-w-sm space-y-3 p-4">
      <h1 className="text-xl font-semibold">Enter engine API key</h1>
      <p className="text-sm text-neutral-600">Render: market-jury service → Environment → copy API_KEY. This is not your Render management key or LLM key. The first connection may take a minute on the free plan.</p>
      <label htmlFor="api-key" className="block text-sm">Engine API key</label>
      <input id="api-key" className="w-full rounded bg-neutral-100 p-2" value={v} onChange={(e) => setV(e.target.value)} type="password" />
      <button disabled={busy || !v.trim()} className="rounded bg-neutral-200 px-4 py-2 disabled:opacity-40" onClick={connect}>{busy ? "Checking connection…" : "Connect"}</button>
      {error && <p role="alert" className="text-sm">{error}</p>}
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
  if (status.isError && String(status.error).includes("Invalid API key")) return <KeyGate onSet={() => location.reload()} />;
  return (
    <div className="min-h-screen">
      <a className="skip-link" href="#main">Skip to content</a>
      <header className="flex flex-wrap items-center gap-4 border-b border-neutral-200 px-4 py-2">
        <b>market-jury</b>{localStorage.getItem("display_name") && <span className="text-sm">{localStorage.getItem("display_name")}</span>}
        <nav aria-label="Main navigation" className="flex flex-wrap gap-3 text-sm">
          {NAV.map(([to, l]) => (
            <NavLink key={to} to={to} end className={({ isActive }) => (isActive ? "text-black underline underline-offset-4 font-semibold" : "text-neutral-700 hover:text-black")}>{l}</NavLink>
          ))}
        </nav>
        <div className="ml-auto flex items-center gap-3 text-xs text-neutral-600">
          <span>phase: {status.data?.phase ?? "…"}</span>
          <span className="rounded border border-white bg-black px-2 py-0.5 text-white">PAPER ONLY</span>
          <span className={connected ? "text-neutral-900" : "text-neutral-900"}>{connected ? "engine connected" : "engine disconnected"}</span>
        </div>
      </header>
      <div role="status" className="border-b border-neutral-400 bg-neutral-200 px-4 py-3 text-sm text-neutral-900">
        {status.data?.data_source === "simulated" ? "DEMO DATA: synthetic prices. AI text may be generated or placeholder; not real market calls." : `Data: ${status.data?.data_source ?? "checking connection"}. Research only, not execution prices.`}
      </div>
      {status.isError && <div role="alert" className="p-4 text-neutral-900">{String(status.error)}. Check the engine and API key. <button onClick={() => {clearKey(); location.reload();}}>Change key</button></div>}
      <main id="main" tabIndex={-1} className="mx-auto max-w-6xl space-y-4 p-4">
        <Routes>
          <Route path="/" element={<Overview />} /><Route path="/portfolio" element={<Portfolio />} />
          <Route path="/debates" element={<Debates />} /><Route path="/agents" element={<Agents />} />
          <Route path="/watchlist" element={<Watchlist />} /><Route path="/timeline" element={<Timeline />} />
          <Route path="/scoreboard" element={<Scoreboard />} /><Route path="/regime" element={<Regime />} />
          <Route path="/workbench" element={<Workbench />} /><Route path="/settings" element={<Settings />} />
        </Routes>
        <p className="pt-6 text-xs text-neutral-600">Not investment advice. Paper trading only. Past verdicts do not predict future results.</p>
      </main>
    </div>
  );
}
