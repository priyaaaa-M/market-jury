import { PageIntro, Metric, EmptyState } from "../components/PageIntro";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api, post } from "../lib/api";
import { Btn, Card } from "../components/ui";

export default function Agents() {
  const qc = useQueryClient();
  const agents = useQuery({ queryKey: ["agents"], queryFn: () => api("/agents") });
  const cost = useQuery({ queryKey: ["cost"], queryFn: () => api("/cost") });
  const [sel, setSel] = useState<string | null>(null);
  const hist = useQuery({ queryKey: ["history", sel], queryFn: () => api(`/agents/${sel}/history`), enabled: !!sel });
  const sess = useQuery({ queryKey: ["session", sel], queryFn: () => api(`/agents/${sel}/session`), enabled: !!sel });
  const toggle = useMutation({ mutationFn: ({ n, a }: { n: string; a: string }) => post(`/agents/${n}/${a}`), onSuccess: () => qc.invalidateQueries({ queryKey: ["agents"] }) });
  return (
    <>
      <PageIntro eyebrow="THE PEOPLE BEHIND THE POSITIONS" title="Meet your research crew." description="Inspect real engine agents, their event history and session records. Role icons are illustrations, not model logos." icon="◈" accent="violet"><Metric label="ENGINE AGENTS" value={agents.data?Object.keys(agents.data).length:"Loading…"}/><Metric label="COST TODAY" value={cost.data?`$${Number(cost.data.total_cost_usd).toFixed(4)}`:"Loading…"}/></PageIntro>
      {agents.isError&&<p role="alert">{String(agents.error)}</p>}
      {agents.isSuccess&&!Object.keys(agents.data??{}).length&&<EmptyState title="No engine agents reported" body="Check your connection. This page only lists agents returned by the engine."/>}
      <div className="agent-gallery grid gap-4 md:grid-cols-3">
        {Object.entries(agents.data ?? {}).map(([n, a]: any) => (
          <Card key={n} title={n.replaceAll("_"," ")} right={<span className="agent-state">{a.state}</span>}>
            <div className="agent-identity"><span aria-hidden="true">{n.includes("bull")?"B+":n.includes("bear")?"B−":n.includes("risk")?"R":n.includes("judge")?"J":"◈"}</span><b>{n.includes("bull")?"The optimist":n.includes("bear")?"The challenger":n.includes("risk")?"The guardian":n.includes("judge")?"The judge":"Research agent"}</b></div>
            <p className="text-xs text-neutral-600">{cost.isSuccess?`$${(cost.data?.agents?.[n]?.cost_usd ?? 0).toFixed(4)} · ${cost.data?.agents?.[n]?.calls ?? 0} recorded calls`:"Loading cost records…"}</p>
            <div className="mt-2 flex gap-2"><Btn onClick={() => setSel(n)}>Inspect</Btn>
              <Btn onClick={() => toggle.mutate({ n, a: a.state === "paused" ? "resume" : "pause" })}>{a.state === "paused" ? "Resume" : "Pause"}</Btn></div>
          </Card>))}
      </div>
      {sel && (
        <Card title={`${sel} detail`}>
          <h3 className="text-xs text-neutral-600">Recent events</h3>
          <pre className="max-h-56 overflow-auto text-xs">{JSON.stringify(hist.data?.history?.slice(-20), null, 1)}</pre>
          <h3 className="mt-2 text-xs text-neutral-600">Session ({sess.data?.message_count} messages)</h3>
          <pre className="max-h-56 overflow-auto text-xs">{JSON.stringify(sess.data?.messages, null, 1)}</pre>
        </Card>
      )}
    </>
  );
}
