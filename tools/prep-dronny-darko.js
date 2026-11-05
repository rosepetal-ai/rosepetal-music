// Prepara las texturas de «99Sounds x Dronny Darko – Cinematic Textures» para la pieza 10 (Código pétalo).
// El pack es gratuito y libre de derechos para usar en música y vídeo, pero no se puede redistribuir, así que no está en el
// repositorio: descárgalo de 99sounds.org, descomprímelo y ejecuta
//   node tools/prep-dronny-darko.js "<carpeta descomprimida>/99Sounds x Dronny Darko Cinematic Textures" samples/Texturas/DronnyDarko
// Recorta (texturas y drones: 30 s desde el segundo indicado; golpes enteros), funde la entrada y la salida, normaliza
// (texturas a −3 dBFS, golpes a −1 dBFS) y guarda WAV de 16 bits. Escribe una línea por archivo con los SHA-256 (16 primeros)
// del original y del resultado. El servidor sirve cada archivo de samples/Texturas como un banco con su nombre (dd_…).
const fs = require('fs'), path = require('path'), crypto = require('crypto');
const [src, out] = process.argv.slice(2);
const T = { len: 30, fin: 2, fout: 5, peak: -3 };      // texturas y drones
const F = { len: 0, fin: 0, fout: 1, peak: -1 };       // golpes y efectos (enteros)
const list = [
  // Solo sonidos limpios y tonales (líneas estables en el espectrograma); se descartaron los granulares, con barridos o glitches
  ['dd_resonancia',   'Chrono-Scouts (drones)/03 Celestial Resonance.wav', 4, T],     // Re
  ['dd_hiperimpulso', 'Aetheric (synthesys)/01 Hyperdrive Engage.wav', 2, T],         // Re, muy puro
  ['dd_pulso',        'Aetheric (synthesys)/05 Dark Matter Pulse.wav', 10, T],        // Do (se sube a Re con speed 1,1225)
  ['dd_entrelazado',  'Aetheric (synthesys)/06 Quantum Entanglement.wav', 10, T],     // Do (→ Re)
  ['dd_choque',       'Nebula Essence (fx)/01 Quantum Shockwave.wav', 0, F],          // impacto tonal Do–Sol–Re (→ Re–La–Mi)
  ['dd_singularidad', 'Nebula Essence (fx)/05 Singularity Burst.wav', 0, F],          // golpe grave suave, Fa# (→ Re)
  ['dd_subida',       'Nebula Essence (fx)/10 Tachyon Surge.wav', 0, F],              // barrido de ruido (→ +1 semitono)
  ['dd_cascada',      'Aetheric (synthesys)/10 Quantum Cascade.wav', 0, F],           // crecida larga, Re# (→ Re)
];
fs.mkdirSync(out, { recursive: true });
for (const [name, rel, start, o] of list) {
  const b = fs.readFileSync(path.join(src, rel)); let p = 12, ch, sr, bits, d;
  while (p < b.length - 8) { const id = b.toString('ascii', p, p + 4), sz = b.readUInt32LE(p + 4);
    if (id === 'fmt ') { ch = b.readUInt16LE(p + 10); sr = b.readUInt32LE(p + 12); bits = b.readUInt16LE(p + 22); }
    if (id === 'data') { d = b.subarray(p + 8, Math.min(b.length, p + 8 + sz)); break; } p += 8 + sz + (sz & 1); }
  if (bits !== 24) throw new Error(rel + ': se esperaban 24 bits');
  const total = Math.floor(d.length / 3 / ch), a = Math.floor(start * sr);
  const n = o.len ? Math.min(total - a, Math.floor(o.len * sr)) : total - a;
  const x = new Float32Array(n * ch); let peak = 0;
  for (let i = 0; i < n; i++) for (let c = 0; c < ch; c++) { const v = d.readIntLE(((a + i) * ch + c) * 3, 3) / 8388608; x[i * ch + c] = v; peak = Math.max(peak, Math.abs(v)); }
  const g = 10 ** (o.peak / 20) / peak, fi = Math.floor(o.fin * sr), fo = Math.floor(o.fout * sr);
  const outB = Buffer.alloc(44 + n * ch * 2);
  outB.write('RIFF', 0); outB.writeUInt32LE(36 + n * ch * 2, 4); outB.write('WAVEfmt ', 8); outB.writeUInt32LE(16, 16);
  outB.writeUInt16LE(1, 20); outB.writeUInt16LE(ch, 22); outB.writeUInt32LE(sr, 24); outB.writeUInt32LE(sr * ch * 2, 28);
  outB.writeUInt16LE(ch * 2, 32); outB.writeUInt16LE(16, 34); outB.write('data', 36); outB.writeUInt32LE(n * ch * 2, 40);
  for (let i = 0; i < n; i++) {
    let e = g; if (fi && i < fi) e *= i / fi; if (fo && i > n - fo) e *= (n - i) / fo;
    for (let c = 0; c < ch; c++) outB.writeInt16LE(Math.max(-32768, Math.min(32767, Math.round(x[i * ch + c] * e * 32767))), 44 + (i * ch + c) * 2);
  }
  const file = path.join(out, name + '.wav'); fs.writeFileSync(file, outB);
  console.log([name, rel, start + 's', (n / sr).toFixed(1) + 's', '+' + (20 * Math.log10(g)).toFixed(1) + 'dB',
    crypto.createHash('sha256').update(b).digest('hex').slice(0, 16), crypto.createHash('sha256').update(outB).digest('hex').slice(0, 16)].join(' | '));
}
