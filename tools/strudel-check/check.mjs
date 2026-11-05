// Comprueba una pieza .strudel sin audio, con el mismo Strudel que la página (1.2.6):
//  · que se evalúa sin errores (la página no devuelve los errores cuando la pieza llega por POST /play);
//  · cuántas notas empiezan en cada compás (el Surface Go aguanta unas 55 sin cortes);
//  · que cada sonido existe: un sintetizador de Strudel o un banco del servidor (si está arrancado).
// El tempo sale del último .cpm(…) y la duración de arrange([n, …], …); se pueden forzar con --cpm y --compases.
// Uso (una vez: npm install dentro de tools/strudel-check):
//   node tools/strudel-check/check.mjs public/music/11-belleza-callada.strudel [--compases 77] [--limite 55] [--cpm 20.17]
//   [--servidor http://127.0.0.1:8091]
import * as mod from 'node:module';
import fs from 'node:fs';

// @kabelsalat/web no carga en Node: se sustituye por un módulo vacío (registerHooks desde Node 22.15; antes, hooks.mjs)
const vacio = new URL('./kabelsalat-vacio.mjs', import.meta.url).href;
if (mod.registerHooks) mod.registerHooks({ resolve: (s, c, next) => s === '@kabelsalat/web' ? { url: vacio, shortCircuit: true } : next(s, c) });
else mod.register('./hooks.mjs', import.meta.url);
const [log, warn] = [console.log, console.warn]; console.log = console.warn = () => {};   // silencia los avisos de carga de Strudel
const core = await import('@strudel/core');
const { transpiler } = await import('@strudel/transpiler');
await core.evalScope(core, import('@strudel/mini'), import('@strudel/tonal'));
[console.log, console.warn] = [log, warn];

const args = process.argv.slice(2);
const opt = name => { const i = args.indexOf('--' + name); return i >= 0 ? args[i + 1] : undefined; };
const file = args.find((a, i) => !a.startsWith('--') && !(i > 0 && args[i - 1].startsWith('--')));
if (!file) { console.error('Uso: node check.mjs <pieza.strudel> [--compases N] [--limite 55] [--cpm N] [--servidor URL]'); process.exit(2); }
const code = fs.readFileSync(file, 'utf8');
const limite = Number(opt('limite') ?? 55);

// texto entre el paréntesis que abre en «at» y el que lo cierra
const inside = (src, at) => { let d = 0; for (let i = at; i < src.length; i++) { if (src[i] === '(') d++; else if (src[i] === ')' && --d === 0) return src.slice(at + 1, i); } return null; };
const limpio = code.replace(/\/\*[\s\S]*?\*\//g, '').replace(/(^|[^:])\/\/.*$/gm, '$1');

let cpm = opt('cpm') !== undefined ? Number(opt('cpm')) : null;
if (cpm === null) {
  const k = limpio.lastIndexOf('.cpm('); const expr = k >= 0 ? inside(limpio, k + 4) : null;
  if (expr && /^[\d.\s/*+()-]+$/.test(expr)) cpm = Function(`return (${expr})`)();
}
// en Node, sin planificador, cpm(n) = fast(n / 60): un compás (un ciclo de la pieza) dura 60 / n unidades
const barLen = cpm ? 60 / cpm : 1;

let bars = opt('compases') !== undefined ? Number(opt('compases')) : null, origen = '--compases';
if (bars === null) {
  const k = limpio.indexOf('arrange('); const body = k >= 0 ? inside(limpio, k + 7) : null;
  if (body) {
    const n = [...body.replace(/"[^"]*"|'[^']*'|`[^`]*`/g, '""').matchAll(/\[\s*(\d+(?:\.\d+)?)\s*,/g)].reduce((s, m) => s + Number(m[1]), 0);
    if (n > 0) { bars = n; origen = 'arrange'; }
  }
  if (bars === null) { bars = 64; origen = 'por defecto, no hay arrange: usa --compases'; }
}

let pattern;
const counts = [], sounds = {}, porCompas = [];
try {
  ({ pattern } = await core.evaluate(code, transpiler));
  for (let b = 0; b < bars; b++) {
    const haps = pattern.queryArc(b * barLen, (b + 1) * barLen).filter(h => h.hasOnset());
    counts.push(haps.length); const aqui = {};
    for (const h of haps) { const s = h.value && typeof h.value === 'object' ? h.value.s ?? (h.value.note !== undefined ? '(note sin s)' : '?') : '?'; sounds[s] = (sounds[s] || 0) + 1; aqui[s] = (aqui[s] || 0) + 1; }
    porCompas.push(aqui);
  }
} catch (e) {
  console.error(`ERROR en ${file}: ${e.message}`);
  process.exit(1);
}

const total = counts.reduce((a, b) => a + b, 0), max = Math.max(...counts), maxBar = counts.indexOf(max);
const secs = bars * (cpm ? 60 / cpm : 0);
console.log(`OK · ${bars} compases (${origen})` + (cpm ? ` · cpm ${+cpm.toFixed(3)} = ${+(cpm * 4).toFixed(2)} BPM en 4/4 · ${Math.floor(secs / 60)}:${String(Math.round(secs % 60)).padStart(2, '0')}` : ' · sin .cpm(): 1 ciclo por compás')
  + ` · media ${(total / bars).toFixed(1)} notas/compás · máximo ${max} (compás ${maxBar})`);
console.log('notas por compás:', counts.join(' '));
console.log('por sonido:', Object.entries(sounds).sort((a, b) => b[1] - a[1]).map(([k, v]) => `${k} ${v}`).join(' · '));

let fallo = false;
const pesados = counts.map((n, b) => [b, n]).filter(([, n]) => n > limite);
if (pesados.length) {
  fallo = true;
  console.log(`⚠ ${pesados.length} compases pasan de ${limite} notas (el Surface Go puede cortar): ${pesados.map(([b, n]) => `${b}:${n}`).join(' ')}`);
  console.log(`  en el compás ${maxBar}: ` + Object.entries(porCompas[maxBar]).sort((a, b) => b[1] - a[1]).map(([k, v]) => `${k} ${v}`).join(' · '));
}

// sonidos que la página no conoce: ni sintetizadores de Strudel ni bancos del servidor
const SINTES = new Set(['sine', 'sin', 'sawtooth', 'saw', 'square', 'sqr', 'triangle', 'tri', 'white', 'pink', 'brown', 'crackle', 'supersaw', 'pulse', 'sbd', 'bytebeat', 'user',
  'zzfx', 'z_sine', 'z_sawtooth', 'z_triangle', 'z_square', 'z_tan', 'z_noise']);
const servidor = opt('servidor') ?? 'http://127.0.0.1:8091';
try {
  const { banks } = await (await fetch(servidor + '/samples/index.json', { signal: AbortSignal.timeout(2000) })).json();
  const raros = Object.keys(sounds).filter(s => s !== '?' && s !== '(note sin s)' && !SINTES.has(s) && !banks[s] && !banks[s.split(':')[0]]);
  if (raros.length) { fallo = true; console.log(`⚠ sonidos que no son sintetizadores de Strudel ni bancos de ${servidor}: ${raros.join(', ')}`); }
  else console.log(`sonidos: todos existen (${Object.keys(banks).length} bancos en ${servidor})`);
} catch { console.log(`(no compruebo los nombres de sonido: el servidor ${servidor} no responde)`); }
process.exit(fallo ? 1 : 0);
