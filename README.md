# Rosepetal Music

Música ambiental para los vídeos de Rosepetal: minimalista, instrumental, lo-fi, tocada en [Strudel](https://strudel.cc) con [DJ Claude](https://www.npmjs.com/package/dj-claude). Todos los samples son CC0 (SFXMint), así que lo que sale de aquí se puede publicar.

## Arrancar

Hace falta Node 22 o posterior.

```bash
node server.js
```

Abre http://127.0.0.1:8091 y pulsa **▶ Iniciar audio**. Para otro puerto: `node server.js 9000`.

En la página:

- **▶ Tocar aquí**: toca la pieza elegida de `public/music/`, sin DJ Claude.
- **● Grabar**: graba lo que suena (WebM/Opus, 256 kbit/s) y lo descarga al parar. Para un bucle limpio, empieza a grabar justo al darle a «Tocar aquí» y para tras 16 compases (~51 s a 75 BPM) o un múltiplo.

## Con DJ Claude

1. Arranca el servidor y abre la página.
2. Pasa DJ Claude a modo navegador (`switch_audio browser`). El servidor encuentra su puerto solo (con `netstat`, solo en Windows) y la página pasa a «● conectado a DJ Claude».
3. Lo que toque DJ Claude (`play_strudel`) suena en esta página, con los samples de `samples/` ya cargados.

Si no lo encuentra, dale el puerto de la pestaña de DJ Claude: `curl -X POST "http://127.0.0.1:8091/dj-port?port=PUERTO"`.

## Piezas

| Archivo | Qué es |
|---|---|
| `01-petalos-bajo-la-lluvia.strudel` | 75 BPM, bucle de 16 compases. Lluvia y crepitar de vinilo, acorde de piano, pad de piano eléctrico y flauta lenta con aire Nujabes. Fa maj9 · Mi m7 · Re m9 · La m9. Batería suave solo en la segunda mitad. |

Cada pieza lleva en sus comentarios la forma, la armonía y la afinación de los samples.

## Cómo está hecho

- `server.js`: sirve la página, las piezas (`/music/`), los samples (`/samples/`) y el relé de DJ Claude (`/dj`). Viene del proyecto de visuales de DJ Claude (djtest). `ws-lite.js` es el WebSocket mínimo del relé.
- `public/index.html`: reproductor. Registra los samples, recibe lo que manda DJ Claude y graba la salida.
- `samples/SFXMint/`: los sonidos, con licencia y huellas en [SOUNDS.md](SOUNDS.md). Cada archivo es un banco `sfx_<nombre>`; los WAV nuevos que pongas en esa carpeta aparecen solos en unos segundos. Otros packs en `samples/` se cargan pero git no los sube.

La variable `SAMPLES_DIRS` cambia las carpetas de samples (separadas por `;`). Para tocar desde otro equipo de la red local hace falta HTTPS con un certificado en `cert/` (igual que en djtest).
