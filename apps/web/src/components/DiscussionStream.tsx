import { motion } from "motion/react";
import { Card } from "./ui";
export const JURY_ROLES = [
  {id:"debater_bull",label:"The optimist",role:"Bull case",icon:"B+",description:"What supports the upside?"},
  {id:"debater_bear",label:"The challenger",role:"Bear case",icon:"B−",description:"What breaks the thesis?"},
  {id:"risk_reviewer",label:"The guardian",role:"Risk review",icon:"R",description:"What's missing? What can go wrong?"},
  {id:"final_judge",label:"The judge",role:"Final decision",icon:"J",description:"Weigh the discussion. Decide or hold."},
];
export default function DiscussionStream({messages,current,replay=false}:{messages:any[];current?:any;replay?:boolean}) {
  return <Card title={replay?"Saved discussion · replay":"Live discussion · completed turns"} right={<span className="discussion-label">{messages.length} TURNS</span>}>
    <p className="mb-5 text-xs text-neutral-600">{replay?"Saved model arguments, shown in order. This is a replay, not agents speaking now.":"A bubble appears when an agent finishes and its response/cost checks pass. This is turn-by-turn, not token streaming."}</p>
    <div className="discussion-stream" role="log" aria-live="polite" aria-relevant="additions">
      {messages.map((m,i)=>{const r=JURY_ROLES.find(r=>r.id===m.agent_name);return <motion.article initial={{opacity:0,y:8}} animate={{opacity:1,y:0}} transition={{duration:.2}} key={`${m.agent_name}-${i}`} className={`agent-turn ${m.agent_name==="debater_bear"||m.agent_name==="final_judge"?"turn-right":""}`}>
        <span className="turn-avatar" aria-hidden="true">{r?.icon||"AI"}</span><div className="turn-body"><div className="turn-meta"><b>{r?.label||m.agent_name}</b><span>{r?.role} · turn {i+1}</span></div><div className="turn-bubble"><p className="model-line">{m.receipt?.actual_model||m.model||"Model not recorded"}</p><p className="leading-relaxed text-sm whitespace-pre-wrap">{m.argument}</p>{Array.isArray(m.evidence)&&m.evidence.length>0&&<details className="mt-3 text-xs"><summary>View model-cited evidence</summary><ul className="mt-2 list-disc pl-4">{m.evidence.map((e:string,j:number)=><li key={j}>{e}</li>)}</ul></details>}<p className="turn-receipt">{m.receipt?.cost_usd===0?"$0 provider receipt checked":"Historical cost not verified"}{m.timestamp?` · ${new Date(m.timestamp).toLocaleTimeString()}`:""}</p></div></div>
      </motion.article>})}
      {!messages.length&&<div className="stream-empty"><span className="text-3xl">◉</span><b>The room is quiet.</b><p>Start a discussion. Real completed turns will appear here.</p></div>}
      {!replay&&["running","retrying"].includes(current?.state)&&<div className="turn-wait" role="status"><span className="status-dot live-dot"/>{JURY_ROLES.find(r=>r.id===current.role)?.label||current.role} · {current.state==="retrying"?"retrying free model":"waiting for model response"}. No answer yet.</div>}
      {!replay&&current?.state==="failed"&&<p role="alert" className="turn-wait">{current.message}</p>}
    </div>
  </Card>;
}
