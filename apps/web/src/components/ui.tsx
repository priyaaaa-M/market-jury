import { ReactNode } from "react";

export const Card = ({ title, children, right }: { title?: string; children: ReactNode; right?: ReactNode }) => (
  <section className="rounded-lg border border-slate-800 bg-slate-900 p-4">
    {(title || right) && (
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">{title}</h2>{right}
      </div>
    )}
    {children}
  </section>
);

export const Stat = ({ label, value, tone }: { label: string; value: ReactNode; tone?: "good" | "bad" }) => (
  <div>
    <div className="text-xs text-slate-400">{label}</div>
    <div className={`text-xl font-semibold ${tone === "good" ? "text-emerald-400" : tone === "bad" ? "text-rose-400" : ""}`}>{value}</div>
  </div>
);

export const Btn = ({ children, ...p }: React.ButtonHTMLAttributes<HTMLButtonElement>) => (
  <button {...p} className={`rounded bg-slate-700 px-3 py-1 text-sm hover:bg-slate-600 disabled:opacity-40 ${p.className || ""}`}>{children}</button>
);

const VC: Record<string, string> = {
  strong_buy: "bg-emerald-600", buy: "bg-emerald-800", hold: "bg-slate-600", sell: "bg-rose-800", strong_sell: "bg-rose-600",
};
export const Verdict = ({ v }: { v: string }) => (
  <span className={`rounded px-2 py-0.5 text-xs font-semibold uppercase ${VC[v] || "bg-slate-700"}`}>{v.replace("_", " ")}</span>
);

export const inr = (n: number) => "₹" + n.toLocaleString("en-IN", { maximumFractionDigits: 0 });
export const tone = (n: number) => (n > 0 ? "good" : n < 0 ? "bad" : undefined) as "good" | "bad" | undefined;
