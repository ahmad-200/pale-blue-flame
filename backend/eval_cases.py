"""Run everyday questions through the live backend and check the first material. Usage: uv run python eval_cases.py"""
import json, sys, urllib.request

CASES = [  # question, expected first material (None = nothing comparable), expected place
    ("would my nvidia gpu burn in space", "PMMA (acrylic)", "iss"),
    ("would my laptop burn on the station", "PMMA (acrylic)", "iss"),
    ("would my phone case burn on the moon", "PMMA (acrylic)", "moon"),
    ("would my keyboard burn in a moon rover", "PMMA (acrylic)", "rover"),
    # a running shoe's outside is mostly mesh fabric, with a rubber and foam sole: either stand-in can lead
    ("would my running shoe burn in a moon rover", ("SIBAL (cotton-fiberglass)", "silicone"), "rover"),
    ("would my cotton shirt burn on the moon", "SIBAL (cotton-fiberglass)", "moon"),
    ("would a towel burn on the space station", "SIBAL (cotton-fiberglass)", "iss"),
    ("would a firefighter suit burn in the airlock", "Nomex", "airlock"),
    ("would a candle burn on a mars base", "candle wax", "moon"),
    ("would a rubber seal burn in the rover", "silicone", "rover"),
    ("would a usb cable burn on the moon", "silicone", "moon"),
    ("would plexiglass burn on the ISS", "PMMA (acrylic)", "iss"),
    ("would an aluminium spoon burn on the station", None, "iss"),
    ("would water burn on the moon", None, "moon"),
]
ok = 0
for q, want, place in CASES:
    req = urllib.request.Request("http://localhost:8787/api/ask", json.dumps({"question": q}).encode(),
                                 {"Content-Type": "application/json"})
    d = json.load(urllib.request.urlopen(req, timeout=120))
    got = d.get("material")
    good = (got in want if isinstance(want, tuple) else got == want) and d.get("place") == place
    ok += good
    print(("PASS" if good else "FAIL"), f"{q!r}: {got} @ {d.get('place')}  (parts: {d.get('made_of')})")
print(f"{ok}/{len(CASES)} passed")
sys.exit(0 if ok == len(CASES) else 1)
