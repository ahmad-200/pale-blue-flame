"""Pale Blue Flame backend: one LangGraph that answers "would X burn in Y?" from NASA's data.

    interpret (LLM) -> lookup (our data, no LLM) -> explain (LLM, only the looked-up facts)

The model only translates the question and words the answer; every number comes from ../data.
Run:  DEEPSEEK_API_KEY=... uv run uvicorn app:app --port 8787
"""
import csv, json, os
from pathlib import Path
from typing import TypedDict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from pydantic import BaseModel

DATA = Path(__file__).resolve().parent.parent / "data"
PLACES = {p["id"]: p for p in json.loads((DATA / "places.json").read_text())["places"]}
EXPERIMENTS = {e["name"]: e for e in json.loads((DATA / "experiments.json").read_text())["experiments"] if e["name"]}
TESTS = [r for r in csv.DictReader((DATA / "material_tests.csv").open())]
MATERIALS = {
    "SIBAL (cotton-fiberglass)": "cotton fabric on fiberglass: cloth, clothes, fabric",
    "PMMA (acrylic)": "clear hard plastic: plastic parts, cases, windows",
    "Nomex": "flame-resistant fabric: firefighter and flight suits",
    "silicone": "rubbery: rubber, foam soles, seals, cables",
    "candle wax": "wax, candles",
    "Ultem": "tough amber engineering plastic",
}

llm = ChatOpenAI(model="deepseek-chat", base_url="https://api.deepseek.com", temperature=0,
                 api_key=os.environ.get("DEEPSEEK_API_KEY", "missing"))


class State(TypedDict, total=False):
    question: str
    object: str
    made_of: str
    candidates: list   # [{material, why}] closest NASA-tested materials
    place: str
    facts: dict
    answer: str
    error: str


def ask_json(system: str, user: str) -> dict:
    out = llm.invoke([("system", system), ("user", user)], response_format={"type": "json_object"})
    return json.loads(out.content)


def interpret(s: State) -> State:
    """LLM: the object, what it is made of, the closest materials NASA tested, and the place."""
    try:
        out = ask_json(
            "Map a question about fire in space onto lists. JSON only: "
            '{"object": str, "made_of": str, "candidates": [{"material": key, "why": str}], "place": key or null}. '
            "candidates: 1-3 closest materials from MATERIALS by what the object is made of, closest first; "
            "empty only for metals, liquids, gases, food. Never invent keys. Mars habitat -> moon.\n"
            f"MATERIALS: {json.dumps(MATERIALS)}\nPLACES: {json.dumps({k: v['name'] for k, v in PLACES.items()})}",
            s["question"])
    except Exception as e:  # a provider outage degrades, it does not crash
        return {"error": f"The AI could not read the question ({type(e).__name__})."}
    cands = [c for c in out.get("candidates", []) if c.get("material") in MATERIALS][:3]
    plottable = {t["material"] for t in TESTS if t["oxygen_pct"]}
    cands.sort(key=lambda c: c["material"] not in plottable)   # stable: keeps the AI's order among plottable ones
    return {"object": str(out.get("object", ""))[:60], "made_of": str(out.get("made_of", ""))[:120],
            "candidates": cands, "place": out.get("place") if out.get("place") in PLACES else None}


def lookup(s: State) -> State:
    """No LLM: what NASA's data says for the first candidate in this place."""
    if s.get("error") or not s.get("candidates") or not s.get("place"):
        return {"facts": {}}
    mat, place = s["candidates"][0]["material"], PLACES[s["place"]]
    fires = [t for t in TESTS if t["material"] == mat and t["oxygen_pct"]]
    o2 = sorted(float(t["oxygen_pct"]) for t in fires)
    tested = bool(o2) and abs(place["pressure_atm"] - 1) <= 0.1 and o2[0] - 1 <= place["oxygen_pct"] <= o2[-1] + 1
    closest = min(fires, key=lambda t: abs(float(t["oxygen_pct"]) - place["oxygen_pct"]), default=None)
    exps = sorted({t["experiment"] for t in TESTS if t["material"] == mat})
    return {"facts": {
        "material": mat, "place": place["name"], "place_oxygen_pct": place["oxygen_pct"], "place_pressure_atm": place["pressure_atm"],
        "fires_with_oxygen_recorded": len(o2), "tested_oxygen_range": [o2[0], o2[-1]] if o2 else None,
        "tested_pressure_atm": 1.0, "tested_in_this_air": tested,
        "closest_fire": closest and {"experiment": closest["experiment"], "test": closest["test"], "oxygen_pct": float(closest["oxygen_pct"])},
        "experiments": exps,
        "papers": [p["title"] for e in exps for p in EXPERIMENTS.get(e, {}).get("papers", [])][:5],
    }}


def explain(s: State) -> State:
    """LLM: two or three plain sentences, using only the facts."""
    if s.get("error"):
        return {}
    if not s.get("facts"):
        return {"answer": f"NASA's fire tests have nothing comparable to {s.get('object') or 'that'}." if not s.get("candidates")
                else "Pick a place too: the Space Station, the airlock, a Moon base or a rover."}
    try:
        out = ask_json(
            'Answer in JSON {"answer": str}: two or three plain sentences for a non-expert. Use ONLY the facts given; '
            "no other numbers. Say the material is a stand-in for the object. If tested_in_this_air is false, say nobody "
            "has tested it in this air and that not tested is not the same as safe.",
            json.dumps({"object": s.get("object"), "made_of": s.get("made_of"), "facts": s["facts"]}))
        return {"answer": str(out.get("answer", ""))[:600]}
    except Exception:
        return {"answer": ""}


graph = StateGraph(State)
for name, fn in [("interpret", interpret), ("lookup", lookup), ("explain", explain)]:
    graph.add_node(name, fn)
graph.set_entry_point("interpret")
graph.add_edge("interpret", "lookup")
graph.add_edge("lookup", "explain")
graph.add_edge("explain", END)
agent = graph.compile()

app = FastAPI(title="Pale Blue Flame")
app.add_middleware(CORSMiddleware, allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
                   allow_methods=["GET", "POST"], allow_headers=["Content-Type"])


class Ask(BaseModel):
    question: str


@app.get("/api/health")
def health():
    return {"status": "ok", "materials": len(MATERIALS), "places": len(PLACES), "tests": len(TESTS)}


@app.post("/api/ask")
def ask(body: Ask):
    q = body.question.strip()[:300]
    if not q:
        return {"error": "Type a question first."}
    if not os.environ.get("DEEPSEEK_API_KEY"):
        return {"error": "The question box is not set up on this server (no API key)."}
    s = agent.invoke({"question": q})
    c = s.get("candidates") or []
    return {"error": s.get("error"), "object": s.get("object"), "made_of": s.get("made_of"), "candidates": c,
            "material": c[0]["material"] if c else None, "place": s.get("place"),
            "answer": s.get("answer"), "facts": s.get("facts")}
