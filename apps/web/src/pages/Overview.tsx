import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, post } from "../lib/api";
import { Btn, Card, Stat, Verdict, inr, tone } from "../components/ui";

export default function Overview() {
  const qc = useQueryClient();
  const pf = useQuery({ queryKey: ["portfolio"], queryFn: () => api("/portfolio") });
  const verdicts = useQuery({ queryKey: ["verdicts"], queryFn: () => api("/verdicts?limit=6") });
  const pending = useQuery({ queryKey: ["pending"], queryFn: () => api("/pending") });
  const regime = useQuery({ queryKey: ["regime"], queryFn: () => api("/regime"), staleTime: 60_000 });
  const act = useMutation({ mutationFn: ({ kind, i }: { kind: string; i: number }) => post(`/trade/${kind}/${i}`),
    onSuccess: () => qc.invalidateQueries() });
  const quotes = useQuery({queryKey:["quotes"], queryFn:()=>api("/quotes")});
  const p = pf.data;
  return (
    <>
      <Card title="Market observations">
        {quotes.isError && <p role="alert">{String(quotes.error)}</p>}
        <div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead><tr><th>Symbol</th><th>Price</th><th>As of</th><th>Source / freshness</th><th>Independent check</th></tr></thead><tbody>{Object.values(quotes.data??{}).map((q:any)=><tr key={q.symbol} className="border-t border-slate-700"><td>{q.symbol}</td><td>{Number(q.price).toLocaleString("en-IN", {style:"currency",currency:"INR",minimumFractionDigits:2,maximumFractionDigits:2})}</td><td>{q.as_of_date??q.timestamp}</td><td>{q.data_source} · {q.freshness??"demo"}</td><td><span>{q.crosscheck?.status??"unavailable"}</span>{q.crosscheck?.reason && <p className="text-xs text-slate-300">{q.crosscheck.reason.replaceAll("_", " ")}</p>}{q.crosscheck?.secondary && <details className="mt-1 text-xs"><summary>Second source evidence</summary><p>{q.crosscheck.secondary.provider}: ₹{q.crosscheck.secondary.price} · {q.crosscheck.secondary.as_of_date} · {q.crosscheck.secondary.comparison_price_type}</p><p>Source time: {q.crosscheck.secondary.source_timestamp}</p><p>{q.crosscheck.secondary.caveat}</p><a className="underline" href={q.crosscheck.secondary.source_url} target="_blank" rel="noreferrer">Source</a></details>}</td></tr>)}</tbody></table></div>
        <p className="mt-2 text-xs text-slate-300">Yahoo mode uses delayed adjusted daily closes, not live executable quotes. Same-day bars are provider-reported, not independently NSE-verified. Check source date before use.</p>
      </Card>
      <Card title="Market regime">
        <div className="flex flex-wrap gap-6">
          <Stat label="Regime" value={regime.data?.regime ?? "…"} />
          <Stat label="Size multiplier" value={regime.data?.size_multiplier ?? "…"} />
          <Stat label="India VIX" value={regime.data?.inputs?.india_vix ?? "…"} />
        </div>
      </Card>
      {p && (
        <Card title="Paper portfolio">
          <div className="flex flex-wrap gap-6">
            <Stat label="Total value" value={inr(p.total_value)} />
            <Stat label="P&L" value={`${inr(p.total_pnl)} (${p.pnl_pct}%)`} tone={tone(p.total_pnl)} />
            <Stat label="Trades" value={p.total_trades} /><Stat label="Win rate" value={`${p.win_rate}%`} />
          </div>
        </Card>
      )}
      <Card title="Awaiting your approval">
        {(pending.data?.pending ?? []).length === 0 && <p className="text-sm text-slate-400">Nothing pending.</p>}
        {(pending.data?.pending ?? []).map((t: any, i: number) => (
          <div key={i} className="flex items-center justify-between border-t border-slate-800 py-2 text-sm">
            <span>{t.action} {t.quantity} {t.symbol} · conf {Math.round(t.confidence * 100)}% · {t.reasoning}</span>
            <span className="flex gap-2"><Btn onClick={() => act.mutate({ kind: "approve", i })}>Approve</Btn>
              <Btn onClick={() => act.mutate({ kind: "reject", i })}>Reject</Btn></span>
          </div>
        ))}
      </Card>
      <Card title="Latest verdicts">
        {(verdicts.data?.verdicts ?? []).map((v: any) => (
          <div key={v.id} className="flex items-center gap-3 border-t border-slate-800 py-2 text-sm">
            <b className="w-24">{v.symbol}</b><Verdict v={v.verdict} /><span>{Math.round(v.confidence * 100)}%</span>
            <span className="text-slate-400">{v.regime}</span>
          </div>
        ))}
      </Card>
    </>
  );
}
