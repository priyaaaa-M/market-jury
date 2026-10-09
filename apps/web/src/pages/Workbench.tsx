import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, post } from "../lib/api";
import { Card, inr } from "../components/ui";

export default function Workbench() {
  const qc = useQueryClient();
  const [values, setValues] = useState({capital:100000, risk_pct:1, entry:1000, stop:980, target:1040});
  const [side, setSide] = useState("long");
  const [note, setNote] = useState({symbol:"TCS", thesis:"", invalidation:"", review:""});
  const plan = useMutation({mutationFn: () => post("/risk-plan", {...values, side})});
  const journal = useQuery({queryKey:["journal"], queryFn: () => api("/journal")});
  const save = useMutation({mutationFn: () => post("/journal", note), onSuccess: () => {qc.invalidateQueries({queryKey:["journal"]}); setNote({...note, thesis:"", invalidation:"", review:""});}});
  const remove = useMutation({mutationFn: (id:string) => api(`/journal/${id}`, {method:"DELETE"}), onSuccess: () => qc.invalidateQueries({queryKey:["journal"]})});
  function exportJournal() {
    const url = URL.createObjectURL(new Blob([JSON.stringify(journal.data?.entries ?? [],null,2)],{type:"application/json"}));
    const a=document.createElement("a"); a.href=url; a.download="market-jury-journal.json"; a.click(); URL.revokeObjectURL(url);
  }
  return <>
    <Card title="Before you trade: equity risk planner">
      <p className="mb-4 text-sm text-neutral-700">Plan the risk before the entry. This is a calculation, not a recommendation or stop-loss order. No derivatives or leverage.</p>
      <form onSubmit={e=>{e.preventDefault();plan.mutate();}} className="grid gap-4 sm:grid-cols-3">
        {Object.entries(values).map(([k,v])=><label key={k} className="text-sm">{({capital:"Capital (₹)",risk_pct:"Risk per trade (%)",entry:"Entry (₹)",stop:"Stop (₹)",target:"Target (₹)"} as Record<string,string>)[k]}<input required type="number" min="0.01" max={k==="risk_pct"?5:undefined} step="0.01" value={v} onChange={e=>setValues({...values,[k]:Number(e.target.value)})} className="mt-1 block w-full rounded bg-neutral-100 p-2" /></label>)}
        <label className="text-sm">Side<select className="mt-1 block w-full rounded bg-neutral-100 p-2" value={side} onChange={e=>setSide(e.target.value)}><option value="long">Long</option><option value="short">Short (planning only)</option></select></label>
        <button className="rounded bg-neutral-200 px-4 py-2" disabled={plan.isPending}>Calculate risk</button>
      </form>
      {plan.isError && <p role="alert" className="mt-3 text-neutral-900">{String(plan.error)}</p>}
      {plan.data && <div role="status" className="mt-4 rounded border border-neutral-400 p-4"><p>Quantity: {plan.data.quantity} shares · Planned loss: {inr(plan.data.planned_loss)} · Reward/risk: {plan.data.reward_risk}:1</p><p className="mt-2 text-sm text-neutral-700">Regime size multiplier: {plan.data.size_multiplier}. {plan.data.note}</p></div>}
    </Card>
    <Card title="Research journal (private)">
      <p className="mb-3 text-sm text-neutral-700">Write the thesis, what would invalidate it, and the later review. Stored in your engine, never in the public scoreboard.</p>
      <form className="grid gap-3" onSubmit={e=>{e.preventDefault();save.mutate();}}>
        {Object.entries(note).map(([k,v])=><label key={k} className="text-sm capitalize">{k}<textarea required={k!=="review"} maxLength={k==="symbol"?30:1000} className="mt-1 block w-full rounded bg-neutral-100 p-2" rows={k==="symbol"?1:2} value={v} onChange={e=>setNote({...note,[k]:e.target.value})}/></label>)}
        <div className="flex gap-3"><button className="rounded bg-neutral-200 px-4 py-2" disabled={save.isPending}>Save journal entry</button><button type="button" className="rounded border border-neutral-400 px-4 py-2" onClick={exportJournal}>Export JSON</button></div>
      </form>
      {save.isError && <p role="alert">{String(save.error)}</p>}
      {journal.isError && <p role="alert">{String(journal.error)}</p>}
      {(journal.data?.entries ?? []).map((e:any)=><article className="mt-4 border-t border-neutral-300 pt-4" key={e.id}><h3>{e.symbol} · {new Date(e.timestamp).toLocaleString()}</h3><p className="whitespace-pre-wrap text-sm">Thesis: {e.thesis}</p><p className="text-sm">Invalidation: {e.invalidation}</p><p className="text-sm">Review: {e.review || "Not reviewed yet"}</p><button className="mt-2 text-sm underline" onClick={()=>{if(confirm("Delete this journal entry?"))remove.mutate(e.id);}}>Delete entry</button></article>)}
    </Card>
  </>;
}
