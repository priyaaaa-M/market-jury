import { ReactNode } from "react";
import { motion } from "motion/react";

export const Card = ({ title, children, right }: { title?: string; children: ReactNode; right?: ReactNode }) => (
  <motion.section initial={{opacity:0,y:8}} whileInView={{opacity:1,y:0}} viewport={{once:true,amount:.1}} transition={{duration:.25}} className="data-card rounded-lg border border-neutral-200 bg-white p-4">
    {(title || right) && (
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-neutral-600">{title}</h2>{right}
      </div>
    )}
    {children}
  </motion.section>
);

export const Stat = ({ label, value, tone }: { label: string; value: ReactNode; tone?: "good" | "bad" }) => (
  <div>
    <div className="text-xs text-neutral-600">{label}</div>
    <div className={`text-xl font-semibold ${tone === "good" ? "text-neutral-900" : tone === "bad" ? "text-neutral-900" : ""}`}>{value}</div>
  </div>
);

export const Btn = ({ children, ...p }: React.ButtonHTMLAttributes<HTMLButtonElement>) => (
  <button {...p} className={`rounded bg-neutral-200 px-3 py-1 text-sm hover:bg-neutral-300 disabled:opacity-40 ${p.className || ""}`}>{children}</button>
);

const VC: Record<string, string> = {
  strong_buy: "bg-white text-black border border-black", buy: "bg-white text-black border border-black", hold: "bg-neutral-700 text-white border border-neutral-500", sell: "bg-black text-white border border-white", strong_sell: "bg-black text-white border border-white",
};
export const Verdict = ({ v }: { v: string }) => (
  <span className={`rounded px-2 py-0.5 text-xs font-semibold uppercase ${VC[v] || "bg-neutral-700"}`}>{v.replace("_", " ")}</span>
);

export const inr = (n: number) => "₹" + n.toLocaleString("en-IN", { maximumFractionDigits: 0 });
export const tone = (n: number) => (n > 0 ? "good" : n < 0 ? "bad" : undefined) as "good" | "bad" | undefined;
