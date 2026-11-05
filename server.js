// Reproductor de Rosepetal Music para DJ Claude: sirve la página, los samples y el relé de DJ Claude.
// Uso: node server.js [puerto] [puertoDJClaude]
// Escucha en 127.0.0.1 y en la red local (192.168.x.x); con HOST=0.0.0.0 (o una lista separada por comas) se cambia.
const http = require('node:http');
const https = require('node:https');
const net = require('node:net');
const fs = require('node:fs');
const path = require('node:path');

const PORT = Number(process.argv[2] || process.env.PORT || 8091);
const DJ_PORT = Number(process.argv[3] || process.env.DJ_PORT || 53221);
const PUBLIC = path.join(__dirname, 'public');
const MIME = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.json': 'application/json', '.strudel': 'text/plain; charset=utf-8',
  '.wav': 'audio/wav', '.aif': 'audio/aiff', '.aiff': 'audio/aiff', '.mp3': 'audio/mpeg', '.ogg': 'audio/ogg', '.flac': 'audio/flac' };
const ROUTES = { '/': 'index.html' };

// ── Samples: se escanean varias carpetas y los golpes se agrupan por tipo ──
// Por defecto solo samples/ del proyecto (los sonidos CC0 de SFXMint), para que todo lo que suena se pueda publicar.
// Se cambia con la variable SAMPLES_DIRS (rutas separadas por ";").
const os = require('node:os');
const SAMPLES_DIRS = (process.env.SAMPLES_DIRS ? process.env.SAMPLES_DIRS.split(';')
  : [path.join(__dirname, 'samples')])
  .map(d => path.resolve(d));
const AUDIO = /\.(wav|aiff?|mp3|ogg|flac)$/i;
const PER_BANK = 96;
// Palabras clave por banco (sobre el nombre del archivo y sus carpetas, troceados en palabras)
const BANKS = [
  ['kick', t => t.has('kick') || t.has('kicks') || t.has('bd') || t.has('bassdrum') || (t.has('bass') && t.has('drum'))],
  ['openhat', t => t.has('oh') || t.has('openhat') || t.has('openhats') || (t.has('open') && (t.has('hat') || t.has('hats') || t.has('hh') || t.has('hihat')))],
  ['clap', t => t.has('clap') || t.has('claps') || t.has('cp') || t.has('handclap')],
  ['snare', t => t.has('snare') || t.has('snares') || t.has('sd') || t.has('sn') || t.has('snr')],
  ['rim', t => t.has('rim') || t.has('rimshot') || t.has('rs') || t.has('sidestick')],
  ['ride', t => t.has('ride') || t.has('rides') || t.has('rd')],
  ['crash', t => t.has('crash') || t.has('crashes') || t.has('cy') || t.has('cym') || t.has('cymbal') || t.has('cymbals') || t.has('china') || t.has('splash')],
  ['hat', t => t.has('hat') || t.has('hats') || t.has('hh') || t.has('ch') || t.has('hihat') || t.has('hihats') || t.has('closedhat')],
  ['tom', t => t.has('tom') || t.has('toms') || t.has('lt') || t.has('mt') || t.has('ht')],
  ['perc', t => ['perc', 'percs', 'percussion', 'cowbell', 'cb', 'conga', 'congas', 'bongo', 'bongos', 'shaker', 'shakers', 'tamb', 'tambourine', 'clave', 'claves', 'block', 'cl'].some(w => t.has(w))],
  ['fx', t => ['fx', 'sfx', 'riser', 'risers', 'sweep', 'sweeps', 'noise', 'impact', 'impacts', 'whoosh', 'reverse', 'rev'].some(w => t.has(w))],
  ['bass', t => t.has('808') || t.has('bass') || t.has('sub')],
];
const tokens = s => new Set(s.replace(/([a-z])([A-Z])/g, '$1 $2').toLowerCase()
  .split(/[^a-z0-9]+|(?<=[a-z])(?=[0-9])|(?<=[0-9])(?=[a-z])/).filter(Boolean));
let sampleIndex = null, sampleIndexAt = 0;
function scanSamples() {
  if (sampleIndex && Date.now() - sampleIndexAt < 10000) return sampleIndex;
  const banks = {}, files = [];
  SAMPLES_DIRS.forEach((root, di) => {
    const walk = (dir, depth) => {
      let entries = [];
      try { entries = fs.readdirSync(dir, { withFileTypes: true }); } catch { return; }
      for (const e of entries) {
        const full = path.join(dir, e.name);
        if (e.isDirectory() && depth < 8) walk(full, depth + 1);
        else if (e.isFile() && AUDIO.test(e.name)) files.push([di, path.relative(root, full)]);
      }
    };
    walk(root, 0);
  });
  files.sort((x, y) => (x[0] - y[0]) || x[1].localeCompare(y[1]));
  for (const [di, rel] of files) {
    // Sonidos de SFXMint: cada archivo es su propio banco con nombre (sfx_impact_metal_hit_46…)
    if (/(^|[\\/])sfxmint([\\/]|$)/i.test(rel)) {
      const name = 'sfx_' + path.basename(rel).replace(AUDIO, '').toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '');
      banks[name] = [di + '/' + rel.split(path.sep).map(encodeURIComponent).join('/')];
      continue;
    }
    // Texturas preparadas a mano (samples/Texturas/…): cada archivo es su propio banco, con su nombre tal cual (dd_resonancia…)
    if (/(^|[\\/])texturas[\\/]/i.test(rel)) {
      const name = path.basename(rel).replace(AUDIO, '').toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '');
      banks[name] = [di + '/' + rel.split(path.sep).map(encodeURIComponent).join('/')];
      continue;
    }
    // Instrumentos afinados de VCSL: VCSL/<instrumento>/<instrumento>_<nota>.wav → banco <instrumento> con una muestra por nota
    // (en el nombre, la «s» marca el sostenido: steinway_Fs4.wav = Fa#4). Strudel elige la muestra más cercana y la transpone.
    const pitched = /(^|[\\/])vcsl[\\/]([^\\/]+)[\\/][^\\/]*_([A-G]s?-?\d)\.\w+$/i.exec(rel);
    if (pitched) {
      const bank = pitched[2].toLowerCase(), note = pitched[3].replace('s', '#');
      (banks[bank] ||= {})[note] = [di + '/' + rel.split(path.sep).map(encodeURIComponent).join('/')];
      continue;
    }
    const t = tokens(rel.replace(AUDIO, ''));
    if (t.has('loop') || t.has('loops') || t.has('bpm')) continue;          // solo golpes sueltos, sin loops
    const hit = BANKS.find(([, test]) => test(t));
    if (!hit) continue;
    const key = 'sfm_' + hit[0];
    (banks[key] ||= []);
    if (banks[key].length < PER_BANK) banks[key].push(di + '/' + rel.split(path.sep).map(encodeURIComponent).join('/'));
  }
  sampleIndex = { dirs: SAMPLES_DIRS, files: files.length, banks };
  sampleIndexAt = Date.now();
  return sampleIndex;
}

// Último latido de cada página abierta (para saber desde fuera qué escena se ve)
const clients = new Map();

function handle(req, res) {
    const url = new URL(req.url, 'http://x');
    if (url.pathname === '/config.json') {
      res.writeHead(200, { 'content-type': MIME['.json'] });
      return res.end(JSON.stringify({ djPort: DJ_PORT }));
    }
    if (url.pathname === '/hb' && req.method === 'POST') {
      let body = '';
      req.on('data', c => { body += c; if (body.length > 65536) req.destroy(); });
      req.on('end', () => {
        try {
          const hb = JSON.parse(body), now = Date.now();
          clients.set(String(hb.id), { ...hb, at: now, from: req.socket.remoteAddress });
          if (clients.size > 32) for (const [k, c] of clients) if (now - c.at > 60000) clients.delete(k);
        } catch {}
        res.writeHead(204); res.end();
      });
      return;
    }
    // Tocar una pieza en todas las páginas abiertas sin pasar por DJ Claude (solo desde este equipo):
    //   POST /play?track=03-ambient-trance.strudel   · o POST /play con el código Strudel en el cuerpo
    //   POST /hush                                    · para parar
    if ((url.pathname === '/play' || url.pathname === '/hush') && req.method === 'POST') {
      if (!isLoopback(req.socket.remoteAddress)) { res.writeHead(403); return res.end(); }
      if (url.pathname === '/hush') {
        relay.cache = null; toPages(JSON.stringify({ type: 'hush' }));
        res.writeHead(200); return res.end(`parado en ${relay.pages.size} página(s)\n`);
      }
      let body = '';
      req.on('data', c => { body += c; if (body.length > 1024 * 1024) req.destroy(); });
      req.on('end', () => {
        const track = url.searchParams.get('track');
        let code = body;
        if (track) {
          const file = path.normalize(path.join(PUBLIC, 'music', track));
          if (!file.startsWith(path.join(PUBLIC, 'music') + path.sep)) { res.writeHead(403); return res.end(); }
          try { code = fs.readFileSync(file, 'utf8'); } catch { res.writeHead(404); return res.end('pieza no encontrada\n'); }
        }
        if (!code.trim()) { res.writeHead(400); return res.end('sin código\n'); }
        const msg = { type: 'evaluate', code, id: `local-${++relay.seq}` };
        relay.cache = msg;                                       // las páginas que se conecten después también la reciben
        toPages(JSON.stringify(msg));
        res.writeHead(200); res.end(`enviado a ${relay.pages.size} página(s)\n`);
      });
      return;
    }
    // Puerto de DJ Claude a mano (solo desde este equipo), por si la búsqueda automática no lo ve
    if (url.pathname === '/dj-port' && req.method === 'POST') {
      if (!isLoopback(req.socket.remoteAddress)) { res.writeHead(403); return res.end(); }
      const p = Number(url.searchParams.get('port'));
      if (!(p > 0 && p < 65536)) { res.writeHead(400); return res.end('puerto no válido'); }
      relay.hint = p;
      (relay.open && relay.port !== p ? reregister() : connectUpstream())?.catch?.(() => {});
      res.writeHead(204); return res.end();
    }
    if (url.pathname === '/status') {
      const now = Date.now();
      const list = [...clients.values()].filter(c => now - c.at < 15000).map(c => ({ ...c, ageMs: now - c.at }));
      res.writeHead(200, { 'content-type': MIME['.json'] });
      return res.end(JSON.stringify(list, null, 2));
    }
    // Lista de piezas (public/music/*.strudel) para el selector de la página
    if (url.pathname === '/music/index.json') {
      let list = [];
      try { list = fs.readdirSync(path.join(PUBLIC, 'music')).filter(f => f.endsWith('.strudel')).sort(); } catch {}
      res.writeHead(200, { 'content-type': MIME['.json'], 'cache-control': 'no-store' });
      return res.end(JSON.stringify(list));
    }
    if (url.pathname === '/samples/index.json') {
      res.writeHead(200, { 'content-type': MIME['.json'], 'cache-control': 'no-store' });
      return res.end(JSON.stringify(scanSamples()));
    }
    if (url.pathname.startsWith('/samples/')) {
      const [di, ...rest] = url.pathname.slice('/samples/'.length).split('/');
      const root = SAMPLES_DIRS[Number(di)];
      const file = root && path.normalize(path.join(root, ...rest.map(decodeURIComponent)));
      if (!root || !file.startsWith(root + path.sep) || !AUDIO.test(file)) { res.writeHead(403); return res.end(); }
      return fs.readFile(file, (err, data) => {
        if (err) { res.writeHead(404); return res.end(); }
        res.writeHead(200, { 'content-type': MIME[path.extname(file).toLowerCase()] || 'application/octet-stream', 'cache-control': 'max-age=3600' });
        res.end(data);
      });
    }
    const rel = ROUTES[url.pathname] || url.pathname.slice(1);
    const file = path.normalize(path.join(PUBLIC, rel));
    if (!file.startsWith(PUBLIC)) { res.writeHead(403); return res.end(); }
    fs.readFile(file, (err, data) => {
      if (err) { res.writeHead(404); return res.end('No encontrado'); }
      res.writeHead(200, { 'content-type': MIME[path.extname(file)] || 'application/octet-stream', 'cache-control': 'no-store' });
      res.end(data);
    });
}

// ── Red local ──
// El mismo puerto atiende HTTP y HTTPS: el primer byte de cada conexión dice si es TLS (0x16) o HTTP.
// Desde otro equipo se redirige a HTTPS, porque el audio de Strudel (AudioWorklet: shape, crush…) solo funciona
// en un contexto seguro y http://192.168.x.x no lo es. El certificado (cert/) es local y autofirmado:
// el navegador avisará la primera vez y hay que aceptar el aviso.
const isLoopback = a => /^(127\.|::1$|::ffff:127\.)/.test(a || '');
const lanIPs = () => Object.values(os.networkInterfaces()).flat()
  .filter(a => a && a.family === 'IPv4' && !a.internal && a.address.startsWith('192.168.')).map(a => a.address);
const HOSTS = process.env.HOST ? process.env.HOST.split(',').map(h => h.trim()).filter(Boolean) : ['127.0.0.1', ...lanIPs()];
let tlsOpts = null;
try { tlsOpts = { key: fs.readFileSync(path.join(__dirname, 'cert', 'key.pem')), cert: fs.readFileSync(path.join(__dirname, 'cert', 'cert.pem')) }; } catch {}

const httpServer = http.createServer((req, res) => {
  if (tlsOpts && !isLoopback(req.socket.remoteAddress)) {
    const host = req.headers.host || `${req.socket.localAddress}:${PORT}`;
    res.writeHead(307, { location: `https://${host}${req.url}`, 'cache-control': 'no-store' });
    return res.end();
  }
  handle(req, res);
});
const httpsServer = tlsOpts ? https.createServer(tlsOpts, handle) : null;

// ── Relé de DJ Claude ──
// En modo navegador, DJ Claude abre su WebSocket en un puerto aleatorio de 127.0.0.1 y solo atiende a la última
// conexión. El servidor hace de cliente único: lo localiza solo, reparte su música a todas las páginas conectadas a
// /dj (en este equipo o desde la red local, por el mismo puerto que la web) y le devuelve una sola respuesta por cambio.
const { execFile } = require('node:child_process');
const wsLite = require('./ws-lite.js');
const relay = { up: null, port: 0, hint: 0, open: false, connecting: null, cache: null, pending: new Map(), pages: new Set(), seq: 0, idleTimer: null };
const relayStatus = () => JSON.stringify({ type: 'relay', dj: relay.open, port: relay.open ? relay.port : 0 });
const toPages = text => { for (const p of relay.pages) p.send(text); };

// ¿Hay una página de DJ Claude en ese puerto? (su HTML lleva <title>DJ Claude …)
function probeDj(port) {
  return new Promise(resolve => {
    let body = '', settled = false;
    const done = v => { if (!settled) { settled = true; resolve(v); } };
    const req = http.get({ host: '127.0.0.1', port, path: '/', timeout: 700 }, res => {
      res.setEncoding('utf8');
      res.on('data', c => { body += c; if (/<title>DJ Claude/i.test(body)) { done(true); res.destroy(); } else if (body.length > 8192) res.destroy(); });
      res.on('end', () => done(/<title>DJ Claude/i.test(body)));
      res.on('close', () => done(/<title>DJ Claude/i.test(body)));
    });
    req.on('timeout', () => { req.destroy(); done(false); });
    req.on('error', () => done(false));
  });
}
// Puertos que escuchan en 127.0.0.1 (netstat). Se reconocen por la dirección remota con puerto 0
// ("127.0.0.1:0" o "0.0.0.0:0") y no por la palabra del estado, que cambia con el idioma de Windows.
function loopbackPorts() {
  return new Promise(resolve => {
    if (process.platform !== 'win32') return resolve([]);
    execFile('netstat', ['-ano', '-p', 'TCP'], { windowsHide: true, timeout: 5000 }, (err, out) => {
      const ports = new Set();
      if (!err) for (const line of String(out).split(/\r?\n/)) {
        const m = /^\s*TCP\s+127\.0\.0\.1:(\d+)\s+\S+:0\s/i.exec(line);
        if (m) ports.add(Number(m[1]));
      }
      ports.delete(PORT);
      resolve([...ports]);
    });
  });
}
async function findDj() {
  if (relay.hint && await probeDj(relay.hint)) return relay.hint;                 // el indicado con POST /dj-port
  if (relay.port && await probeDj(relay.port)) return relay.port;                 // el último conocido
  if (DJ_PORT && DJ_PORT !== relay.port && await probeDj(DJ_PORT)) return DJ_PORT;  // el de la línea de órdenes
  const ports = await loopbackPorts();
  const hits = await Promise.all(ports.map(async p => (await probeDj(p) ? p : 0)));
  return hits.find(Boolean) || await scanForDj();
}
// Plan B: en algunos equipos netstat no ve el puerto de DJ Claude (sale una lista recortada). Entonces se prueban todos
// los puertos de 127.0.0.1 en tandas pequeñas (con muchas conexiones a la vez Windows las rechaza) y se pregunta a los
// abiertos si son DJ Claude. Tarda menos de un minuto y no se repite más de una vez cada 2 minutos.
let lastScan = 0;
function portOpen(port) {
  return new Promise(resolve => {
    const s = net.connect({ host: '127.0.0.1', port });
    s.setTimeout(250);
    s.on('connect', () => { s.destroy(); resolve(true); });
    s.on('timeout', () => { s.destroy(); resolve(false); });
    s.on('error', () => resolve(false));
  });
}
async function scanForDj() {
  if (Date.now() - lastScan < 120000) return 0;
  lastScan = Date.now();
  for (let start = 1024; start <= 65535; start += 150) {
    const batch = [];
    for (let p = start; p < Math.min(start + 150, 65536); p++) if (p !== PORT) batch.push(p);
    const open = (await Promise.all(batch.map(async p => (await portOpen(p) ? p : 0)))).filter(Boolean);
    for (const p of open) if (await probeDj(p)) { console.log(`relé: DJ Claude encontrado probando puertos (${p})`); return p; }
  }
  return 0;
}
function onUpstream(text) {
  let msg; try { msg = JSON.parse(text); } catch { return; }
  if (msg.type === 'evaluate') { relay.cache = msg; if (msg.id) relay.pending.set(msg.id, Date.now()); }
  else if (msg.type === 'hush') relay.cache = null;
  toPages(text);
}
function connectUpstream() {
  if (relay.open || relay.connecting || !relay.pages.size || typeof WebSocket !== 'function') return relay.connecting;
  relay.connecting = (async () => {
    const port = await findDj();
    if (!port || !relay.pages.size) return;
    await new Promise(resolve => {
      const up = new WebSocket(`ws://127.0.0.1:${port}`);
      const timer = setTimeout(() => { try { up.close(); } catch {} resolve(); }, 4000);
      up.onopen = () => {
        clearTimeout(timer);
        relay.up = up; relay.port = port; relay.open = true;
        up.send(JSON.stringify({ type: 'ready' }));             // DJ Claude contesta reenviando lo que suena
        console.log(`relé: conectado a DJ Claude (127.0.0.1:${port}), ${relay.pages.size} página(s)`);
        toPages(relayStatus()); resolve();
      };
      up.onmessage = ev => { if (relay.up === up && typeof ev.data === 'string') onUpstream(ev.data); };
      up.onclose = () => {
        clearTimeout(timer);
        if (relay.up === up) { relay.up = null; relay.open = false; console.log('relé: DJ Claude desconectado'); toPages(relayStatus()); }
        resolve();
      };
      up.onerror = () => {};
    });
  })().finally(() => { relay.connecting = null; });
  return relay.connecting;
}
// Suelta a DJ Claude y espera a que lo note antes de volver a conectar: si una conexión vieja se cerrara después de
// abrir la nueva, DJ Claude olvidaría también la nueva.
async function disconnectUpstream() {
  const up = relay.up;
  relay.up = null; relay.open = false;
  if (!up) return;
  await new Promise(resolve => {
    const t = setTimeout(resolve, 1500);
    up.onclose = () => { clearTimeout(t); resolve(); };
    try { up.close(); } catch { clearTimeout(t); resolve(); }
  });
  await new Promise(r => setTimeout(r, 300));
}
async function reregister() {
  if (relay.connecting) await relay.connecting;
  await disconnectUpstream();
  toPages(relayStatus());
  await connectUpstream();
}
function onPage(conn, text) {
  let msg; try { msg = JSON.parse(text); } catch { return; }
  if (msg.type === 'ready') {
    conn.send(relayStatus());
    if (msg.force) { reregister(); return; }                     // botón «reconectar» de la página
    // Lo último que sonó (de DJ Claude o de POST /play) también le llega a la página que acaba de conectarse
    if (relay.cache && (relay.open || String(relay.cache.id).startsWith('local-')))
      conn.send(JSON.stringify({ type: 'evaluate', code: relay.cache.code, id: `relay-${++relay.seq}` }));
    if (!relay.open) connectUpstream();
    return;
  }
  // Una sola respuesta por cambio: la primera página que confirma (o falla) habla por todas
  if ((msg.type === 'ack' || msg.type === 'error') && msg.id && relay.pending.has(msg.id)) {
    relay.pending.delete(msg.id);
    if (relay.open) relay.up.send(text);
  }
}
function onUpgrade(req, socket, head) {
  const url = new URL(req.url, 'http://x'), origin = req.headers.origin;
  let sameOrigin = true;                                        // solo páginas servidas por este mismo servidor
  if (origin) { try { sameOrigin = new URL(origin).host === req.headers.host; } catch { sameOrigin = false; } }
  if (url.pathname !== '/dj' || !sameOrigin) { socket.end('HTTP/1.1 403 Forbidden\r\nConnection: close\r\n\r\n'); return; }
  const conn = wsLite.accept(req, socket, head, {
    onMessage: onPage,
    onClose: c => {
      relay.pages.delete(c);
      clearTimeout(relay.idleTimer);
      // sin páginas se suelta a DJ Claude: así guarda los cambios en cola en vez de esperar respuestas que no llegan
      if (!relay.pages.size) relay.idleTimer = setTimeout(() => { if (!relay.pages.size) disconnectUpstream(); }, 8000);
    },
  });
  if (!conn) return;
  relay.pages.add(conn);
  clearTimeout(relay.idleTimer);
}
// Por HTTP sin cifrar solo desde este equipo; desde la red local, por HTTPS (wss://)
httpServer.on('upgrade', (req, socket, head) => {
  if (tlsOpts && !isLoopback(req.socket.remoteAddress)) { socket.end('HTTP/1.1 403 Forbidden\r\nConnection: close\r\n\r\n'); return; }
  onUpgrade(req, socket, head);
});
httpsServer?.on('upgrade', onUpgrade);
setInterval(() => {
  if (relay.pages.size && !relay.open) connectUpstream();      // DJ Claude aún no está en modo navegador o se reinició
  const old = Date.now() - 60000;
  for (const [id, at] of relay.pending) if (at < old) relay.pending.delete(id);
}, 3000).unref();

function onConnection(sock) {
  const idle = () => sock.destroy();                 // conexiones que no llegan a enviar nada
  sock.on('error', () => {});
  sock.setTimeout(20000, idle);
  sock.once('data', buf => {
    sock.setTimeout(0, idle);
    sock.pause();
    sock.unshift(buf);
    (httpsServer && buf[0] === 0x16 ? httpsServer : httpServer).emit('connection', sock);
    process.nextTick(() => sock.resume());
  });
}
for (const host of HOSTS) {
  net.createServer(onConnection)
    .on('error', err => console.error(`No se pudo escuchar en ${host}:${PORT}: ${err.message}`))
    .listen(PORT, host, () => {
      console.log(isLoopback(host)
        ? `Rosepetal Music en http://${host}:${PORT}  (relé de DJ Claude en /dj: busca su puerto solo)`
        : `  red local: ${tlsOpts ? 'https' : 'http'}://${host}:${PORT}${tlsOpts ? '  (certificado local: acepta el aviso del navegador la primera vez)' : ''}`);
    });
}
