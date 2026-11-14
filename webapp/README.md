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
