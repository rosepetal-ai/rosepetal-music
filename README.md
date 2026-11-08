# Rosepetal Music

Música ambiental para los vídeos de Rosepetal: minimalista, instrumental, lo-fi, tocada en [Strudel](https://strudel.cc) con [DJ Claude](https://www.npmjs.com/package/dj-claude). Todos los samples son CC0 (SFXMint y VCSL), así que lo que sale de aquí se puede publicar.

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

Para encontrar su puerto usa `netstat` (solo Windows) y, si no lo ve, prueba los puertos locales uno a uno (menos de un minuto). También se le puede dar a mano: `curl -X POST "http://127.0.0.1:8091/dj-port?port=PUERTO"`.

Sin DJ Claude, desde este equipo:

```bash
curl -X POST "http://127.0.0.1:8091/play?track=03-ambient-trance.strudel"
```

manda una pieza a todas las páginas abiertas, y `curl -X POST http://127.0.0.1:8091/hush` las para.

## Equipos modestos

Strudel genera el audio en el navegador, en tiempo real. En una Surface Go 3 (Core i3-10100Y, 5 W) las piezas con muchas capas se cortaban. Lo que lo evita:

- La página pide al navegador un búfer de audio grande (`latencyHint: 'playback'`).
- Una sola reverb y un solo eco por pieza, con los mismos ajustes en todas las capas que los usan: si cambian dentro de un canal (`orbit`), Strudel los recalcula sin parar.
- Unas 50 notas por compás como mucho: arpegios y charles a corcheas en vez de semicorcheas.
- La pestaña, a la vista: en segundo plano el navegador frena la página y se saltan notas.

## Piezas

| Archivo | Qué es |
|---|---|
| `01-petalos-bajo-la-lluvia.strudel` | 75 BPM, bucle de 16 compases. Lluvia y crepitar de vinilo, piano troceado, pad de piano eléctrico, arpegio de campanita, bajo que camina y dos flautas con aire Nujabes. Fa maj9 · Mi m7 · Re m9 · La m9. La batería suave entra en el compás 5. |
| `02-piano-y-cellos.strudel` | 75 BPM, 16 compases. Piano Steinway con la melodía, dos cellos que se contestan, bajo en pizzicato y batería muy suave de bombo grande y caja. Misma armonía que la 01. |
| `03-ambient-trance.strudel` | 90 BPM, 16 compases, tranquila y alegre. Los instrumentos de la 02 sobre una base de ambient trance (pad que bombea, arpegio en semicorcheas, bajo pizzicato a contratiempo) con batería lofi con swing. Do maj9 · Sol add9 · La m7 · Fa maj9. |
| `04-hacia-la-luz.strudel` | 90 BPM, Re mayor, luminosa y esperanzadora. Forma ABABCBA (56 compases, ~2 min 30 s): estrofa, puente y estribillo con violín. Batería downtempo al frente, piano a dos manos por detrás, bajo triangular con línea melódica, un sinte agudo que repite un motivo simple toda la pieza y un crecendo de principio a fin. |
| `05-lofi.strudel` | Lofi hip-hop a 100 BPM en Sol mayor, forma AABCABCA (64 compases, ~2 min 34 s). A: groove con piano a dos manos, xilófono y batería boom-bap (entra a mitad del primer A y se va a mitad del último). B: subida con un cello en crescendo. C: estribillo con violines (salterio de arco real), más batería y platillo. Mucho vinilo. |
| `06-ventanas-encendidas.strudel` | Downtempo / trip-hop nocturno y cinematográfico, 88 BPM, Fa# menor, 64 compases (~2 min 55 s). Un motivo de piano en 3+3+2 recorre toda la canción; estrofas, estribillos que suben al mayor relativo con las cuerdas a dos voces, un puente y un final que vuelve a dejar el piano solo. |
| `07-cinco-notas.strudel` | Post-rock / downtempo que crece poco a poco, 98 BPM, Sol mayor, 72 compases (~2 min 56 s). El motivo del xilófono es el hilo; los instrumentos entran de uno en uno (pad, bajo, piano, timbal, cuerdas y batería) hasta un clímax amplio, y todo se apaga hasta dejar el xilófono solo. |
| `08-latido-de-cristal.strudel` | Electrónica ambiental (Kiasmos, Ital Tek, Lorn), 118 BPM, Fa menor, 64 compases (~2 min 10 s). Bombo a negras, pad que bombea, piano apagado en 3-3-2, pulso de sierra a 3 contra 8 y bajo a contratiempo; en la pausa, un bajo oscuro y resonante y la melodía, que vuelve arriba en el clímax. |
| `09-orbita-lenta.strudel` | Electrónica espacial con pulso, pensada como BSO para animaciones: 120 BPM, Re mayor lidio, 2 min justos. Cada sección empieza cada 16 s con un golpe para poder cortar en el montaje; secuencia de sierra en semicorcheas, salterio con el tema, estrellas FM, subida y cumbre. |
| `10-codigo-petalo.strudel` | Banda sonora para las animaciones de Rosepetal con el aire de «Code 46» (The Free Association): 86 BPM, Re menor, 64 compases (~3 min). Breakbeat suave, piano, ostinato y salterio, sobre texturas de cine de Dronny Darko (necesita `samples/Texturas`, ver abajo). |
| `11-belleza-callada.strudel` | Recreación de «Quiet Beauty», una canción hecha con Suno, a partir del análisis de sus pistas ([tools/analisis](tools/analisis/README.md)): 80,67 BPM, Re mayor, 77 compases (~3 min 49 s). Intro, groove A, B con cuerdas y metales, B2, parón sin bajo, final y cierre. Ajustada después capa a capa contra las pistas de Suno ([informe](docs/11-belleza-callada-fidelidad.md)); la maraca es la de Suno (`samples/Suno`, no se sube). |

Cada pieza lleva en sus comentarios la forma, la armonía y la afinación de los samples.

Ojo al escribir piezas: en Strudel las comillas dobles son patrones de mini-notación, no textos de JavaScript. Métodos como `"...".replace()` fallan; escribe los nombres de los samples completos.

## Cómo está hecho

- `server.js`: sirve la página, las piezas (`/music/`), los samples (`/samples/`) y el relé de DJ Claude (`/dj`). Viene del proyecto de visuales de DJ Claude (djtest). `ws-lite.js` es el WebSocket mínimo del relé.
- `public/index.html`: reproductor. Registra los samples, recibe lo que manda DJ Claude y graba la salida.
- `samples/SFXMint/`: los sonidos de SFXMint; `samples/VCSL/`: piano Steinway, xilófono y salterio de arco afinados nota a nota (VCSL, CC0). Licencias y huellas en [SOUNDS.md](SOUNDS.md). Cada archivo es un banco `sfx_<nombre>`; los WAV nuevos que pongas en esa carpeta aparecen solos en unos segundos. Otros packs en `samples/` se cargan pero git no los sube.
- `samples/Texturas/`: texturas preparadas a mano; cada archivo es un banco con su nombre (`dd_resonancia`, `dd_pulso`…). Las de la pieza 10 vienen de «99Sounds x Dronny Darko – Cinematic Textures», que no se puede redistribuir: descárgalo de 99sounds.org y prepáralo con `tools/prep-dronny-darko.js` (ver [SOUNDS.md](SOUNDS.md)).

La variable `SAMPLES_DIRS` cambia las carpetas de samples (separadas por `;`). Para tocar desde otro equipo de la red local hace falta HTTPS con un certificado en `cert/` (igual que en djtest).

## Herramientas

- **Comprobar una pieza sin abrir la página:**
  ```bash
  cd tools/strudel-check && npm install && cd ../..   # solo la primera vez
  node tools/strudel-check/check.mjs public/music/11-belleza-callada.strudel
  ```
  Evalúa la pieza con el mismo Strudel que la página (1.2.6) y cuenta las notas de cada compás. Avisa si un compás pasa de 55 (el Surface Go puede cortar) y si un sonido no existe en el servidor. La página no devuelve los errores cuando la pieza llega por `POST /play`; esto sí.
- **Analizar una canción de referencia** (tempo, compases, acordes, notas, secciones y timbre a partir de sus pistas separadas): [tools/analisis](tools/analisis/README.md). Usa librosa, Essentia y Basic Pitch en WSL.
- **Comparar una pieza con su referencia, instrumento a instrumento:** `public/render-lote.html` renderiza cada capa de la pieza (marcada con `.tag('nombre')`) sin tiempo real, y `tools/analisis/06_comparar.py` y `07_ab.py` dan un informe por compás y una página de escucha A/B en `http://127.0.0.1:8091/renders/…` (ver [tools/analisis](tools/analisis/README.md)).
- **Preparar las texturas de Dronny Darko** de la pieza 10: `tools/prep-dronny-darko.js` (instrucciones en su cabecera).
