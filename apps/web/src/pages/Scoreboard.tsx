import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";
import { Card } from "../components/ui";

const pct = (x?: number) => (x === undefined ? "–" : `${(x * 100).toFixed(1)}%`);

export default function Scoreboard() {
  const sb = useQuery({ queryKey: ["scoreboard"], queryFn: () => api("/scoreboard") });
  const d = sb.data;
  if (sb.isError) return <p role="alert">{String(sb.error)}</p>;
  if (!d) return <p>Loading…</p>;
  return (
    <>
      <Card title="How have verdicts done?">
        <p className="text-sm text-neutral-400">{d.total_verdicts} verdicts logged, {d.scored_rows} horizon rows scored. {d.excluded_demo} demo calls excluded. Hits count direction only; excess return is vs Nifty. {d.note}</p>
        <table className="mt-3 w-full text-left text-sm"><thead className="text-neutral-400"><tr><th>Horizon</th><th>n</th><th>Hit rate</th><th>Avg excess</th></tr></thead>
          <tbody>{Object.entries(d.by_horizon).map(([h, v]: any) => (<tr key={h} className="border-t border-neutral-800"><td>{h} {h === "1" ? "session" : "sessions"}</td><td>{v.n}</td><td>{pct(v.hit_rate)}</td><td>{pct(v.avg_excess_return)}</td></tr>))}</tbody></table>
      </Card>
      <Card title="By regime (5-session)">
        {Object.keys(d.by_regime).length === 0 && <p className="text-sm text-neutral-300">No real five-session outcomes yet.</p>}
        <table className="w-full text-left text-sm"><tbody>{Object.entries(d.by_regime).map(([g, v]: any) => (
          <tr key={g} className="border-t border-neutral-800"><td>{g}</td><td>{v["5"].n}</td><td>{pct(v["5"].hit_rate)}</td></tr>))}</tbody></table>
      </Card>
      <Card title="Calibration (does higher confidence mean more hits?)">
        {Object.keys(d.calibration).length === 0 && <p className="text-sm text-neutral-300">Needs real five-session samples. No accuracy claim from a demo.</p>}
        <table className="w-full text-left text-sm"><tbody>{Object.entries(d.calibration).map(([b, v]: any) => (
          <tr key={b} className="border-t border-neutral-800"><td>{b}</td><td>{v.n}</td><td>{pct(v.hit_rate)}</td></tr>))}</tbody></table>
      </Card>
      <Card title="Per-call audit trail">
        <p className="text-sm text-neutral-300">Every call stays visible, including holds and calls waiting for enough real observations.</p>
        <div className="overflow-x-auto"><table className="mt-3 w-full text-left text-sm"><thead><tr><th>Symbol</th><th>Verdict</th><th>Source</th><th>Outcome status</th></tr></thead><tbody>{(d.outcomes??[]).map((v:any)=><tr key={v.id} className="border-t border-neutral-700"><td>{v.symbol}</td><td>{v.verdict}</td><td>{v.data_source}</td><td>{v.status}</td></tr>)}</tbody></table></div>
      </Card>
    </>
  );
}
