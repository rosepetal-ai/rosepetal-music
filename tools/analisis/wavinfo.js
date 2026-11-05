// Lee WAV (PCM 16/24/32 o float32) y muestra formato, duración, pico, envolvente en 8 tramos y croma (clases de nota) por
// ventanas, más las tres notas graves más fuertes: sirve para saber en qué nota está un sample antes de afinarlo con speed.
// Uso: node tools/analisis/wavinfo.js <archivo.wav> [más archivos…]
const fs = require('fs');
function load(f) {
  const b = fs.readFileSync(f); let o = 12, fmt, ch, sr, bits, d;
  while (o < b.length - 8) { const id = b.toString('ascii', o, o + 4), sz = b.readUInt32LE(o + 4);
    if (id === 'fmt ') { fmt = b.readUInt16LE(o + 8); ch = b.readUInt16LE(o + 10); sr = b.readUInt32LE(o + 12); bits = b.readUInt16LE(o + 22);
      if (fmt === 0xFFFE) fmt = b.readUInt16LE(o + 32); }
    if (id === 'data') { d = b.subarray(o + 8, Math.min(b.length, o + 8 + sz)); break; }
    o += 8 + sz + (sz & 1); }
  const bps = bits / 8, n = Math.floor(d.length / bps / ch), x = new Float32Array(n);
  const rd = fmt === 3 ? (i => d.readFloatLE(i)) : bits === 16 ? (i => d.readInt16LE(i) / 32768) : bits === 24 ? (i => d.readIntLE(i, 3) / 8388608) : (i => d.readInt32LE(i) / 2147483648);
  let peak = 0;
  for (let i = 0; i < n; i++) { let s = 0; for (let c = 0; c < ch; c++) { const v = rd((i * ch + c) * bps); s += v; if (Math.abs(v) > peak) peak = Math.abs(v); } x[i] = s / ch; }
  return { x, sr, ch, bits, fmt, peak };
}
const names = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B'];
function goertzel(x, sr, f, a, b) { const k = 2 * Math.cos(2 * Math.PI * f / sr); let s1 = 0, s2 = 0; for (let i = a; i < b; i++) { const s = x[i] + k * s1 - s2; s2 = s1; s1 = s; } return s1 * s1 + s2 * s2 - k * s1 * s2; }
for (const f of process.argv.slice(2)) {
  const { x, sr, ch, bits, fmt, peak } = load(f), dur = x.length / sr;
  // envolvente RMS en 8 tramos
  const env = []; for (let k = 0; k < 8; k++) { const a = Math.floor(k * x.length / 8), b = Math.floor((k + 1) * x.length / 8); let s = 0; for (let i = a; i < b; i++) s += x[i] * x[i]; env.push((20 * Math.log10(Math.sqrt(s / (b - a)) + 1e-9)).toFixed(0)); }
  // croma: 6 ventanas de 1 s repartidas, notas MIDI 28..88
  const chroma = new Array(12).fill(0), low = {}; const W = sr;
  for (let k = 1; k <= 6; k++) { const a = Math.floor(k * (x.length - W) / 7); for (let m = 28; m <= 88; m++) { const e = goertzel(x, sr, 440 * 2 ** ((m - 69) / 12), a, a + W); chroma[m % 12] += e; if (m < 52) low[m] = (low[m] || 0) + e; } }
  const mx = Math.max(...chroma); const top = chroma.map((e, i) => [names[i], e / mx]).sort((p, q) => q[1] - p[1]).slice(0, 5).map(([n, e]) => n + ':' + e.toFixed(2)).join(' ');
  const lowTop = Object.entries(low).sort((p, q) => q[1] - p[1]).slice(0, 3).map(([m]) => names[m % 12] + (Math.floor(m / 12) - 1)).join(' ');
  console.log(`${f.split(/[\/]/).slice(-2).join('/')}\n  ${dur.toFixed(1)}s ${sr}Hz ${bits}bit ${ch}ch fmt${fmt} pico ${(20 * Math.log10(peak)).toFixed(1)}dB | env ${env.join(' ')} | croma ${top} | graves ${lowTop}`);
}
