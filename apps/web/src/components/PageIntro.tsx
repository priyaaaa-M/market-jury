import { motion } from "motion/react";
import { ReactNode } from "react";
import { Link } from "react-router-dom";
export function PageIntro({eyebrow,title,description,icon,accent="violet",children}:{eyebrow:string;title:string;description:string;icon:string;accent?:string;children?:ReactNode}) {
 return <motion.section className={`page-intro accent-${accent}`} initial={{opacity:0,y:10}} animate={{opacity:1,y:0}} transition={{duration:.3}}><div className="intro-copy"><span className="intro-eyebrow">{eyebrow}</span><h2>{title}</h2><p>{description}</p>{children&&<div className="intro-chips">{children}</div>}</div><div className="intro-art" aria-hidden="true"><span>{icon}</span><i/><i/></div></motion.section>;
}
export function Metric({label,value}:{label:string;value:ReactNode}) {return <div className="intro-metric"><small>{label}</small><b>{value}</b></div>;}
export function EmptyState({icon="↳",title,body,to,label}:{icon?:string;title:string;body:string;to?:string;label?:string}) {return <div className="honest-empty"><span aria-hidden="true">{icon}</span><h3>{title}</h3><p>{body}</p>{to&&<Link to={to}>{label||"Open discussion room"} ↗</Link>}</div>;}
