import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { wsUrl } from "./api";

export type LiveEvent = { event: string; time: string; data: Record<string, unknown> };

/** One WebSocket for the whole app. Events refresh the relevant queries, so no polling. */
export function useLive() {
  const qc = useQueryClient();
  const [events, setEvents] = useState<LiveEvent[]>([]);
  const [connected, setConnected] = useState(false);
  useEffect(() => {
    let ws: WebSocket | null = null;
    let stop = false;
    const connect = () => {
      ws = new WebSocket(wsUrl());
      ws.onopen = () => setConnected(true);
      ws.onclose = () => { setConnected(false); if (!stop) setTimeout(connect, 3000); };
      ws.onmessage = (m) => {
        const ev: LiveEvent = JSON.parse(m.data);
        setEvents((p) => [ev, ...p].slice(0, 200));
        const keys = ["status", "portfolio", "pending", "cost", "agents"];
        if (["consensus", "debate_started"].includes(ev.event)) keys.push("verdicts", "scoreboard", "consensus");
        if (["research", "analysis", "screen"].includes(ev.event)) keys.push("signals", "research");
        keys.forEach((k) => qc.invalidateQueries({ queryKey: [k] }));
      };
    };
    connect();
    return () => { stop = true; ws?.close(); };
  }, [qc]);
  return { events, connected };
}
