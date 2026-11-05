// Métricas de «rareza» y espectrogramas de todos los WAV de una carpeta (y subcarpetas), para elegir samples de un pack.
// Uso: node tools/analisis/metricas-sonidos.js <carpeta> <salida.png>
// Por archivo: ruido (planitud espectral: 0 tonal, 1 ruido), brillo (centroide), cambio (flujo espectral: granular o con
// glitches si es alto), vaivén (σ del volumen), tono (peso de la clase de nota dominante / de las tres primeras), deriva
// (σ de la nota más fuerte en semitonos: barridos si es alta) y las tres notas más presentes. El PNG pone los espectrogramas
// en 4 columnas, en el orden de la lista. Con esto se eligieron los 8 sonidos limpios de Dronny Darko de la pieza 10.
const fs = require('fs'), path = require('path'), zlib = require('zlib');
function load(f) {
  const b = fs.readFileSync(f); let o = 12, ch, sr, bits, d;
  while (o < b.length - 8) { const id = b.toString('ascii', o, o + 4), sz = b.readUInt32LE(o + 4);
    if (id === 'fmt ') { ch = b.readUInt16LE(o + 10); sr = b.readUInt32LE(o + 12); bits = b.readUInt16LE(o + 22); }
    if (id === 'data') { d = b.subarray(o + 8, Math.min(b.length, o + 8 + sz)); break; } o += 8 + sz + (sz & 1); }
  const bps = bits / 8, n = Math.floor(d.length / bps / ch), x = new Float32Array(n);
  for (let i = 0; i < n; i++) { let s = 0; for (let c = 0; c < ch; c++) s += bps === 3 ? d.readIntLE((i * ch + c) * 3, 3) / 8388608 : d.readInt16LE((i * ch + c) * 2) / 32768; x[i] = s / ch; }
  return { x, sr };
}
function fft(re, im) { const n = re.length;
  for (let i = 1, j = 0; i < n; i++) { let bit = n >> 1; for (; j & bit; bit >>= 1) j ^= bit; j ^= bit; if (i < j) { [re[i], re[j]] = [re[j], re[i]]; [im[i], im[j]] = [im[j], im[i]]; } }
  for (let len = 2; len <= n; len <<= 1) { const a = -2 * Math.PI / len, wr = Math.cos(a), wi = Math.sin(a);
    for (let i = 0; i < n; i += len) { let cr = 1, ci = 0; for (let k = 0; k < len / 2; k++) { const ur = re[i + k], ui = im[i + k], vr = re[i + k + len / 2] * cr - im[i + k + len / 2] * ci, vi = re[i + k + len / 2] * ci + im[i + k + len / 2] * cr;
      re[i + k] = ur + vr; im[i + k] = ui + vi; re[i + k + len / 2] = ur - vr; im[i + k + len / 2] = ui - vi; const t = cr * wr - ci * wi; ci = cr * wi + ci * wr; cr = t; } } } }
const N = 4096, W = 240, H = 90, COLS = 4;
const [dir, png] = process.argv.slice(2);
const files = []; (function walk(d) { for (const e of fs.readdirSync(d, { withFileTypes: true })) { const p = path.join(d, e.name); if (e.isDirectory()) walk(p); else if (/\.wav$/i.test(e.name)) files.push(p); } })(dir);
files.sort();
const tiles = [];
files.forEach((f, idx) => {
  const { x, sr } = load(f), frames = Math.floor((x.length - N) / N); const step = Math.max(1, Math.floor(frames / 400));
  const win = new Float32Array(N).map((_, i) => 0.5 - 0.5 * Math.cos(2 * Math.PI * i / N));
  let flat = 0, cent = 0, flux = 0, cnt = 0, prev = null; const rms = [], chroma = new Array(12).fill(0), peaks = [], cols = [];
  for (let fr = 0; fr < frames; fr += step) {
    const re = new Float64Array(N), im = new Float64Array(N); let e = 0;
    for (let i = 0; i < N; i++) { const v = x[fr * N + i]; re[i] = v * win[i]; e += v * v; }
    rms.push(10 * Math.log10(e / N + 1e-12)); fft(re, im);
    const mag = new Float64Array(N / 2); for (let k = 1; k < N / 2; k++) mag[k] = re[k] * re[k] + im[k] * im[k];
    const k0 = Math.round(100 * N / sr), k1 = Math.round(10000 * N / sr); let lg = 0, ar = 0, wsum = 0, msum = 0;
    for (let k = k0; k < k1; k++) { lg += Math.log(mag[k] + 1e-20); ar += mag[k]; wsum += k * sr / N * mag[k]; msum += mag[k]; }
    if (e / N > 1e-7) { flat += Math.exp(lg / (k1 - k0)) / (ar / (k1 - k0)); cent += wsum / msum; cnt++;
      const m = Array.from(mag.slice(0, k1)).map(v => Math.sqrt(v)); const tot = m.reduce((a, b) => a + b, 0) + 1e-12;
      if (prev) { let s = 0; for (let k = 0; k < k1; k++) s += Math.abs(m[k] / tot - prev[k]); flux += s; } prev = m.map(v => v / tot);
      let best = 0, bk = 0; for (let k = Math.round(60 * N / sr); k < Math.round(2000 * N / sr); k++) { const midi = 69 + 12 * Math.log2(k * sr / N / 440); chroma[((Math.round(midi) % 12) + 12) % 12] += mag[k]; if (mag[k] > best) { best = mag[k]; bk = k; } }
      peaks.push(69 + 12 * Math.log2(bk * sr / N / 440)); }
    // columna del espectrograma (escala log 50 Hz–12 kHz)
    const col = new Float64Array(H); for (let y = 0; y < H; y++) { const fA = 50 * (240) ** (y / H), fB = 50 * (240) ** ((y + 1) / H); let s = 0, c = 0; for (let k = Math.floor(fA * N / sr); k <= Math.ceil(fB * N / sr); k++) { s += mag[k] || 0; c++; } col[H - 1 - y] = 10 * Math.log10(s / c + 1e-20); }
    cols.push(col);
  }
  const ch = chroma.reduce((a, b) => a + b, 0), top = [...chroma].sort((a, b) => b - a), names = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B'];
  const mean = rms.reduce((a, b) => a + b, 0) / rms.length, sd = Math.sqrt(rms.reduce((a, b) => a + (b - mean) ** 2, 0) / rms.length);
  const pm = peaks.reduce((a, b) => a + b, 0) / peaks.length, psd = Math.sqrt(peaks.reduce((a, b) => a + (b - pm) ** 2, 0) / peaks.length);
  const key = chroma.map((v, i) => [names[i], v / top[0]]).sort((a, b) => b[1] - a[1]).slice(0, 3).map(([n, v]) => n + v.toFixed(1)).join(' ');
  console.log(`${String(idx + 1).padStart(2)} ${path.basename(path.dirname(f)).split(' ')[0].padEnd(13)} ${path.basename(f).replace('.wav', '').padEnd(34)} ruido ${(flat / cnt).toFixed(3)} brillo ${(cent / cnt / 1000).toFixed(1)}k cambio ${(flux / Math.max(1, cnt - 1)).toFixed(2)} vaivén ${sd.toFixed(1)}dB tono ${(top[0] / ch).toFixed(2)}/${((top[0] + top[1] + top[2]) / ch).toFixed(2)} deriva ${psd.toFixed(1)}st | ${key}`);
  // escalar columnas a W
  const tile = []; const all = cols.flatMap(c => Array.from(c)); const mx = Math.max(...all), mn = mx - 70;
  for (let y = 0; y < H; y++) { const row = []; for (let xx = 0; xx < W; xx++) { const c = cols[Math.min(cols.length - 1, Math.floor(xx * cols.length / W))]; row.push(Math.max(0, Math.min(1, (c[y] - mn) / 70))); } tile.push(row); }
  tiles.push(tile);
});
// PNG
const rowsN = Math.ceil(tiles.length / COLS), PW = COLS * (W + 6), PH = rowsN * (H + 6);
const raw = Buffer.alloc((PW * 3 + 1) * PH);
const heat = v => [Math.round(255 * Math.min(1, v * 1.6)), Math.round(255 * Math.max(0, Math.min(1, v * 1.6 - 0.5))), Math.round(255 * Math.max(0, v * 2 - 1.2))];
for (let t = 0; t < tiles.length; t++) { const ox = (t % COLS) * (W + 6) + 3, oy = Math.floor(t / COLS) * (H + 6) + 3;
  for (let y = 0; y < H; y++) for (let xx = 0; xx < W; xx++) { const [r, g, b] = heat(tiles[t][y][xx]); const p = (oy + y) * (PW * 3 + 1) + 1 + (ox + xx) * 3; raw[p] = r; raw[p + 1] = g; raw[p + 2] = b; } }
for (let y = 0; y < PH; y++) raw[y * (PW * 3 + 1)] = 0;
const crcT = new Int32Array(256).map((_, n) => { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xEDB88320 ^ (c >>> 1) : c >>> 1; return c; });
const crc = b => { let c = -1; for (const v of b) c = crcT[(c ^ v) & 255] ^ (c >>> 8); return (c ^ -1) >>> 0; };
const chunk = (t, d) => { const l = Buffer.alloc(4); l.writeUInt32BE(d.length); const td = Buffer.concat([Buffer.from(t), d]); const c = Buffer.alloc(4); c.writeUInt32BE(crc(td)); return Buffer.concat([l, td, c]); };
const ihdr = Buffer.alloc(13); ihdr.writeUInt32BE(PW, 0); ihdr.writeUInt32BE(PH, 4); ihdr[8] = 8; ihdr[9] = 2;
fs.writeFileSync(png, Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), chunk('IHDR', ihdr), chunk('IDAT', zlib.deflateSync(raw)), chunk('IEND', Buffer.alloc(0))]));
console.log('PNG', png, PW + 'x' + PH, '(4 columnas, en el orden de la lista)');
