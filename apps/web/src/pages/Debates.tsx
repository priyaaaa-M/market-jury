import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../lib/api";
import { Card, Verdict } from "../components/ui";

export default function Debates() {
  const wl = useQuery({ queryKey: ["watchlist"], queryFn: () => api("/watchlist") });
  const [sym, setSym] = useState("");
  const symbol = sym || wl.data?.symbols?.[0];
  const v = useQuery({ queryKey: ["consensus", symbol], queryFn: () => api(`/consensus/${symbol}`), enabled: !!symbol, retry: false });
  return (
    <>
      <div className="flex flex-wrap gap-2">{(wl.data?.symbols ?? []).map((s: string) => (
        <button key={s} onClick={() => setSym(s)} className={`rounded px-3 py-1 text-sm ${s === symbol ? "bg-neutral-200" : "bg-neutral-100"}`}>{s}</button>))}</div>
      {v.isError && <p className="text-sm text-neutral-600">No debate for {symbol} yet. Start one from the Watchlist page.</p>}
      {v.data && (
        <>
          <Card title={`${v.data.symbol} verdict`}>
            <div className="flex flex-wrap items-center gap-4"><Verdict v={v.data.verdict} /><span>{Math.round(v.data.confidence * 100)}% confidence</span>
              <span className="text-neutral-600">bull {v.data.bull_score} vs bear {v.data.bear_score}</span><span className="text-neutral-600">regime {v.data.regime}</span></div>
            <p className="mt-2 text-sm text-neutral-700">{v.data.reasoning}</p>
          </Card>
          <div className="grid gap-4 md:grid-cols-2">
            {v.data.positions.map((p: any, i: number) => (
              <Card key={i} title={`${p.stance} · round ${p.round + 1}`}>
                <p className="text-sm">{p.argument}</p>
                <div className="mt-2 flex flex-wrap gap-1">{p.evidence.map((e: string) => <span key={e} className="rounded bg-neutral-100 px-2 py-0.5 text-xs">{e}</span>)}</div>
              </Card>))}
          </div>
        </>
      )}
    </>
  );
}
