import { readFileSync, readdirSync, statSync, existsSync } from 'fs';
import { join, dirname, resolve } from 'path';

const ROOT = process.argv[2];
const files = [];
(function walk(d) {
  for (const e of readdirSync(d)) {
    const p = join(d, e);
    statSync(p).isDirectory() ? walk(p) : /\.jsx?$/.test(p) && files.push(p);
  }
})(ROOT);

const exportsOf = (f) => {
  const src = readFileSync(f, 'utf8');
  const names = new Set();
  for (const m of src.matchAll(/export\s+(?:async\s+)?(?:function|const|let|class)\s+([A-Za-z0-9_$]+)/g)) names.add(m[1]);
  for (const m of src.matchAll(/export\s*\{([^}]*)\}/g))
    m[1].split(',').forEach((p) => { const n = p.split(/\s+as\s+/).pop().trim(); if (n) names.add(n); });
  if (/export\s+default/.test(src)) names.add('default');
  return names;
};

const resolveSpec = (from, spec) => {
  if (!spec.startsWith('.')) return null;
  const base = resolve(dirname(from), spec);
  for (const c of [base, base + '.js', base + '.jsx', join(base, 'index.js'), join(base, 'index.jsx')])
    if (existsSync(c) && statSync(c).isFile()) return c;
  return false;
};

let bad = 0;
for (const f of files) {
  const src = readFileSync(f, 'utf8');
  for (const m of src.matchAll(/import\s+([^;]*?)\s+from\s+['"]([^'"]+)['"]/gs)) {
    const [, clause, spec] = m;
    const target = resolveSpec(f, spec);
    if (target === null) continue;
    if (target === false) { console.log(`MISSING MODULE ${f}: ${spec}`); bad++; continue; }
    const avail = exportsOf(target);
    const braces = clause.match(/\{([^}]*)\}/);
    const named = braces ? braces[1].split(',').map((p) => p.split(/\s+as\s+/)[0].trim()).filter(Boolean) : [];
    const def = clause.replace(/\{[^}]*\}/, '').replace(/,/g, '').trim();
    if (def && !avail.has('default')) { console.log(`NO DEFAULT ${f}: ${def} from ${spec}`); bad++; }
    for (const n of named)
      if (!avail.has(n)) { console.log(`NO EXPORT  ${f}: ${n} from ${spec}`); bad++; }
  }
}
console.log(bad ? `\n${bad} problem(s)` : `\nclean — ${files.length} files`);
