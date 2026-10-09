import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../lib/api";
import { Card } from "../components/ui";
import { useLive } from "../lib/useLive";

export default function Timeline() {
  const [type, setType] = useState("");
  const [since, setSince] = useState("");
  const { events: live } = useLive();
  const hist = useQuery({ queryKey: ["timeline", type, since, live.length], queryFn: () => api(`/timeline?limit=200${type ? `&event=${type}` : ""}${since ? `&since=${since}` : ""}`) });
  return (
    <Card title="Event stream" right={
      <div className="flex gap-2 text-sm">
        <select className="rounded bg-neutral-800 p-1" value={type} onChange={(e) => setType(e.target.value)}>
          <option value="">all</option>{["research", "screen", "analysis", "debate_started", "consensus", "trade_pending", "trade", "task_done", "task_failed"].map((t) => <option key={t}>{t}</option>)}</select>
        <input type="date" className="rounded bg-neutral-800 p-1" value={since} onChange={(e) => setSince(e.target.value)} />
      </div>}>
      {(hist.data?.events ?? []).map((e: any, i: number) => (
        <details key={i} className="border-t border-neutral-800 py-1 text-sm"><summary className="cursor-pointer">
          <span className="text-neutral-400">{e.time.slice(11, 19)}</span> <b>{e.event}</b> {e.data.symbol ?? ""}</summary>
          <pre className="text-xs text-neutral-400">{JSON.stringify(e.data, null, 1)}</pre></details>))}
    </Card>
  );
}
