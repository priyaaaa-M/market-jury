const BASE = import.meta.env.VITE_API_URL || "/api";
const KEY_NAME = "engine_api_key";

export const getKey = () => localStorage.getItem(KEY_NAME) || "";
export const setKey = (k: string) => localStorage.setItem(KEY_NAME, k);

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
    : `${location.protocol === "https:" ? "wss" : "ws"}://${location.hostname}:8008`;
  return `${base}/ws?token=${encodeURIComponent(getKey())}`;
}
