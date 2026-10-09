import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api, post, clearKey, validateKey, setKey } from "../lib/api";
import { Btn, Card } from "../components/ui";

export default function Settings() {
  const qc = useQueryClient();
  const cfg = useQuery({ queryKey: ["config"], queryFn: () => api("/config") });
  const save = useMutation({ mutationFn: (p: any) => post("/config", p), onSuccess: () => qc.invalidateQueries({ queryKey: ["config"] }) });
  const reset = useMutation({ mutationFn: () => post("/reset?confirm=true"), onSuccess: () => qc.invalidateQueries() });
  const [confirm, setConfirm] = useState("");
  const c = cfg.data;
  const [key, updateKey] = useState("");
  const [connection, setConnection] = useState("");
  const [checking, setChecking] = useState(false);
  const [name, setName] = useState(localStorage.getItem("display_name") || "");
  const [theme, setTheme] = useState(localStorage.getItem("theme") || "light");
  const connect = async () => {
    setChecking(true); setConnection("");
    try { await validateKey(key); setKey(key); location.reload(); }
    catch (e) { setConnection(e instanceof Error ? e.message : "Connection failed"); }
    finally { setChecking(false); }
  };
  const num = (k: string, step = 1) => (
    <label className="flex flex-wrap items-center justify-between gap-2 text-sm break-all">{k}
      <input type="number" step={step} className="w-28 shrink-0 rounded bg-neutral-100 p-1" defaultValue={c[k]}
        onBlur={(e) => save.mutate({ [k]: typeof c[k] === "number" && !Number.isInteger(c[k]) ? parseFloat(e.target.value) : Number(e.target.value) })} /></label>);
  const flag = (k: string) => (
    <label className="flex flex-wrap items-center justify-between gap-2 text-sm break-all">{k}
      <input type="checkbox" checked={c[k]} onChange={(e) => save.mutate({ [k]: e.target.checked })} /></label>);
  return (
    <>
      <Card title="Connection">
        <p className="mb-2 text-sm">Change the key saved in this browser, not the server's secret. Copy API_KEY from the Render service Environment tab. Never use the rnd_ management key or LLM_API_KEY here.</p>
        <label className="block text-sm" htmlFor="replacement-key">New engine API key</label>
        <input id="replacement-key" type="password" autoComplete="off" className="w-full rounded bg-neutral-100 p-2" value={key} onChange={e=>updateKey(e.target.value)} />
        <div className="my-2 flex flex-wrap gap-2"><Btn disabled={checking || !key.trim()} onClick={connect}>{checking ? "Checking…" : "Validate and save key"}</Btn>
        <Btn onClick={()=>{clearKey(); location.reload();}}>Sign out / change key</Btn>
        <Btn onClick={async()=>{setConnection("Checking engine…"); try { await api("/status"); setConnection("Connected. Your saved key is valid."); qc.invalidateQueries(); } catch(e) {setConnection(String(e));}}}>Check connection</Btn></div>
        {connection && <p role="status" className="text-sm">{connection}</p>}
      </Card>
      <Card title="Personal preferences">
        <label htmlFor="display-name" className="block text-sm">Display name (this browser only)</label>
        <input id="display-name" maxLength={60} className="w-full rounded bg-neutral-100 p-2" value={name} onChange={e=>{setName(e.target.value);localStorage.setItem("display_name",e.target.value);}} />
        <p className="my-2 text-xs text-neutral-600">This is a local label, not a user account. It does not separate portfolios or journals.</p>
        <label htmlFor="theme" className="block text-sm">Theme</label>
        <select id="theme" className="rounded bg-neutral-100 p-2" value={theme} onChange={e=>{setTheme(e.target.value);localStorage.setItem("theme",e.target.value);document.documentElement.dataset.theme=e.target.value;}}><option value="light">Light</option><option value="dark">Dark</option></select>
      </Card>
      {cfg.isError && <p role="alert">{String(cfg.error)}. Use the connection controls above to recover.</p>}
      {!c && !cfg.isError && <p>Loading engine settings…</p>}
      {c && <>
      <Card title="Trading">
        <label className="flex flex-wrap items-center justify-between gap-2 text-sm break-all">TRADING_MODE
          <select className="rounded bg-neutral-100 p-1" value={c.TRADING_MODE} onChange={(e) => save.mutate({ TRADING_MODE: e.target.value })}>
            {["equity_intraday", "equity_delivery", "fno", "all"].map((m) => <option key={m}>{m}</option>)}</select></label>
        {flag("AGENT_FORCE_ACTIVE")}{flag("AGENT_AUTO_EXECUTE")}{num("AGENT_DEBATE_ROUNDS")}{num("AGENT_MIN_CONFIDENCE", 0.05)}
        <p className="text-xs text-neutral-600">Auto-execute only places paper orders. Live trading is not implemented.</p>
      </Card>
      <Card title="LLM budgets (USD)">{num("AGENT_DAILY_BUDGET_USD", 0.5)}{num("AGENT_PER_AGENT_BUDGET_USD", 0.5)}{num("AGENT_MASTER_BUDGET_USD", 0.5)}</Card>
      <Card title="Danger zone">
        <p className="text-sm text-neutral-600">Type RESET to wipe trades, verdicts and events.</p>
        <div className="mt-2 flex gap-2"><input className="rounded bg-neutral-100 p-1 text-sm" value={confirm} onChange={(e) => setConfirm(e.target.value)} />
          <Btn disabled={confirm !== "RESET"} onClick={() => reset.mutate()}>Hard reset</Btn></div>
      </Card>
      </>}
    </>
  );
}
