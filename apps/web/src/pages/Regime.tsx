import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";
import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { post } from "../lib/api";
import { Card, Stat } from "../components/ui";

export default function Regime() {
  const r = useQuery({ queryKey: ["regime"], queryFn: () => api("/regime") });
  const qc = useQueryClient();
  const [ctx,setCtx] = useState({as_of:new Date().toLocaleDateString("en-CA", {timeZone:"Asia/Kolkata"}), source:"", breadth_pct:"", fii_net_crore:"", dii_net_crore:""});
  const save=useMutation({mutationFn:()=>post("/regime/context",{...ctx,breadth_pct:ctx.breadth_pct===""?null:Number(ctx.breadth_pct),fii_net_crore:ctx.fii_net_crore===""?null:Number(ctx.fii_net_crore),dii_net_crore:ctx.dii_net_crore===""?null:Number(ctx.dii_net_crore)}),onSuccess:()=>qc.invalidateQueries()});
  const d = r.data;
  if (r.isError) return <p role="alert">{String(r.error)}</p>;
  if (!d) return <p>Loading…</p>;
  return (
    <Card title="Current regime">
      <div className="flex flex-wrap gap-6"><Stat label="Regime" value={d.regime} /><Stat label="Trend" value={d.trend} /><Stat label="Volatility" value={d.volatility} />
        <Stat label="Size multiplier" value={d.size_multiplier} /><Stat label="Extra confidence required" value={`+${Math.round(d.confidence_adjust * 100)}%`} /></div>
      <pre className="mt-3 overflow-x-auto text-xs text-slate-300">{JSON.stringify(d.inputs, null, 1)}</pre>
      <p className="mt-2 text-sm text-slate-300">{d.method}</p>
      <p className="mt-2 text-sm">Context: {d.context_status}. Missing: {(d.missing_inputs??[]).join(", ") || "none"}. Stale or absent context is not fabricated.</p>
      <form className="mt-4 grid gap-3 sm:grid-cols-2" onSubmit={e=>{e.preventDefault();save.mutate();}}>
        {Object.entries(ctx).map(([k,v])=><label key={k} className="text-sm">{({as_of:"Observation date (IST)",source:"Source / provenance",breadth_pct:"Breadth: advancing share (%)",fii_net_crore:"FII net (₹ crore)",dii_net_crore:"DII net (₹ crore)"} as Record<string,string>)[k]}<input className="mt-1 block w-full rounded bg-slate-800 p-2" required={k==="as_of"||k==="source"} type={k==="as_of"?"date":k==="source"?"text":"number"} step="any" min={k==="breadth_pct"?0:undefined} max={k==="breadth_pct"?100:undefined} value={v} onChange={e=>setCtx({...ctx,[k]:e.target.value})}/></label>)}
        <button className="rounded bg-emerald-800 px-4 py-2" disabled={save.isPending}>Save manual context</button>
      </form>
      {save.isError && <p role="alert">{String(save.error)}</p>}
      <p className="mt-3 text-xs text-slate-300">Enter observed context only. Breadth = advancing / (advancing + declining) × 100, same universe and date. Flows: net buys minus sells, ₹ crore. No automatic NSE feed is claimed.</p>
    </Card>
  );
}
