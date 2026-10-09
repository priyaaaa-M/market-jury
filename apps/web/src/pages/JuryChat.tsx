import GettingStarted from "../components/GettingStarted";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { motion } from "motion/react";
import { api, post } from "../lib/api";
import { Btn, Card, Verdict } from "../components/ui";
const QUESTIONS=["Why did the judge decide?","What's the bear case?","What's the bull case?","What risks are missing?","Summarise the discussion"];
export default function JuryChat() {
  const wl=useQuery({queryKey:["watchlist"],queryFn:()=>api("/watchlist")});
  const [symbol,setSymbol]=useState("");const [question,setQuestion]=useState("");const [turns,setTurns]=useState<any[]>([]);const [busy,setBusy]=useState(false);const [error,setError]=useState("");
  const selected=symbol||wl.data?.symbols?.[0]||"TCS";
  const ask=async(q:string)=>{if(busy||!q.trim())return;setBusy(true);setError("");try {const reply=await post("/jury-chat",{symbol:selected,question:q.trim()});setTurns(t=>[...t.slice(-19),{question:q,symbol:selected,reply}]);setQuestion("");}catch(e){setError(String(e));}finally{setBusy(false);}};
  return <>
    <GettingStarted symbol={selected}/>
    <Card title="Ask the jury" right={<span className="discussion-label">EVIDENCE, NOT GUESSES</span>}><h2 className="text-2xl font-bold tracking-tight">Ask why. See the receipts.</h2><p className="mt-2 text-sm text-neutral-600">Answers quote saved debates exactly. No new model call, no made-up verdicts. Your messages stay in this tab and are not saved on the server or sent to OpenRouter.</p></Card>
    <div className="chat-workspace"><div className="chat-main">
      <div className="chat-toolbar"><label>Stock <select aria-label="Chat stock" value={selected} onChange={e=>setSymbol(e.target.value)} className="rounded bg-neutral-100 p-2 ml-2">{(wl.data?.symbols||["TCS"]).map((s:string)=><option key={s}>{s}</option>)}</select></label><Btn onClick={()=>setTurns([])}>Clear this chat</Btn></div>
      <div className="jury-chat-log" role="log" aria-live="polite">
        {!turns.length&&<div className="stream-empty"><span className="text-4xl">↳</span><b>Your questions start with a saved debate.</b><p>Run a discussion first, then ask about the latest saved verdict for the same stock.</p></div>}
        {turns.map((t,i)=><motion.div key={i} initial={{opacity:0,y:8}} animate={{opacity:1,y:0}} className="chat-exchange"><div className="user-question"><small>YOU · {t.symbol}</small><p>{t.question}</p></div><article className="jury-answer"><div className="turn-meta"><b>MJ · Evidence desk</b><span>Local lookup · $0</span></div>{t.reply.verdict&&<div className="my-3"><Verdict v={t.reply.verdict}/></div>}<p className="text-sm leading-relaxed">{t.reply.answer}</p>{t.reply.sources?.map((s:any,j:number)=><blockquote key={j} className="source-quote"><b>{s.role}</b><small>{s.model}{s.round?` · round ${s.round}`:""}</small><p>{s.quote}</p></blockquote>)}{t.reply.timestamp&&<div className="source-footnote">Saved debate #{t.reply.verdict_id??"test"} · {new Date(t.reply.timestamp).toLocaleString()} · {t.reply.data_source}<a href={`/debates`} className="underline block mt-2">Open discussion room ↗</a></div>}</article></motion.div>)}
      </div>
      <form className="chat-composer" onSubmit={e=>{e.preventDefault();ask(question);}}><label htmlFor="jury-question" className="sr-only">Message the jury</label><textarea id="jury-question" rows={2} maxLength={1000} placeholder={`Ask about ${selected}'s saved debate…`} value={question} onChange={e=>setQuestion(e.target.value)}/><Btn disabled={busy||!question.trim()} type="submit">{busy?"Reading…":"Ask ↗"}</Btn></form>{error&&<p role="alert" className="text-sm p-3">{error}</p>}
    </div><aside className="chat-help"><h3>Start with a question.</h3>{QUESTIONS.map(q=><button key={q} disabled={busy} onClick={()=>ask(q)}>{q}<span>↗</span></button>)}<p>Pick a stock first. No saved debate? The jury will say so. Chat never starts a trade or a new debate.</p><p>Quotes are model opinions, not independently verified market facts. Research and paper trading only.</p></aside></div>
  </>;
}
