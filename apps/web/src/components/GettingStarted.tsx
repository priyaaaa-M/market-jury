import { Link } from "react-router-dom";
import { motion } from "motion/react";

const STEPS=[
  {title:"Start the conversation",body:"Discussion room → pick a stock → Start discussion.",icon:"↗"},
  {title:"Let the jury weigh in",body:"Real turns arrive as agents finish. Wait for the saved verdict. Free models may take minutes or fail.",icon:"◈"},
  {title:"Ask why. Get receipts.",body:"Pick the same stock in chat. Answers quote its latest saved discussion, not a new forecast.",icon:"↳"},
];
export default function GettingStarted({symbol}:{symbol?:string}) {
  return <section className="launch-guide" aria-label="How to start with the jury">
    <div className="guide-hero">
      <div className="guide-copy"><span className="guide-eyebrow"><span className="spark-mark">✳</span> YOUR FIRST DISCUSSION STARTS HERE</span>
        <h2>Big questions.<br/><span>Real receipts.</span></h2>
        <p>Four roles. One evidence-led discussion.<br/>Run a debate first. Then ask the jury why.</p>
        <div className="guide-actions"><Link className="onboarding-primary" to="/debates">Start a discussion <span>↗</span></Link><Link className="onboarding-secondary" to="/chat">Meet the evidence desk ↳</Link></div>
        <small>{symbol?`Research ${symbol}. `:"Public market research. "}Paper only. No sample verdicts.</small>
      </div>
      <div className="jury-orbit" aria-label="Four jury roles, decorative illustration, not live activity"><div className="orbit-ring ring-one"/><div className="orbit-ring ring-two"/><div className="orbit-center"><b>MJ</b><span>THE JURY</span></div>{[{role:"BULL",letter:"B+",style:"bull"},{role:"BEAR",letter:"B−",style:"bear"},{role:"RISK",letter:"R",style:"risk"},{role:"JUDGE",letter:"J",style:"judge"}].map((r,i)=><motion.div key={r.role} className={`orbit-role orbit-${r.style}`} initial={{opacity:0,scale:.8}} animate={{opacity:1,scale:1}} transition={{delay:i*.1,duration:.35}}><b>{r.letter}</b><span>{r.role}</span></motion.div>)}<span className="orbit-note">FOUR PERSPECTIVES · NOT LIVE ACTIVITY</span></div>
    </div>
    <div className="guide-lower"><div className="getting-started-steps">{STEPS.map((s,i)=><motion.div className="guide-step" key={s.title} initial={{opacity:0,y:12}} whileInView={{opacity:1,y:0}} viewport={{once:true}} transition={{delay:i*.09,duration:.3}}><span className="step-index">0{i+1}</span><span className="step-icon">{s.icon}</span><h3>{s.title}</h3><p>{s.body}</p></motion.div>)}</div>
      <div className="guide-notes"><p><b>Prices ≠ a verdict.</b> Prices can appear before any debate. An empty workspace isn't dummy evidence. A failed session creates no new verdict.</p><details><summary>Market closed? Here's how to research anyway ↗</summary><p>In <Link to="/settings">Profile & settings → Trading</Link>, enable Out-of-hours research (AGENT_FORCE_ACTIVE). It does not enable live trading or automatic paper orders.</p></details><small>Free Render uses temporary storage. Saved debates may disappear after a restart or redeploy.</small></div>
    </div>
  </section>;
}
