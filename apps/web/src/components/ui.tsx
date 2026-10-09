import { ReactNode } from "react";

export const Card = ({ title, children, right }: { title?: string; children: ReactNode; right?: ReactNode }) => (
  <section className="rounded-lg border border-neutral-800 bg-neutral-900 p-4">
    {(title || right) && (
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-neutral-400">{title}</h2>{right}
      </div>
    )}
    {children}
  </section>
);

export const Stat = ({ label, value, tone }: { label: string; value: ReactNode; tone?: "good" | "bad" }) => (
  <div>
    <div className="text-xs text-neutral-400">{label}</div>
    <div className={`text-xl font-semibold ${tone === "good" ? "text-neutral-100" : tone === "bad" ? "text-neutral-100" : ""}`}>{value}</div>
  </div>
);

export const Btn = ({ children, ...p }: React.ButtonHTMLAttributes<HTMLButtonElement>) => (
  <button {...p} className={`rounded bg-neutral-700 px-3 py-1 text-sm hover:bg-neutral-600 disabled:opacity-40 ${p.className || ""}`}>{children}</button>
);

const VC: Record<string, string> = {
  strong_buy: "bg-white text-black border border-white", buy: "bg-white text-black border border-white", hold: "bg-neutral-700 text-white border border-neutral-500", sell: "bg-black text-white border border-white", strong_sell: "bg-black text-white border border-white",
};
export const Verdict = ({ v }: { v: string }) => (
  <span className={`rounded px-2 py-0.5 text-xs font-semibold uppercase ${VC[v] || "bg-neutral-700"}`}>{v.replace("_", " ")}</span>
);

export const inr = (n: number) => "₹" + n.toLocaleString("en-IN", { maximumFractionDigits: 0 });
export const tone = (n: number) => (n > 0 ? "good" : n < 0 ? "bad" : undefined) as "good" | "bad" | undefined;
