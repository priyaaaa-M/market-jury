"""Local, extractive answers. No LLM call, network request or user prompt storage.
Debate arguments are quoted as model opinions, never upgraded into market facts.
"""
import re

ROLE_LABELS = {"debater_bull": "Bull case", "debater_bear": "Bear case",
               "risk_reviewer": "Risk review", "final_judge": "Final judge"}


def answer(store, question: str, symbol: str) -> dict:
    symbol = symbol.upper().strip()
    if not re.fullmatch(r"[A-Z0-9&-]{1,30}", symbol):
        raise ValueError("Choose a valid NSE symbol")
    from .data import DEFAULT_UNIVERSE
    mentioned = [s for s in DEFAULT_UNIVERSE if re.search(r"\b" + re.escape(s) + r"\b", question, re.I)]
    if any(s != symbol for s in mentioned):
        return {"status": "symbol_mismatch", "symbol": symbol,
                "answer": "Your question names a different stock. Change the stock selector to match it, then ask again. I won't silently answer about the wrong company.",
                "sources": [], "cost_usd": 0}
    records = store.verdicts(symbol, limit=1)
    if not records:
        return {"status": "no_evidence", "symbol": symbol,
                "answer": f"No completed debate is saved for {symbol}. I cannot explain a verdict that does not exist. Start a discussion first.",
                "sources": [], "cost_usd": 0}
    v = records[0]
    q = question.lower()
    roles = []
    if any(w in q for w in ("bear", "downside", "challenger")): roles.append("debater_bear")
    if any(w in q for w in ("bull", "upside", "optimist")): roles.append("debater_bull")
    if any(w in q for w in ("risk", "missing", "guardian")): roles.append("risk_reviewer")
    if not roles and any(w in q for w in ("why", "hold", "judge", "decision", "verdict")): roles = ["final_judge"]
    if not roles and any(w in q for w in ("summary", "summar", "discuss", "said")): roles = list(ROLE_LABELS)
    if not roles:
        return {"status": "unsupported", "symbol": symbol, "answer": "I can show the saved verdict, why the judge decided, the bull case, bear case, risk review or full discussion. I do not invent news, predict future prices, give personalised advice or start tasks from chat.", "sources": [], "cost_usd": 0}
    sources = []
    for p in v.get("positions", []):
        if p.get("agent_name") in roles:
            sources.append({"role": ROLE_LABELS[p["agent_name"]], "quote": p.get("argument", ""),
                "evidence": p.get("evidence", []), "model": p.get("receipt", {}).get("actual_model") or p.get("model") or "not recorded",
                "round": p.get("round", 0) + 1})
    # Old two-role verdicts used a deterministic judge. Don't invent an AI turn.
    if not sources and roles == ["final_judge"]:
        sources = [{"role": "Stored decision reasoning", "quote": v.get("reasoning", "Not recorded"),
                    "model": v.get("audit", {}).get("model", "not recorded"), "round": None}]
    if not sources:
        return {"status": "no_role_evidence", "symbol": symbol,
                "answer": "The saved debate does not contain that role's argument. I won't invent a missing turn.",
                "sources": [], "cost_usd": 0}
    return {"status": "grounded", "symbol": symbol,
            "answer": f"The latest saved verdict for {symbol} is {v['verdict'].upper()} with {round(v['confidence']*100)}% model confidence (not a calibrated probability). These are exact saved model arguments, not verified market facts. The engine's final decision may include a hard confidence/regime gate.",
            "verdict": v["verdict"], "timestamp": v["timestamp"], "verdict_id": v.get("id"),
            "data_source": v.get("audit", {}).get("data_source", "unknown"), "sources": sources,
            "cost_usd": 0, "note": "Local evidence lookup only. No chat text is sent to a model or saved on the server."}
