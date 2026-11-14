# Pale Blue Flame

*Nobody has lit a fire there yet.*

NASA has spent years setting small, careful fires in space, and every material it burned was burned in Space Station air. The places people want to live next, a base on the Moon, a pressurized rover, a habitat on Mars, are planned with more oxygen and thinner air. In that air, NASA's fire data has nothing. This project makes that gap visible, and lets you ask about the things you would actually take with you.

We built it for the NASA Space Apps Challenge 2026, for the challenge [Flame in Freefall](https://www.spaceappschallenge.org/2026/challenges/flame-in-freefall/): an SI-powered dashboard that summarizes, ranks and interprets NASA's microgravity combustion research for fire safety.

## The one question

**Would this burn here?** You pick a material and a place, or type a question in your own words ("would my running shoe burn in a Moon rover?"), and the page answers in one of two ways:

- **NASA tested this.** There are real fires with that material in air like that place's. Tested is not the same as safe: what happened in each is on its experiment page.
- **We don't know. No matching test.** NASA tested the material, but only in different air. Not tested here does not mean safe.

It sounds like a small answer. It is actually the finding. Every material fire in the database we used ran at about 1 atm and 14 to 22% oxygen. NASA's proposed exploration atmosphere for Moon and Mars habitats is 34% oxygen at 0.56 atm. One NASA investigation, ACME BRE, reports in its own record that burning continued without airflow in elevated-oxygen air like that, while in normal 21% air the flames went out.

## What is in this repository

| Folder | What it holds |
|---|---|
| `notebooks/01_explore_the_data.ipynb` | What NASA's fire data looks like: 24 investigations, their test tables, papers and raw files. Start here. |
| `notebooks/02_clean_the_data.ipynb` | How the messy test tables became one clean table of 263 material tests. |
| `data/` | Everything the site reads: `material_tests.csv` (the clean table), `experiments.json` (the 24 investigations), `places.json` (the air in each place, with NASA sources), `summaries.json` (sourced summaries) and `saffire1_sensors.json` (a real fire's sensor log). |
| `webapp/` | The website (Vue 3, Vite, SVG and D3). |
| `backend/` | The question box (FastAPI and LangGraph, with DeepSeek). |

## Run it on your machine

You need Node 18 or newer. The question box also needs Python 3.11+, [uv](https://docs.astral.sh/uv/) and a DeepSeek API key.

```sh
cd webapp
npm install
npm run dev                 # http://localhost:5173
```

That is the whole site, and it works offline. For the question box, start the backend in a second terminal:

```sh
cd backend
export DEEPSEEK_API_KEY=your-key
uv run uvicorn app:app --port 8787
```

The site passes `/api` to it. **The key stays in the backend and never goes into the website.** Without the backend, the question box says so and everything else keeps working.

For a screen at a stand, open `http://localhost:5173/?stand=1#/burn` in full screen: one 16:9 view, no menus, a new example every six seconds.

## How the AI is kept honest

The AI only does what it is good at: understanding what an everyday object is made of. It describes the parts ("a GPU: a plastic shroud, a circuit board, a metal heatsink"), and a fixed table in our code picks the closest material NASA actually tested. The verdict, every number and every chart come from NASA's data, never from the model. When nothing in the data is comparable (a metal spoon, water), the page says so instead of guessing.

The experiment summaries were drafted by AI from each investigation's NASA record. Every line names the part of the record it comes from, lines without a real source were removed, and "what they found" appears only where NASA's record states a result. Please read them before quoting them.

`backend/eval_cases.py` runs fourteen everyday questions through the backend and checks the answers. Run it after any change to the AI.

## Where the data comes from

NASA's [Physical Sciences Informatics](https://psi.nasa.gov/physci/repo/search?q=combustion) database, Combustion Science (23 of the 24 records are CC0-1.0). The place atmospheres come from NASA technical reports linked in `data/places.json`. The background is a tribute to Voyager 1's Pale Blue Dot, drawn in code, not a star map.

A few things to keep in mind:

- NASA's tables don't record pressure for the material tests; we assume cabin pressure (about 1 atm) and mark it in the data.
- "No matching test" means no match in the data we used, not in every fire test ever run.
- The Moon, rover and Mars atmospheres are proposed designs. Real missions may differ.

We hope it makes one thing hard to miss: we know a great deal about fire in one kind of air, and almost nothing about the air we are about to live in.
