import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api, post } from "../lib/api";
import { Btn, Card, Stat, inr, tone } from "../components/ui";

export default function Portfolio() {
  const qc = useQueryClient();
  const pf = useQuery({ queryKey: ["portfolio"], queryFn: () => api("/portfolio") });
  const cost = useQuery({ queryKey: ["cost"], queryFn: () => api("/cost") });
  const [q, setQ] = useState("");
  const close = useMutation({ mutationFn: (s: string) => post(`/positions/${s}/close`), onSuccess: () => qc.invalidateQueries() });
  const p = pf.data;
  if (!p) return <p>Loading…</p>;
  const trades = [...p.trades].reverse().filter((t: any) => !q || t.symbol.includes(q.toUpperCase()) || t.action === q.toUpperCase());
  return (
    <>
      <Card title="Capital">
        <div className="flex flex-wrap gap-6">
          <Stat label="Cash" value={inr(p.capital)} /><Stat label="Positions" value={inr(p.positions_value)} />
          <Stat label="Realized" value={inr(p.realized_pnl)} tone={tone(p.realized_pnl)} />
          <Stat label="Unrealized" value={inr(p.unrealized_pnl)} tone={tone(p.unrealized_pnl)} />
          <Stat label="Win rate" value={`${p.win_rate}%`} />
        </div>
      </Card>
      <Card title="Holdings">
        {Object.entries(p.positions).map(([s, v]: any) => (
          <div key={s} className="flex items-center justify-between border-t border-neutral-200 py-2 text-sm">
            <span>{s}: {v.qty} @ {v.avg_price}</span><Btn onClick={() => close.mutate(s)}>Close</Btn>
          </div>
        ))}
        {!Object.keys(p.positions).length && <p className="text-sm text-neutral-600">No open positions.</p>}
      </Card>
      <Card title="LLM cost today">
        <p className="text-sm">${cost.data?.total_cost_usd?.toFixed(4)} of ${cost.data?.daily_budget} budget</p>
        <div className="mt-2 h-2 rounded bg-neutral-100"><div className="h-2 rounded bg-neutral-200"
          style={{ width: `${Math.min(100, ((cost.data?.total_cost_usd ?? 0) / (cost.data?.daily_budget || 1)) * 100)}%` }} /></div>
      </Card>
      <Card title="Trade log" right={<input placeholder="symbol / action" className="rounded bg-neutral-100 px-2 py-1 text-sm" value={q} onChange={(e) => setQ(e.target.value)} />}>
        <table className="w-full text-left text-sm"><thead className="text-neutral-600"><tr><th>Time</th><th>Symbol</th><th>Action</th><th>Qty</th><th>Fill</th><th>Fees</th><th>P&L</th></tr></thead>
          <tbody>{trades.map((t: any) => (
            <tr key={t.order_id} className="border-t border-neutral-200"><td>{t.timestamp.slice(0, 16)}</td><td>{t.symbol}</td><td>{t.action}</td>
              <td>{t.quantity}</td><td>{t.fill_price}</td><td>{t.fees}</td><td className={t.pnl > 0 ? "text-neutral-900" : t.pnl < 0 ? "text-neutral-900" : ""}>{t.pnl}</td></tr>))}</tbody></table>
      </Card>
    </>
  );
}
