import { readFileSync, readdirSync, statSync } from 'fs';
import { join } from 'path';

const ROOT = process.argv[2];
const files = [];
(function walk(d) {
  for (const e of readdirSync(d)) {
    const p = join(d, e);
    statSync(p).isDirectory() ? walk(p) : /\.jsx?$/.test(p) && files.push(p);
  }
})(ROOT);

const apiNames = new Set();
for (const f of files.filter((f) => f.includes('/api/'))) {
  const src = readFileSync(f, 'utf8');
  for (const m of src.matchAll(/export\s+(?:async\s+)?(?:function|const|let|class)\s+([A-Za-z0-9_$]+)/g))
    apiNames.add(m[1]);
}

let bad = 0;
for (const f of files) {
  if (f.includes('/api/')) continue;
  const src = readFileSync(f, 'utf8');

  const imported = new Set();
  for (const m of src.matchAll(/import\s+([^;]*?)\s+from\s+['"][^'"]+['"]/gs)) {
    const clause = m[1];
    const braces = clause.match(/\{([^}]*)\}/);
    if (braces)
      braces[1].split(',').forEach((p) => {
        const name = p.split(/\s+as\s+/).pop().trim();
        if (name) imported.add(name);
      });
    const def = clause.replace(/\{[^}]*\}/, '').replace(/,/g, '').trim();
    if (def) imported.add(def);
  }

  const body = src.replace(/import\s+[^;]*?\s+from\s+['"][^'"]+['"];?/gs, '');
  const locallyDefined = new Set();
  for (const m of body.matchAll(/(?:function|const|let|var|class)\s+([A-Za-z0-9_$]+)/g))
    locallyDefined.add(m[1]);

  for (const name of apiNames) {
    if (imported.has(name) || locallyDefined.has(name)) continue;

    if (new RegExp(`(?<![.\\w])${name}\\s*\\(`).test(body)) {
      console.log(`NOT IMPORTED  ${f}: ${name}()`);
      bad++;
    }
  }
}
console.log(bad ? `\n${bad} problem(s)` : `\nclean — checked ${apiNames.size} API names across ${files.length} files`);
process.exit(bad ? 1 : 0);
