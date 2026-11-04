// WebSocket mínimo (RFC 6455) del lado servidor, sin dependencias: solo mensajes de texto y sin extensiones.
// Lo usa el relé de DJ Claude de server.js para hablar con las páginas por el mismo puerto que la web.
const crypto = require('node:crypto');

const GUID = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11';
const MAX = 8 * 1024 * 1024;                     // tamaño máximo de un mensaje (el código de una canción ocupa ~25 KB)

function frame(op, payload) {
  const len = payload.length;
  let head;
  if (len < 126) head = Buffer.from([0x80 | op, len]);
  else if (len < 65536) { head = Buffer.alloc(4); head[0] = 0x80 | op; head[1] = 126; head.writeUInt16BE(len, 2); }
  else { head = Buffer.alloc(10); head[0] = 0x80 | op; head[1] = 127; head.writeUInt32BE(0, 2); head.writeUInt32BE(len, 6); }
  return Buffer.concat([head, payload]);
}

// Acepta una petición 'upgrade' de http/https. Devuelve la conexión, o null si no es un WebSocket válido.
// handlers: { onMessage(conn, text), onClose(conn) }
function accept(req, socket, head, handlers = {}) {
  const key = req.headers['sec-websocket-key'];
  if (!key || String(req.headers.upgrade || '').toLowerCase() !== 'websocket') {
    socket.end('HTTP/1.1 400 Bad Request\r\nConnection: close\r\n\r\n');
    return null;
  }
  const acceptKey = crypto.createHash('sha1').update(key + GUID).digest('base64');
  socket.write('HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n' +
    `Sec-WebSocket-Accept: ${acceptKey}\r\n\r\n`);
  socket.setNoDelay?.(true);
  socket.setTimeout?.(0);

  let buf = head && head.length ? Buffer.from(head) : Buffer.alloc(0);
  let frags = [], fragOp = 0, closing = false, done = false;
  const conn = {
    remote: req.socket?.remoteAddress,
    get open() { return !closing && !done; },
    send(text) { if (!closing && !done) socket.write(frame(0x1, Buffer.from(String(text), 'utf8'))); },
    close(code = 1000) {
      if (closing || done) return;
      closing = true;
      try { socket.end(frame(0x8, Buffer.from([code >> 8, code & 255]))); } catch { socket.destroy(); }
      setTimeout(() => socket.destroy(), 2000).unref?.();
    },
  };
  const finish = () => { if (!done) { done = true; handlers.onClose?.(conn); } };
  socket.on('close', finish);
  socket.on('end', () => socket.end());
  socket.on('error', () => socket.destroy());
  socket.on('data', chunk => { buf = buf.length ? Buffer.concat([buf, chunk]) : chunk; parse(); });

  function parse() {
    while (buf.length >= 2) {
      const fin = (buf[0] & 0x80) !== 0, op = buf[0] & 0x0f, masked = (buf[1] & 0x80) !== 0;
      let len = buf[1] & 0x7f, off = 2;
      if (len === 126) { if (buf.length < 4) return; len = buf.readUInt16BE(2); off = 4; }
      else if (len === 127) {
        if (buf.length < 10) return;
        if (buf.readUInt32BE(2) !== 0) { socket.destroy(); return; }
        len = buf.readUInt32BE(6); off = 10;
      }
      if (len > MAX || !masked) { socket.destroy(); return; }   // los clientes siempre enmascaran
      const end = off + 4 + len;
      if (buf.length < end) return;
      const mask = buf.subarray(off, off + 4), payload = Buffer.from(buf.subarray(off + 4, end));
      for (let i = 0; i < payload.length; i++) payload[i] ^= mask[i & 3];
      buf = buf.subarray(end);
      if (op === 0x8) { conn.close(); return; }                                  // cierre: se contesta y se cierra
      if (op === 0x9) { if (!closing) socket.write(frame(0xA, payload)); continue; }   // ping → pong
      if (op === 0xA) continue;                                                  // pong
      if (op === 0x1 || op === 0x2) { fragOp = op; frags = [payload]; }
      else if (op === 0x0 && fragOp) frags.push(payload);
      else continue;
      if (fin) {
        const msg = Buffer.concat(frags); frags = [];
        const wasText = fragOp === 0x1; fragOp = 0;
        if (wasText) handlers.onMessage?.(conn, msg.toString('utf8'));
      }
    }
  }
  if (buf.length) parse();
  return conn;
}

module.exports = { accept, frame };
