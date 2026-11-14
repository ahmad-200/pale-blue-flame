// Copies ../data into public/data so the site reads our own files, never NASA's slow API.
// material_tests.csv becomes material_tests.json (numbers as numbers, blanks as null).
import { readFileSync, writeFileSync, mkdirSync, copyFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const here = dirname(fileURLToPath(import.meta.url))
const src = join(here, '..', '..', 'data')
const out = join(here, '..', 'public', 'data')
mkdirSync(out, { recursive: true })

for (const f of ['experiments.json', 'places.json']) copyFileSync(join(src, f), join(out, f))

function parseCsv(text) {
  const rows = []; let row = [], cell = '', quoted = false
  for (let i = 0; i < text.length; i++) {
    const c = text[i]
    if (quoted) {
      if (c === '"' && text[i + 1] === '"') { cell += '"'; i++ }
      else if (c === '"') quoted = false
      else cell += c
    } else if (c === '"') quoted = true
    else if (c === ',') { row.push(cell); cell = '' }
    else if (c === '\n') { row.push(cell); rows.push(row); row = []; cell = '' }
    else if (c !== '\r') cell += c
  }
  if (cell || row.length) { row.push(cell); rows.push(row) }
  return rows
}

const [header, ...body] = parseCsv(readFileSync(join(src, 'material_tests.csv'), 'utf8'))
const value = v => v === '' ? null : v.includes('?-g ') ? value(v.replaceAll('?-g ', 'microgravity ')) : v === 'True' ? true : v === 'False' ? false
  : /^-?\d+(\.\d+)?$/.test(v) ? Number(v) : v
const tests = body.filter(r => r.length === header.length)
  .map(r => Object.fromEntries(header.map((h, i) => [h, value(r[i])])))
writeFileSync(join(out, 'material_tests.json'), JSON.stringify(tests))
console.log(`sync-data: ${tests.length} material tests, experiments.json, places.json -> public/data`)
