const BASE = import.meta.env.VITE_API_URL || "/api";
const KEY_NAME = "engine_api_key";

export const getKey = () => localStorage.getItem(KEY_NAME) || "";
export const setKey = (k: string) => localStorage.setItem(KEY_NAME, k.trim());

export function clearKey() { localStorage.removeItem(KEY_NAME); }
export async function validateKey(key: string) {
  const res = await fetch(`${BASE}/status`, {headers: {"X-API-Key": key.trim()}, signal: AbortSignal.timeout(90000)});
  if (res.status === 401) throw new Error("Invalid engine key. Copy API_KEY from your Render service's Environment tab, not the rnd_ management key.");
  if (!res.ok) throw new Error(`Engine returned ${res.status}. Try again shortly.`);
  return res.json();
}
export async function api<T = any>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", "X-API-Key": getKey(), ...(init.headers || {}) },
  });
  if (res.status === 401) throw new Error("Invalid API key");
  if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || res.statusText);
  return res.json();
}

export const post = <T = any>(path: string, body?: unknown) =>
  api<T>(path, { method: "POST", body: body === undefined ? undefined : JSON.stringify(body) });

export function wsUrl(): string {
  const base = import.meta.env.VITE_API_URL
    ? import.meta.env.VITE_API_URL.replace(/^http/, "ws")
    : `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/api`;
  return `${base}/ws?token=${encodeURIComponent(getKey())}`;
}
