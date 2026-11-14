"""Draft the "What they found" summaries for every experiment, only from NASA's own record.

Writes ../data/summaries.json. Every line carries its source (a field of NASA's record, a paper title from the
record, or our test table); lines whose source does not exist are dropped. Review before relying on it.
Run: DEEPSEEK_API_KEY=... uv run python summarize.py
"""
import csv, json, os
from pathlib import Path
from langchain_openai import ChatOpenAI

DATA = Path(__file__).resolve().parent.parent / "data"
exps = json.loads((DATA / "experiments.json").read_text())["experiments"]
tests = list(csv.DictReader((DATA / "material_tests.csv").open()))
llm = ChatOpenAI(model="deepseek-chat", base_url="https://api.deepseek.com", temperature=0,
                 api_key=os.environ["DEEPSEEK_API_KEY"])
FIELDS = ["objective", "approach", "hypothesis", "earth_benefits"]

RULES = """You summarize one NASA microgravity combustion investigation for a fire-safety dashboard, for engineers and
students. Use ONLY the record given. JSON only:
{"summary": [{"text": str, "source": str}], "findings": [{"text": str, "source": str}], "safety": str, "earth": str}
- summary: 3-5 short plain sentences: what was studied, how, with what fuels or samples, and why it matters for
  crew fire safety. Each "source" is exactly one of: objective, approach, hypothesis, earth_benefits, our_table,
  or "paper: <exact paper title from the record>".
- findings: ONLY results the record explicitly states (a measured outcome, a conclusion). If the record states
  none, return []. Never infer results from paper titles; a title is not a finding.
- safety: one sentence on which part of fire safety it informs (prevention, detection or suppression) and why.
- earth: one sentence on uses back on Earth if earth_benefits states any, else "".
No numbers that are not in the record. No safety advice."""

def record_for(e):
    rows = [t for t in tests if t["experiment"] == e["name"]]
    o2 = sorted(float(t["oxygen_pct"]) for t in rows if t["oxygen_pct"])
    return {k: e.get(k) for k in ["id", "name", "title", "kind", "where", "start", "end", "hardware"] + FIELDS} | {
        "papers": [p["title"] for p in e["papers"][:20]],
        "our_table": {"material_tests": len(rows), "materials": sorted({t["material"] for t in rows}),
                      "oxygen_range_pct": [o2[0], o2[-1]] if o2 else None} if rows else None}

def valid(item, rec):
    src = str(item.get("source", ""))
    if src in FIELDS:
        return bool(rec.get(src))
    if src == "our_table":
        return bool(rec.get("our_table"))
    if src.startswith("paper:"):
        return src[6:].strip() in rec["papers"]
    return False

out = {}
for e in exps:
    rec = record_for(e)
    try:
        msg = llm.invoke([("system", RULES), ("user", json.dumps(rec))], response_format={"type": "json_object"})
        d = json.loads(msg.content)
    except Exception as x:
        print("FAILED", e["id"], type(x).__name__); continue
    keep = lambda xs: [{"text": str(i["text"])[:300], "source": i["source"]} for i in xs or [] if isinstance(i, dict) and valid(i, rec)]
    out[e["id"]] = {"summary": keep(d.get("summary")), "findings": keep(d.get("findings")),
                    "safety": str(d.get("safety", ""))[:300], "earth": str(d.get("earth", ""))[:300]}
    dropped = len(d.get("summary") or []) + len(d.get("findings") or []) - len(out[e["id"]]["summary"]) - len(out[e["id"]]["findings"])
    print(e["id"], e["name"], "summary", len(out[e["id"]]["summary"]), "findings", len(out[e["id"]]["findings"]), "dropped", dropped)

(DATA / "summaries.json").write_text(json.dumps({
    "meta": {"what": "AI-drafted summaries of NASA's PSI records (deepseek-chat). Every line names its source in the record; "
                     "lines with a source that does not exist were dropped. Findings appear only where the record states a result.",
             "made": "2026-11-15"}, "summaries": out}, indent=1, ensure_ascii=False))
print("wrote", len(out))
