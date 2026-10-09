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
      <div className="grid gap-4 md:grid-cols-3">
        {Object.entries(agents.data ?? {}).map(([n, a]: any) => (
          <Card key={n} title={n} right={<span className="text-xs">{a.state}</span>}>
            <p className="text-xs text-neutral-400">${(cost.data?.agents?.[n]?.cost_usd ?? 0).toFixed(4)} · {cost.data?.agents?.[n]?.calls ?? 0} calls</p>
            <div className="mt-2 flex gap-2"><Btn onClick={() => setSel(n)}>Inspect</Btn>
              <Btn onClick={() => toggle.mutate({ n, a: a.state === "paused" ? "resume" : "pause" })}>{a.state === "paused" ? "Resume" : "Pause"}</Btn></div>
          </Card>))}
      </div>
      {sel && (
        <Card title={`${sel} detail`}>
          <h3 className="text-xs text-neutral-400">Recent events</h3>
          <pre className="max-h-56 overflow-auto text-xs">{JSON.stringify(hist.data?.history?.slice(-20), null, 1)}</pre>
          <h3 className="mt-2 text-xs text-neutral-400">Session ({sess.data?.message_count} messages)</h3>
          <pre className="max-h-56 overflow-auto text-xs">{JSON.stringify(sess.data?.messages, null, 1)}</pre>
        </Card>
      )}
    </>
  );
}
