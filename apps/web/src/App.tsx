import * as Dialog from "@radix-ui/react-dialog";
import { motion, MotionConfig } from "motion/react";
import { useState } from "react";
import { NavLink, Route, Routes, useLocation } from "react-router-dom";
import { getKey, setKey, clearKey, validateKey } from "./lib/api";
import { useLive } from "./lib/useLive";
import { useQuery } from "@tanstack/react-query";
import { api } from "./lib/api";
import JuryChat from "./pages/JuryChat";
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

const GROUPS = [
  {title:"Market desk", items:[["/","Overview","◈"],["/watchlist","Watchlist","⊙"],["/regime","Market regime","∿"]]},
  {title:"The jury", items:[["/chat","Ask the jury","↳"],["/debates","Discussion room","◉"],["/agents","Agent studio","◇"],["/timeline","Session timeline","≡"]]},
  {title:"Accountability", items:[["/scoreboard","Scoreboard","▥"],["/portfolio","Paper portfolio","▧"],["/workbench","Risk & journal","⊞"]]},
  {title:"Your space", items:[["/settings","Profile & settings","⚙"]]},
];

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
  const [menu, setMenu] = useState(false);
  const [collapsed,setCollapsed]=useState(()=>localStorage.getItem("sidebar_collapsed")==="true");
  const toggleSidebar=()=>setCollapsed(v=>{localStorage.setItem("sidebar_collapsed",String(!v));return !v;});
  const location = useLocation();
  const title = GROUPS.flatMap(g=>g.items).find(i=>i[0]===location.pathname)?.[1] || "Market desk";
  const name = localStorage.getItem("display_name") || "Your workspace";
  const status = useQuery({ queryKey: ["status"], queryFn: () => api("/status") });
  if (status.isError && String(status.error).includes("Invalid API key")) return <KeyGate onSet={() => window.location.reload()} />;
  return (
    <MotionConfig reducedMotion="user"><div className={`app-layout min-h-screen ${collapsed?"sidebar-collapsed":""}`}>
      <a className="skip-link" href="#main">Skip to content</a>
      <aside aria-label="Workspace sidebar" className={`sidebar ${menu ? "sidebar-open" : ""}`}>
        <button className="sidebar-toggle" aria-label={collapsed?"Expand sidebar":"Collapse sidebar"} aria-expanded={!collapsed} onClick={toggleSidebar}>{collapsed?"→":"←"}</button>
        <div className="brand-mark"><span className="brand-icon">MJ</span><div><b>market-jury</b><small>THE RESEARCH DESK</small></div><button className="sidebar-close" aria-label="Close navigation" onClick={()=>setMenu(false)}>×</button></div>
        <nav aria-label="Main navigation">{GROUPS.map(g=><section className="nav-group" key={g.title}><h2>{g.title}</h2>{g.items.map(([to,label,icon])=><NavLink to={to} end key={to} title={label} aria-label={label} onClick={()=>setMenu(false)} className={({isActive})=>`nav-item ${isActive?"nav-active":""}`}><span aria-hidden="true">{icon}</span><span>{label}</span><span className="nav-arrow" aria-hidden="true">↗</span></NavLink>)}</section>)}</nav>
        <NavLink to="/settings" className="profile-tile" onClick={()=>setMenu(false)}><span className="avatar">{name.slice(0,2).toUpperCase()}</span><div><b>{name}</b><small>LOCAL PROFILE · PAPER ONLY</small></div></NavLink>
      </aside>
      <Dialog.Root open={menu} onOpenChange={setMenu}><Dialog.Portal><Dialog.Overlay className="nav-backdrop"/><Dialog.Content className="mobile-nav-dialog"><Dialog.Title className="text-xl font-bold">market-jury</Dialog.Title><Dialog.Description className="text-xs text-neutral-600">Research workspace navigation</Dialog.Description><Dialog.Close className="dialog-close" aria-label="Close navigation">×</Dialog.Close><nav aria-label="Mobile navigation">{GROUPS.map(g=><section className="nav-group" key={g.title}><h2>{g.title}</h2>{g.items.map(([to,label,icon])=><NavLink key={to} to={to} end onClick={()=>setMenu(false)} className={({isActive})=>`mobile-nav-item ${isActive?"mobile-nav-active":""}`}><span aria-hidden="true">{icon}</span> {label}</NavLink>)}</section>)}</nav></Dialog.Content></Dialog.Portal></Dialog.Root>
      <div className="workspace">
      <header className="desk-header"><button className="menu-button" aria-label="Open navigation" onClick={()=>setMenu(true)} aria-expanded={menu}>☰</button><div><small>WORKSPACE / {GROUPS.find(g=>g.items.some(i=>i[0]===location.pathname))?.title.toUpperCase()}</small><h1>{title}</h1></div><div className="connection-pill"><span className={connected?"status-dot live-dot":"status-dot"}/><span>{connected ? "engine connected" : "engine disconnected"}</span><b>PAPER ONLY</b></div></header>
      <div role="status" className="border-b border-neutral-400 bg-neutral-200 px-4 py-3 text-sm text-neutral-900">
        {status.data?.data_source === "simulated" ? "DEMO DATA: synthetic prices. AI text may be generated or placeholder; not real market calls." : `Data: ${status.data?.data_source ?? "checking connection"}. Research only, not execution prices.`}
      </div>
      {status.isError && <div role="alert" className="p-4 text-neutral-900">{String(status.error)}. Check the engine and API key. <button onClick={() => {clearKey(); window.location.reload();}}>Change key</button></div>}
      <motion.main initial={{opacity:0,y:6}} animate={{opacity:1,y:0}} transition={{duration:.25}} key={location.pathname} id="main" tabIndex={-1} className="desk-main mx-auto max-w-6xl space-y-4 p-4">
        <Routes>
          <Route path="/" element={<Overview />} /><Route path="/portfolio" element={<Portfolio />} />
          <Route path="/chat" element={<JuryChat />} /><Route path="/debates" element={<Debates />} /><Route path="/agents" element={<Agents />} />
          <Route path="/watchlist" element={<Watchlist />} /><Route path="/timeline" element={<Timeline />} />
          <Route path="/scoreboard" element={<Scoreboard />} /><Route path="/regime" element={<Regime />} />
          <Route path="/workbench" element={<Workbench />} /><Route path="/settings" element={<Settings />} />
        </Routes>
        <p className="pt-6 text-xs text-neutral-600">Not investment advice. Paper trading only. Past verdicts do not predict future results.</p>
      </motion.main>
      </div>
    </div></MotionConfig>
  );
}
