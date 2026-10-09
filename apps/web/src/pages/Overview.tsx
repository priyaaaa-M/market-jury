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
  const p = pf.data;
  return (
    <>
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
