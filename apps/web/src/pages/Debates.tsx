import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api, post } from "../lib/api";
import { Btn, Card, Verdict } from "../components/ui";
const ROLES = [
  {id:"debater_bull",label:"The optimist",role:"Bull case",icon:"B+",description:"What supports the upside?"},
  {id:"debater_bear",label:"The challenger",role:"Bear case",icon:"B−",description:"What breaks the thesis?"},
  {id:"risk_reviewer",label:"The guardian",role:"Risk review",icon:"R",description:"What's missing? What can go wrong?"},
  {id:"final_judge",label:"The judge",role:"Final decision",icon:"J",description:"Weigh the discussion. Decide or hold."},
];
export default function Debates() {
  const qc = useQueryClient();
  const wl = useQuery({ queryKey: ["watchlist"], queryFn: () => api("/watchlist") });
  const progress = useQuery({queryKey:["debate-progress"],queryFn:()=>api("/debate-progress"),refetchInterval:10000});
  const [sym, setSym] = useState("");
  const [message,setMessage] = useState("");
  const symbol = sym || wl.data?.symbols?.[0];
  const v = useQuery({ queryKey: ["consensus", symbol], queryFn: () => api(`/consensus/${symbol}`), enabled: !!symbol, retry: false });
  const run = useMutation({mutationFn:()=>post("/task",{type:"debate",symbols:[symbol]}),onSuccess:()=>{setMessage("Discussion requested. Each role may take a few minutes on free models.");qc.invalidateQueries({queryKey:["debate-progress"]});},onError:(e)=>setMessage(String(e))});
  const current=progress.data?.symbols?.[symbol];
  return <>
    <Card title="A discussion, not a crystal ball" right={<span className="discussion-label">04 ROLES / PAPER ONLY</span>}>
      <h2 className="text-2xl font-bold tracking-tight">Let the evidence face the jury.</h2>
      <p className="mt-2 text-sm text-neutral-600">Three perspectives. One final judge. Public delayed market data only. Model agreement is not proof of accuracy; confidence is not a calibrated probability.</p>
    </Card>
    <div className="team-grid">{ROLES.map(r=><div key={r.id} className="team-tile"><span className="model-monogram" aria-hidden="true">{r.icon}</span><b>{r.label}</b><small>{r.role} · {progress.data?.roles?.[r.id]?.state || "idle"}</small><small className="mt-2 break-all">{progress.data?.roles?.[r.id]?.model || "Loading model…"}</small><p className="mt-3 text-xs">{r.description}</p></div>)}</div>
    <Card title="Session desk"><div className="flex flex-wrap items-center gap-2">{(wl.data?.symbols ?? []).map((s:string)=><Btn key={s} onClick={()=>setSym(s)} aria-pressed={s===symbol}>{s}</Btn>)}<Btn disabled={!symbol || run.isPending || ["running","retrying"].includes(current?.state)} onClick={()=>run.mutate()}>Start discussion</Btn></div>
      {message && <p role="status" className="mt-3 text-sm">{message}</p>}
      {current && <p role="status" className="mt-3 text-sm">{current.state === "failed" ? current.message : `${current.state.toUpperCase()} · ${current.role?.replaceAll("_"," ")} ${current.attempt ? `· attempt ${current.attempt}/2` : ""}`}</p>}
      <p className="mt-2 text-xs text-neutral-600">Free-only. One bounded retry per role, then stop with no new verdict. No paid fallback. Market-hours gate applies; out-of-hours research can be enabled in Settings.</p>
    </Card>
    {(progress.data?.messages?.[symbol] || []).length > 0 && <Card title="Current session · completed turns"><div className="space-y-4">{progress.data.messages[symbol].map((m:any,i:number)=><article key={i} className="border-b border-neutral-200 pb-4"><b>{ROLES.find(r=>r.id===m.agent_name)?.role||m.agent_name}</b><p className="mt-1 break-all text-xs text-neutral-600">{m.receipt?.actual_model||m.model} · {m.receipt?.cost_usd===0?"$0 receipt verified":"cost unverified"}</p><p className="mt-2 text-sm leading-relaxed">{m.argument}</p></article>)}</div></Card>}
    {v.isError && <p className="text-sm text-neutral-600">No completed discussion for {symbol} yet. A failed session never fabricates a verdict.</p>}
    {v.data && <>
      <Card title={`${v.data.symbol} · Latest completed verdict`}><div className="flex flex-wrap items-center gap-4"><Verdict v={v.data.verdict}/><span>{Math.round(v.data.confidence*100)}% model confidence</span><span className="text-neutral-600">regime {v.data.regime}</span></div><p className="mt-2 text-xs text-neutral-600">{v.data.timestamp} · {v.data.audit?.data_source} · {v.data.audit?.team}</p><p className="mt-3 text-sm">{v.data.reasoning}</p></Card>
      <div className="grid gap-4 md:grid-cols-2">{v.data.positions.map((p:any,i:number)=>{const role=ROLES.find(r=>r.id===p.agent_name);return <Card key={i} title={`${role?.role || p.stance} · round ${p.round+1}`} right={<span className="model-monogram" aria-hidden="true">{role?.icon||"AI"}</span>}>
        <p className="mb-2 break-all text-xs text-neutral-600">{p.receipt?.actual_model||p.model||"Historical model not recorded"}</p>
        {p.receipt?.actual_model && <p className="mb-3 break-all text-xs text-neutral-600">Requested: {p.model} · {p.receipt.cost_usd===0?"$0 provider receipt verified":"cost unverified"}</p>}
        <p className="text-sm leading-relaxed">{p.argument}</p><div className="mt-3 flex flex-wrap gap-1">{(Array.isArray(p.evidence)?p.evidence:[]).map((e:string,j:number)=><span key={j} className="rounded bg-neutral-100 px-2 py-1 text-xs">{e}</span>)}</div>
      </Card>})}</div>
      <p className="text-xs text-neutral-600">Initials are role icons, not official model logos. Free Router can select the same underlying model for different roles. Older sessions may use the earlier two-role design.</p>
    </>}
  </>;
}
