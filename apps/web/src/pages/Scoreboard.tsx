import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";
import { Card } from "../components/ui";

const pct = (x?: number) => (x === undefined ? "–" : `${(x * 100).toFixed(1)}%`);

export default function Scoreboard() {
  const sb = useQuery({ queryKey: ["scoreboard"], queryFn: () => api("/scoreboard") });
  const d = sb.data;
  if (!d) return <p>Loading…</p>;
  return (
    <>
      <Card title="How have verdicts done?">
        <p className="text-sm text-slate-400">{d.total_verdicts} verdicts logged, {d.scored_rows} scored. Hits count direction only; excess return is vs Nifty. {d.note}</p>
        <table className="mt-3 w-full text-left text-sm"><thead className="text-slate-400"><tr><th>Horizon</th><th>n</th><th>Hit rate</th><th>Avg excess</th></tr></thead>
          <tbody>{Object.entries(d.by_horizon).map(([h, v]: any) => (<tr key={h} className="border-t border-slate-800"><td>{h}d</td><td>{v.n}</td><td>{pct(v.hit_rate)}</td><td>{pct(v.avg_excess_return)}</td></tr>))}</tbody></table>
      </Card>
      <Card title="By regime (5-day)">
        <table className="w-full text-left text-sm"><tbody>{Object.entries(d.by_regime).map(([g, v]: any) => (
          <tr key={g} className="border-t border-slate-800"><td>{g}</td><td>{v["5"].n}</td><td>{pct(v["5"].hit_rate)}</td></tr>))}</tbody></table>
      </Card>
      <Card title="Calibration (does higher confidence mean more hits?)">
        <table className="w-full text-left text-sm"><tbody>{Object.entries(d.calibration).map(([b, v]: any) => (
          <tr key={b} className="border-t border-slate-800"><td>{b}</td><td>{v.n}</td><td>{pct(v.hit_rate)}</td></tr>))}</tbody></table>
      </Card>
    </>
  );
}
