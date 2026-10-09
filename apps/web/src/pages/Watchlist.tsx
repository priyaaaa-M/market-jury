import { PageIntro, Metric, EmptyState } from "../components/PageIntro";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api, post } from "../lib/api";
import { Btn, Card } from "../components/ui";

const ACTIONS = ["screen", "research", "debate", "analyze"];

export default function Watchlist() {
  const qc = useQueryClient();
  const wl = useQuery({ queryKey: ["watchlist"], queryFn: () => api("/watchlist") });
  const quotes = useQuery({ queryKey: ["quotes"], queryFn: () => api("/quotes"), staleTime:300_000, refetchInterval:300_000, refetchOnWindowFocus:false, retry:false });
  const [sym, setSym] = useState("");
  const [msg, setMsg] = useState("");
  const refresh = () => qc.invalidateQueries({ queryKey: ["watchlist"] });
  const add = useMutation({ mutationFn: (s: string) => api(`/watchlist/${s}`, { method: "PUT" }), onSuccess: refresh });
  const del = useMutation({ mutationFn: (s: string) => api(`/watchlist/${s}`, { method: "DELETE" }), onSuccess: refresh });
  const run = useMutation({ mutationFn: ({ type, symbols }: { type: string; symbols: string[] }) => post("/task", { type, symbols }),
    onSuccess: () => setMsg("Task started. Watch the Timeline."), onError: (e: any) => setMsg(e.message) });
  const all: string[] = wl.data?.symbols ?? [];
  return (
    <>
      <PageIntro eyebrow="MARKET DESK / YOUR RESEARCH UNIVERSE" title="Keep your next question close." description="Organise symbols, inspect public delayed daily prices, and choose what the jury researches next. Not a live-tick feed." icon="⊙" accent="lime"><Metric label="TRACKED SYMBOLS" value={all.length}/><span className="intro-tag">Delayed market observations</span></PageIntro>
      <Card title="Add symbol"><form className="flex gap-2" onSubmit={(e) => { e.preventDefault(); if (sym) add.mutate(sym.toUpperCase()); setSym(""); }}>
        <input aria-label="NSE symbol to add" className="min-w-0 flex-1 rounded bg-neutral-100 p-2 text-sm" placeholder="NSE symbol e.g. RELIANCE" value={sym} onChange={(e) => setSym(e.target.value)} /><Btn type="submit">Add</Btn></form></Card>
      <Card title="Batch">
        <div className="flex flex-wrap gap-2">{ACTIONS.map((a) => <Btn key={a} disabled={!all.length||run.isPending} onClick={() => run.mutate({ type: a, symbols: all })}>{a.toUpperCase()} ALL</Btn>)}</div>
        {msg && <p className="mt-2 text-sm text-neutral-900">{msg}</p>}
      </Card>
      {wl.isError&&<p role="alert">{String(wl.error)}</p>}{quotes.isError&&<p role="alert">Price observations unavailable: {String(quotes.error)}</p>}
      {wl.isSuccess&&!all.length&&<EmptyState icon="⊙" title="Pick your first research question" body="Add an NSE symbol above. Empty watchlists do not run batch tasks."/>}
      <div className="symbol-gallery grid gap-4 md:grid-cols-4">
        {all.map((s) => (
          <Card key={s} title={s} right={<button className="text-xs text-neutral-600" onClick={() => del.mutate(s)}>remove</button>}>
            <div className="symbol-price">{quotes.data?.[s]?Number(quotes.data[s].price).toLocaleString("en-IN",{style:"currency",currency:"INR"}):"Loading…"}</div><p className="mt-2 text-xs text-neutral-600">{quotes.data?.[s]?.as_of_date||"Date pending"} · {quotes.data?.[s]?.data_source||"Source pending"}</p>
            <div className="mt-2 flex flex-wrap gap-1">{ACTIONS.map((a) => <Btn key={a} className="!px-2 !py-0.5 text-xs" onClick={() => run.mutate({ type: a, symbols: [s] })}>{a}</Btn>)}</div>
          </Card>))}
      </div>
    </>
  );
}
