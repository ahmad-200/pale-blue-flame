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

# --- what the AI knows about the data: one card per material, built from our files at startup
def material_card(name: str) -> dict:
    rows = [t for t in TESTS if t["material"] == name]
    o2 = sorted(float(t["oxygen_pct"]) for t in rows if t["oxygen_pct"])
    shapes = {}
    for t in rows:
        if t["shape"]:
            shapes[t["shape"]] = shapes.get(t["shape"], 0) + 1
    exps = sorted({t["experiment"] for t in rows})
    return {
        "what": MATERIALS[name],
        "fires": len(rows),
        "fires_with_oxygen_recorded": len(o2),
        "oxygen_range_tested": [o2[0], o2[-1]] if o2 else None,
        "pressure_tested": "about 1 atm (Space Station or cargo-ship cabin air)",
        "forms_burned": shapes,
        "examples_from_nasa_tables": sorted({t["material_text"] for t in rows})[:4],
        "experiments": {e: EXPERIMENTS[e]["title"] for e in exps if e in EXPERIMENTS},
    }


CARDS = {m: material_card(m) for m in MATERIALS}

# --- the AI only says what the object is made of, in these kinds; this table (our code) picks NASA's material
KINDS = {
    "hard_plastic": "PMMA (acrylic)",          # cases, shells, keys, housings, bottles, windows
    "engineering_plastic": "Ultem",            # tough heat-resistant plastic parts, connectors
    "rubber_or_foam": "silicone",              # soles, seals, gaskets, cable insulation, foam, thermal pads
    "cloth": "SIBAL (cotton-fiberglass)",      # cotton, clothes, towels, canvas, paper-like sheets, leather-like sheets
    "flame_resistant_fabric": "Nomex",         # firefighter, flight and space suits, aramid
    "wax": "candle wax",
    "metal": None, "glass_or_ceramic": None, "circuit_board": None, "liquid": None, "food": None, "other": None,
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
    more: str
    error: str


def ask_json(system: str, user: str) -> dict:
    out = llm.invoke([("system", system), ("user", user)], response_format={"type": "json_object"})
    return json.loads(out.content)


def interpret(s: State) -> State:
    """LLM: what the object is made of (parts, kinds, shares) and the place. Our table picks the NASA materials."""
    try:
        out = ask_json(
            "You help a fire-safety app built on NASA's microgravity fire tests. The app only knows the materials below "
            "(cards built from NASA's tables) and four places. Your job is ONLY to describe what the visitor's object is "
            "made of. JSON only:\n"
            '{"object": short name, "parts": [{"part": str, "kind": one of KINDS, "share": 0-100}], "place": key or null}\n'
            "parts: the 1-4 main parts of the object, with share = rough percent of its outside surface (what would "
            "burn first). Shares add up to about 100. kind must be one of: " + ", ".join(KINDS) + ". "
            "If the visitor names one of the materials below directly, use the matching kind. Mars habitat -> moon; "
            "any spacecraft cabin or 'in space' -> iss.\n"
            f"MATERIAL CARDS: {json.dumps(CARDS)}\nPLACES: {json.dumps({k: v['name'] for k, v in PLACES.items()})}",
            s["question"])
    except Exception as e:  # a provider outage degrades, it does not crash
        return {"error": f"The AI could not read the question ({type(e).__name__})."}
    parts = [p for p in out.get("parts", []) if isinstance(p, dict) and p.get("kind") in KINDS]
    # add up the parts that map to the same NASA material, then rank by how much of the object it covers
    total, names = {}, {}
    for p in parts:
        m = KINDS[p["kind"]]
        if m:
            total[m] = total.get(m, 0) + float(p.get("share") or 0)
            names.setdefault(m, []).append(str(p.get("part", p["kind"])))
    cands = [{"material": m, "why": f"{' and '.join(names[m])} (about {int(total[m])}%)"}
             for m in sorted(total, key=lambda m: -total[m])]
    plottable = {t["material"] for t in TESTS if t["oxygen_pct"]}
    cands.sort(key=lambda c: c["material"] not in plottable)   # stable: keeps size order among plottable ones
    made_of = ", ".join(f"{p.get('part')} ({p['kind'].replace('_', ' ')})" for p in parts)
    return {"object": str(out.get("object", ""))[:60], "made_of": made_of[:160], "candidates": cands[:3],
            "place": out.get("place") if out.get("place") in PLACES else None}


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
            'Answer in JSON {"answer": str, "more": str}. answer: two or three plain sentences for a non-expert. Use ONLY '
            "the facts and the material card; no other numbers. Say the material is a stand-in for the object. If "
            "tested_in_this_air is false, say there is no matching test in this air in the NASA data used, and that not "
            "tested is not the same as safe. more: two to four sentences of general background a curious visitor would "
            "value (why these parts matter in a cabin fire, how flames behave without gravity, why more oxygen matters). "
            "It is general knowledge, not NASA test results: no invented test results or numbers, no safety advice.",
            json.dumps({"object": s.get("object"), "made_of": s.get("made_of"), "facts": s["facts"],
                        "material_card": CARDS.get(s["facts"].get("material"))}))
        return {"answer": str(out.get("answer", ""))[:600], "more": str(out.get("more", ""))[:800]}
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
            "answer": s.get("answer"), "more": s.get("more"), "facts": s.get("facts")}
