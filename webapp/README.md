# Pale Blue Flame: web app (v0.1)

Vue 3 + Vite. Reads only our own files in `../data` (copied into `public/data` on `dev` and `build`), never NASA's API.

```sh
cd webapp
npm install
npm run dev      # http://localhost:5173
npm run build    # static site in dist/
```

Screens: Home (prevent / detect / suppress), **Will it burn here?** (place + material, gap map, honest answer, nearest tests),
and one card per experiment (`#/experiment/PSI-25`).

Not done yet: "what they found" summaries per experiment; oxygen and airflow for BASS (its table has none).

## The question box (AI)

Visitors type a question ("would my nike shoe burn on the Moon?"). The backend in `../backend` (FastAPI + LangGraph,
DeepSeek) picks the closest materials NASA tested and the place, looks the answer up in `../data`, and words it in
two or three sentences using only those facts. The API key lives in the backend only.

```sh
../backend/run.sh   # backend on :8787 (reads DEEPSEEK_API_KEY)
npm run dev         # site on :5173, /api is passed to the backend
```

Without the backend or internet, the box says so and the carousel keeps working.
