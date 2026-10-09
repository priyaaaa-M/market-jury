import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api, post } from "../lib/api";
import { Btn, Card } from "../components/ui";

export default function Settings() {
  const qc = useQueryClient();
  const cfg = useQuery({ queryKey: ["config"], queryFn: () => api("/config") });
  const save = useMutation({ mutationFn: (p: any) => post("/config", p), onSuccess: () => qc.invalidateQueries({ queryKey: ["config"] }) });
  const reset = useMutation({ mutationFn: () => post("/reset?confirm=true"), onSuccess: () => qc.invalidateQueries() });
  const [confirm, setConfirm] = useState("");
  const c = cfg.data;
  if (!c) return <p>Loading…</p>;
  const num = (k: string, step = 1) => (
    <label className="flex items-center justify-between text-sm">{k}
      <input type="number" step={step} className="w-28 rounded bg-slate-800 p-1" defaultValue={c[k]}
        onBlur={(e) => save.mutate({ [k]: typeof c[k] === "number" && !Number.isInteger(c[k]) ? parseFloat(e.target.value) : Number(e.target.value) })} /></label>);
  const flag = (k: string) => (
    <label className="flex items-center justify-between text-sm">{k}
      <input type="checkbox" checked={c[k]} onChange={(e) => save.mutate({ [k]: e.target.checked })} /></label>);
  return (
    <>
      <Card title="Trading">
        <label className="flex items-center justify-between text-sm">TRADING_MODE
          <select className="rounded bg-slate-800 p-1" value={c.TRADING_MODE} onChange={(e) => save.mutate({ TRADING_MODE: e.target.value })}>
            {["equity_intraday", "equity_delivery", "fno", "all"].map((m) => <option key={m}>{m}</option>)}</select></label>
        {flag("AGENT_FORCE_ACTIVE")}{flag("AGENT_AUTO_EXECUTE")}{num("AGENT_DEBATE_ROUNDS")}{num("AGENT_MIN_CONFIDENCE", 0.05)}
        <p className="text-xs text-slate-500">Auto-execute only places paper orders. Live trading is not implemented.</p>
      </Card>
      <Card title="LLM budgets (USD)">{num("AGENT_DAILY_BUDGET_USD", 0.5)}{num("AGENT_PER_AGENT_BUDGET_USD", 0.5)}{num("AGENT_MASTER_BUDGET_USD", 0.5)}</Card>
      <Card title="Danger zone">
        <p className="text-sm text-slate-400">Type RESET to wipe trades, verdicts and events.</p>
        <div className="mt-2 flex gap-2"><input className="rounded bg-slate-800 p-1 text-sm" value={confirm} onChange={(e) => setConfirm(e.target.value)} />
          <Btn disabled={confirm !== "RESET"} onClick={() => reset.mutate()}>Hard reset</Btn></div>
      </Card>
    </>
  );
}
