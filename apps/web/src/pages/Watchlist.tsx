import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api, post } from "../lib/api";
import { Btn, Card } from "../components/ui";

const ACTIONS = ["screen", "research", "debate", "analyze"];

export default function Watchlist() {
  const qc = useQueryClient();
  const wl = useQuery({ queryKey: ["watchlist"], queryFn: () => api("/watchlist") });
  const quotes = useQuery({ queryKey: ["quotes"], queryFn: () => api("/quotes"), refetchInterval: 30_000 });
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
      <Card title="Add symbol"><form className="flex gap-2" onSubmit={(e) => { e.preventDefault(); if (sym) add.mutate(sym.toUpperCase()); setSym(""); }}>
        <input className="rounded bg-neutral-800 p-2 text-sm" placeholder="NSE symbol e.g. RELIANCE" value={sym} onChange={(e) => setSym(e.target.value)} /><Btn type="submit">Add</Btn></form></Card>
      <Card title="Batch">
        <div className="flex gap-2">{ACTIONS.map((a) => <Btn key={a} onClick={() => run.mutate({ type: a, symbols: all })}>{a.toUpperCase()} ALL</Btn>)}</div>
        {msg && <p className="mt-2 text-sm text-neutral-100">{msg}</p>}
      </Card>
      <div className="grid gap-4 md:grid-cols-4">
        {all.map((s) => (
          <Card key={s} title={s} right={<button className="text-xs text-neutral-400" onClick={() => del.mutate(s)}>remove</button>}>
            <div className="text-lg">{quotes.data?.[s]?.price ?? "…"}</div>
            <div className="mt-2 flex flex-wrap gap-1">{ACTIONS.map((a) => <Btn key={a} className="!px-2 !py-0.5 text-xs" onClick={() => run.mutate({ type: a, symbols: [s] })}>{a}</Btn>)}</div>
          </Card>))}
      </div>
    </>
  );
}
