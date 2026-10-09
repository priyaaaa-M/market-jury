import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";
import { Card, Stat } from "../components/ui";

export default function Regime() {
  const r = useQuery({ queryKey: ["regime"], queryFn: () => api("/regime") });
  const d = r.data;
  if (!d) return <p>Loading…</p>;
  return (
    <Card title="Current regime">
      <div className="flex flex-wrap gap-6"><Stat label="Regime" value={d.regime} /><Stat label="Trend" value={d.trend} /><Stat label="Volatility" value={d.volatility} />
        <Stat label="Size multiplier" value={d.size_multiplier} /><Stat label="Extra confidence required" value={`+${Math.round(d.confidence_adjust * 100)}%`} /></div>
      <pre className="mt-3 text-xs text-slate-400">{JSON.stringify(d.inputs, null, 1)}</pre>
      <p className="mt-2 text-sm text-slate-400">In high-volatility or falling regimes the engine asks for more conviction and trades smaller.</p>
    </Card>
  );
}
