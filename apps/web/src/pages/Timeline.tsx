import { PageIntro, Metric, EmptyState } from "../components/PageIntro";
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
    <>
      <PageIntro eyebrow="THE RECORD, NOT A HIGHLIGHT REEL" title="Every step leaves a trail." description="Follow recorded research, decisions and task failures. No animated sample events, no hidden failed sessions." icon="≡" accent="cyan"><Metric label="RECORDED EVENTS" value={hist.data?hist.data.events.length:"Loading…"}/></PageIntro>
    <Card title="Event stream" right={
      <div className="flex flex-wrap gap-2 text-sm">
        <select aria-label="Filter event type" className="rounded bg-neutral-100 p-1" value={type} onChange={(e) => setType(e.target.value)}>
          <option value="">all</option>{["research", "screen", "analysis", "debate_started", "consensus", "trade_pending", "trade", "task_done", "task_failed"].map((t) => <option key={t}>{t}</option>)}</select>
        <input aria-label="Events since date" type="date" className="rounded bg-neutral-100 p-1" value={since} onChange={(e) => setSince(e.target.value)} />
      </div>}>
      {hist.isError&&<p role="alert">{String(hist.error)}</p>}
      {hist.isSuccess&&!hist.data?.events?.length&&<EmptyState icon="≡" title="Nothing recorded in this view yet" body="Run a discussion to create a real event trail, or clear the filters to see other recorded events." to="/debates"/>}
      {(hist.data?.events ?? []).map((e: any, i: number) => (
        <details key={i} className="timeline-event border-t border-neutral-200 py-1 text-sm"><summary className="cursor-pointer">
          <span className="text-neutral-600">{e.time.slice(11, 19)}</span> <b>{e.event}</b> {e.data.symbol ?? ""}</summary>
          <pre className="text-xs text-neutral-600">{JSON.stringify(e.data, null, 1)}</pre></details>))}
    </Card>
    </>
  );
}
