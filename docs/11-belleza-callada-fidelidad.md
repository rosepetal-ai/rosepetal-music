# Pieza 11 · segunda fase: fidelidad respecto a Suno

«Belleza callada» recrea en Strudel «Quiet Beauty», una canción hecha con Suno. En esta fase se ha comparado la pieza con las pistas separadas de Suno capa a capa y compás a compás, y se ha mejorado instrumento a instrumento, guardando cada versión.

## Cómo se mide

1. **Cada capa de la pieza, por separado.** Cada capa lleva `.tag('nombre')`, que no cambia el sonido. [`render-lote.html`](../public/render-lote.html) la renderiza sin tiempo real con el mismo Strudel que la página (1.2.6). Una versión solo renderiza las capas que cambian y hereda las demás.
2. **Alineado.** El tempo de Suno no es fijo: ~80,3 BPM hasta el compás 35 y ~80,76 después; con una rejilla recta el compás 0 cae ~0,6 s tarde. [`06_comparar.py`](../tools/analisis/06_comparar.py) mueve cada compás de Suno hasta que sus ataques cuadran con el render, sin dejarle saltar una corchea. La caja de la batería confirma el resultado.
3. **Sonoridad.** Se mide con el filtro K y LUFS (BS.1770). El timbre, las notas y el ritmo se comparan sin el nivel. El nivel se compara siempre respecto a la mezcla de cada lado, así que subir el volumen general no «mejora» nada. Las escuchas A/B suenan las dos a −23 LUFS.
4. **Dos familias de errores por compás:**
   - **Composición:** arreglo (suena en uno y no en el otro), notas (croma del audio y notas de Basic Pitch) y ritmo (perfil de ataques).
   - **Producción:** timbre (forma del espectro), dinámica, efectos (relleno entre golpes y correlación L/R), nivel en la mezcla, paneo y anchura.
   - Cada problema lleva evidencia, una confianza y unos puntos: gravedad × peso de la pista en la mezcla de Suno × confianza × √compases.

El detalle de cada versión, compás a compás, está en `renders/11/<versión>/comparacion/informe.md` (local: lleva audio de Suno y no se sube).

## Diagnóstico de partida (v0)

Los 20 problemas con más puntos:

| # | Pista | Familia | Tipo | Compases | Evidencia | Confianza | Puntos |
|---|---|---|---|---|---|---|---|
| 1 | batería | producción | anchura | 6–71 | lados frente a centro: Suno −22,4 dB, Strudel −49,3 dB | media | 3,59 |
| 2 | synth (pad) | producción | nivel | 6–56 | en la mezcla: Suno −10,3 dB, Strudel −19,9 dB | alta | 3,47 |
| 3 | bajo | composición | ritmo | 8–52 | perfil de ataques 0,44 (1 = igual) | media | 3,26 |
| 4 | bajo | producción | timbre | 8–53 | espectro a 11,8 dB; centroide Suno 146 Hz, Strudel 229 Hz | media | 3,23 |
| 5 | mezcla | producción | timbre | 17–75 | espectro a 10,9 dB; centroide Suno 1008 Hz, Strudel 1670 Hz | media | 3,17 |
| 6 | synth (pad) | composición | notas | 1–56 | croma 0,70 | alta | 3,01 |
| 7 | bajo | producción | anchura | 8–53 | lados frente a centro: Suno −12,8 dB, Strudel −92,4 dB | media | 2,98 |
| 8 | synth (pad) | producción | timbre | 1–56 | espectro a 30,5 dB; centroide Suno 950 Hz, Strudel 558 Hz | media | 2,72 |
| 9 | batería | producción | timbre | 40–71 | espectro a 10,6 dB | media | 2,32 |
| 10 | teclado | composición | ritmo | 0–76 | perfil de ataques 0,50 | media | 2,23 |
| 11 | synth (pad) | producción | anchura | 1–56 | lados frente a centro: Suno +0,7 dB, Strudel −12,6 dB | media | 2,13 |
| 12 | synth (pad) | producción | nivel | 60–73 | en la mezcla: Suno −9,4 dB, Strudel −19,4 dB | alta | 2,13 |
| 13 | teclado | composición | notas | 0–76 | croma 0,85 | alta | 2,06 |
| 14 | synth (pad) | producción | efectos | 1–56 | correlación L/R Suno −0,07, Strudel 0,89 | baja | 2,03 |
| 15 | teclado | producción | timbre | 0–31 | espectro a 20,3 dB; centroide Suno 572 Hz, Strudel 814 Hz | media | 1,87 |
| 16 | bajo | composición | notas | 9–35 | croma 0,90 | alta | 1,82 |
| 17 | batería | producción | efectos | 6–50 | relleno entre golpes Suno −29,5 dB, Strudel −41,0 dB | baja | 1,76 |
| 18 | synth (pad) | composición | notas | 59–75 | croma 0,72 | alta | 1,65 |
| 19 | synth (pad) | producción | timbre | 59–75 | espectro a 28,7 dB | media | 1,57 |
| 20 | mezcla | producción | timbre | 0–10 | espectro a 13,9 dB | media | 1,55 |

**Puntos por pista (v0):**

| bajo | synth (pad) | teclado | batería | mezcla | cuerdas | guitarra | metales | percusión |
|---|---|---|---|---|---|---|---|---|
| 29,3 | 26,1 | 20,8 | 18,6 | 11,7 | 11,5 | 10,4 | 3,1 | 2,1 |

Tres cuartas partes de los puntos (98 de 134) eran de producción.

**Hallazgos que no se veían en la primera fase:**

- **Bajo:** el de Suno no toca corcheas. Sostiene la fundamental de cada acorde (La1, Mi1, Re2…) y a menudo adelanta el acorde siguiente a la última semicorchea. La pieza tocaba un groove de corcheas.
- **Piano:** no toca acordes en bloque. Parte el acorde en semicorcheas, muchas veces alternando dos notas (Fa#4–La3 en Re).
- **Synth:** la pista no es un arpegio, como parecía con Basic Pitch, sino un pad sostenido y muy abierto. Iba 10 dB por debajo en la pieza.
- **Maraca:** en Suno es una maraca en semicorcheas (con cuerpo desde 500 Hz); la pieza tenía ruido filtrado por encima de 5 kHz.
- **Margen:** la mezcla de la pieza llegaba a −1,0 dBFS en los bombos; no saturaba, pero iba justa. En v9 el pico queda en −3,9 dBFS.
- **Volumen general:** la pieza suena ~10 dB por debajo de Suno (−23 frente a −13 LUFS), porque Suno sale masterizada con limitador. Para comparar, todo se mide respecto a la mezcla de cada lado. Para un vídeo, normaliza la grabación.

## Versiones

Cada versión cambia un instrumento y se compara con la anterior (las demás capas, idénticas). Las piezas de cada versión están en `renders/11/versiones/` (local).

| Versión | Pista | Qué cambia | Familia | Medido frente a la versión anterior |
|---|---|---|---|---|
| v1 | pad (synth) | Voces sacadas compás a compás de la pista de Suno (Re3–Re5); supersaw abierto en estéreo, filtrado a 1,7 kHz; intensidad por sección | composición y producción | croma 0,70 → 0,90 · timbre 30,1 → 11,9 dB · nivel 8,8 → 2,0 dB · puntos 26,1 → 14,9 |
| v2 | bajo | La fundamental sostenida, con el acorde siguiente adelantado a la última semicorchea, en vez de corcheas; sierra con filtro de 24 dB/oct a 200 Hz; casi mudo en la intro y el cierre, fuera del parón | composición y producción | ritmo 0,45 → 0,82 · croma 0,90 → 0,96 · timbre 12,2 → 8,0 dB · compases que sobran 15 → 5 · puntos 29,3 → 16,5 |
| v3 | batería | Charles en corcheas con los acentos de Suno; un poco de la reverb común en caja, charles y platillo; intro más suave; un último golpe en el cierre | producción y arreglo | anchura −49 → −24 dB (Suno −24) · nivel 2,0 → 1,6 dB · puntos 18,6 → 14,1 · timbre 9,0 → 9,3 dB (⚠ leve: la caja va menos filtrada) |
| v4 | piano | Ostinato en semicorcheas transcrito de Suno (`11_arpegio.py`) en lugar de acordes en bloque; melodía del parón con puntillo; filtro de 24 dB/oct | composición y producción | notas (F1 por clase) 0,12 → 0,52 · ritmo 0,49 → 0,84 · croma 0,85 → 0,88 · timbre 17,1 → 13,2 dB · los puntos no bajan: aún sobraban 2 dB y brillo (v9, v10) |
| v5 | cuerdas | Acordes con las voces de la pista de cuerdas de Suno desde el final de A; salterio más apagado | composición y producción | croma 0,83 → 0,88 · timbre 19,8 → 13,3 dB · nivel 9,5 → 6,2 dB · puntos 11,5 → 9,6 |
| v6 | maraca | El bucle original de Suno (`samples/Suno`), a sus niveles por sección; ahorra 15 notas por compás en el parón | producción y arreglo | timbre 28,8 → 10,7 dB · nivel 12,9 → 3,3 dB · puntos 2,1 → 1,5 |
| v7 | guitarra | Solo en los compases en que suena en Suno; algo a la izquierda | arreglo y mezcla | compases que sobran 12 → 1 · nivel 3,9 → 3,4 dB · puntos 10,4 → 9,3 |
| v8 | metales | Solo donde suenan en Suno, con sus voces (octavas de B2 corregidas); más brillo | arreglo y notas | croma 0,77 → 0,85 · timbre 25,9 → 17,8 dB · sobran 17 → 7 · nivel 5,7 → 7,6 dB (⚠, en v10) |
| v9 | retoques | Batería más suave en la intro y el cierre; piano 2 dB más bajo y más oscuro; cuerdas con supersaw abierto, casi fuera en A y fuera en el cierre; maraca −3/−7 dB | producción | timbre de la mezcla 9,9 → 8,8 dB · cuerdas: timbre 13,3 → 11,7, nivel 6,2 → 4,5 · ⚠ el bajo y el pad suben +2/+3 dB respecto a la mezcla, porque esta ha bajado al bajar el piano y las cuerdas |
| v10 | equilibrio | Ganancia de todas las pistas a la vez con `12_balance.py` (bajo −2,4, pad −3,1, piano −1,8, guitarra +1,5, maraca −2,1 dB; metales por sección) | producción | bajo: puntos 19,1 → 15,4 · pad 17,7 → 15,2 · metales: nivel 7,6 → 6,9 dB, error por sección 4,4 → 0,3 dB · `12_balance.py` sobre v10 ya no propone cambios |

**Puntos de problema por versión** (menos es mejor; la mezcla mide su timbre y su dinámica de conjunto):

| Pista | v0 | v1 | v2 | v3 | v4 | v5 | v6 | v7 | v8 | v9 | v10 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| mezcla | 11,7 | 10,5 | 7,6 | 5,9 | 8,5 | 11,1 | 11,1 | 11,0 | 11,0 | 11,0 | 11,4 |
| bajo | 29,3 | 29,3 | 16,5 | 16,5 | 16,5 | 16,5 | 16,5 | 16,5 | 16,5 | 19,1 | 15,4 |
| pad (synth) | 26,1 | 14,9 | 14,9 | 14,9 | 14,9 | 14,9 | 14,9 | 14,9 | 14,9 | 17,7 | 15,2 |
| piano | 20,8 | 20,8 | 20,8 | 20,8 | 20,9 | 20,9 | 20,9 | 20,9 | 20,9 | 21,3 | 21,4 |
| batería | 18,6 | 18,6 | 18,6 | 14,1 | 14,1 | 14,1 | 14,1 | 14,1 | 14,1 | 14,1 | 15,5 |
| cuerdas | 11,5 | 11,5 | 11,5 | 11,5 | 11,5 | 9,6 | 9,6 | 9,6 | 9,6 | 9,5 | 9,5 |
| guitarra | 10,4 | 10,4 | 10,4 | 10,4 | 10,4 | 10,4 | 10,4 | 9,3 | 9,3 | 9,0 | 8,8 |
| maraca | 2,1 | 2,1 | 2,1 | 2,1 | 2,1 | 2,1 | 1,5 | 1,5 | 1,5 | 1,5 | 1,3 |
| metales | 3,1 | 3,1 | 3,1 | 3,1 | 3,1 | 3,1 | 3,1 | 3,1 | 3,0 | 3,0 | 2,6 |
| **total** | **134,3** | **122,0** | **106,3** | **100,1** | **102,8** | **103,6** | **103,0** | **101,9** | **101,8** | **107,1** | **102,0** |

v9 sube porque medir respecto a la mezcla acopla las pistas. Al bajar el piano y las cuerdas, la mezcla bajó, y el bajo y el pad (calibrados antes) quedaron 2–3 dB por encima. De ahí sale `12_balance.py`: busca a la vez las ganancias de todas las pistas. En v10 la batería, que es la referencia fija, pasa de 14,1 a 15,5 puntos: al bajar el resto queda +0,5 dB más fuerte, y el optimizador acepta ese error a cambio de reducir el de todas las demás.

**De v0 a v10:**

| Pista | Croma | Notas (F1 por clase) | Ritmo | Timbre (dB) | Error de nivel (dB) | Dinámica (dB) | Faltan / sobran (compases) |
|---|---|---|---|---|---|---|---|
| mezcla | 0,91 → 0,93 | – → – | 0,79 → 0,88 | 10,9 → 8,7 | 0,0 → 0,0 | 1,2 → 1,3 | 0/1 → 0/1 |
| bajo | 0,90 → 0,96 | 0,17 → 0,21 | 0,45 → 0,82 | 12,2 → 7,4 | 2,9 → 2,5 | 2,5 → 2,0 | 0/15 → 3/5 |
| pad (synth) | 0,70 → 0,90 | 0,02 → 0,03 | 0,89 → 0,96 | 30,1 → 11,9 | 8,8 → 2,3 | 3,6 → 2,3 | 0/4 → 0/4 |
| piano | 0,85 → 0,88 | 0,12 → 0,52 | 0,49 → 0,84 | 17,1 → 12,8 | 6,1 → 4,2 | 4,8 → 4,0 | 0/0 → 0/0 |
| batería | – → – | – → – | 0,72 → 0,71 | 9,0 → 9,3 | 2,0 → 2,5 | 2,1 → 1,9 | 1/0 → 0/0 |
| cuerdas | 0,83 → 0,88 | 0,02 → 0,02 | 0,95 → 0,97 | 19,8 → 11,7 | 9,5 → 4,6 | 5,1 → 5,0 | 1/5 → 1/3 |
| guitarra | 0,82 → 0,83 | 0,24 → 0,23 | 0,62 → 0,64 | 21,0 → 20,4 | 3,9 → 3,6 | 4,2 → 4,1 | 1/12 → 0/2 |
| maraca | – → – | – → – | 0,78 → 0,82 | 28,8 → 10,6 | 12,9 → 3,1 | 4,8 → 3,5 | 40/1 → 37/1 |
| metales | 0,77 → 0,85 | 0,02 → 0,03 | 0,69 → 0,70 | 25,9 → 17,3 | 5,7 → 6,9 | 7,8 → 7,4 | 0/17 → 0/6 |

- **Composición** (arreglo, notas, ritmo): de 36 a 26 puntos. **Producción**: de 98 a 76.
- **Correlación de ataques** entre la pieza y Suno: de 0,67 a 0,73.
- **Densidad:** 53 notas por compás como mucho (antes, 55).
- **Notas F1 de pad, cuerdas y metales:** se quedan cerca de 0 porque Basic Pitch trocea sus notas largas; para ellos cuenta el croma.

## Lo que queda

Los problemas con más puntos en v10, agrupados (el número es su puesto):

| # | Pista | Familia | Tipo | Compases | Evidencia | Confianza | Qué hacer |
|---|---|---|---|---|---|---|---|
| 1 | batería | producción | timbre | 30–72 | espectro a 10,7 dB; +9,5 dB a 1 kHz (cuerpo de la caja de SFXMint) | media | Otra caja (ver la tabla siguiente) |
| 2 | piano | producción | timbre | 24–76 | espectro a 13,3 dB; el Steinway filtrado no suena como el piano blando de Suno | media | Otro piano (ver la tabla siguiente) |
| 3 | pad | composición | notas | 1–56 | croma 0,90 (el F1 bajo es de Basic Pitch) | alta | Afinar a mano las voces de los compases con croma < 0,85 |
| 4, 5, 7 | mezcla | producción | timbre | 0–9, 55–64, 67–75 | intro, parón y cierre más brillantes que Suno (centroide ~1000 frente a ~700 Hz) | media | Sale del piano y del charles en esas secciones |
| 6, 10, 13 | pad | producción | timbre | 1–26, 59–75 | espectro a 10–14 dB en la intro y el final | media | Bajar el filtro en esas secciones o usar el pad de Suno como bucle |
| 9 | batería | producción | efectos | 50–62 | Strudel tiene más cola entre golpes (−23 frente a −40 dB) en el parón | baja | Menos reverb en la caja del parón |
| 11 | batería | composición | ritmo | 57–71 | perfil de ataques 0,67 en el parón y el final | media | Revisar el patrón con `ver_ataques.py --banda` |
| 14 | bajo | composición | notas | 38–53 | croma 0,96; algún compás de B2 con otro ritmo | alta | Comprobar con `ver_notas.py --comparacion` |
| 8 | piano | producción | timbre | 0–21 | espectro a 12,1 dB en la intro y A | media | Lo mismo que el 2 |
| 12 | cuerdas | producción | timbre | 24–55 | espectro a 11,5 dB | media | Cuerdas reales (ver la tabla siguiente) |
| 15 | piano | producción | paneo | 56–60 | en el parón, Suno lo lleva un poco a la derecha y la pieza a la izquierda | media | `pan()` en el parón |

Fuera de la tabla:
- **Bajo de la intro:** en v10 quedó tan bajo que 3 compases ya no cuentan como activos; en Suno se oye poco, pero se oye. Subirlo un poco.
- **Guitarra:** su timbre sigue lejos (20 dB), porque es un triángulo con FM.
- **Metales:** su timbre también sigue lejos (17 dB).
- **Woodwinds, «other» y la voz:** suenan a −30 dB o menos en Suno y no se han añadido.

## Instrumentos: qué cambiar y con qué

Todo lo propuesto es gratuito, funciona en local (el servidor sirve los archivos y Strudel los toca con `samples()`) y permite publicar la música. Las licencias se comprobaron en la página de cada librería; no se ha descargado nada todavía. Quedan unos 5 GB libres en C:, así que se propone bajar solo las carpetas necesarias.

| Instrumento | Ahora | Qué le falta | Propuesta | Licencia y tamaño |
|---|---|---|---|---|
| Batería | SFXMint (bombo, caja, aro, platillo) y charles de ruido | La caja de SFXMint tiene mucho cuerpo en 1 kHz (+10 dB frente a Suno) y no se corrige con filtros | 1) **Golpes sacados de la pista de batería de Suno** (bombo en los pasos 3 y 13, donde no coincide con el charles; caja en el 12 de los compases sin bombo en el 13), con `10_samples_suno.py` ampliado a golpes sueltos. 2) **Karoryfer Gogodze Phu Vol II** (batería lo-fi) | 1) Sin descarga. 2) CC0, ~400 MB |
| Piano | Steinway de VCSL muy filtrado | El de Suno es un piano apagado, tipo «felt»; filtrar un Steinway lo oscurece pero no lo vuelve blando | **VCSL Upright Piano** (Knight o Yamaha), con dos capas de intensidad; o **Osiris Piano** (Yamaha C2 tocado suave, con sordina) | CC0. VCSL: una carpeta de su repositorio (aquí solo están el Steinway, el xilófono y el salterio; tamaño sin comprobar). Osiris: ~460 MB |
| Cuerdas | Pad de sierra (supersaw) y salterio de arco | Una sección de cuerda real, oscura y muy abierta | **VSCO‑2 Community Edition**: Violin, Viola y Cello Sections «susVib» (2 capas) | CC0; solo esas carpetas (el paquete entero son 2,3 GB; las carpetas sueltas, sin comprobar) |
| Metales | Sierra con vibrato | Trompa suave | **VSCO‑2 CE F Horn** «sus» capas v1–v2 | CC0; una carpeta |
| Guitarra | Triángulo con FM | Una guitarra de verdad; en B2 Suno toca acordes | **FreePats FSBS Electric Guitar Clean #2** (eléctrica limpia) o **FreePats Spanish classical guitar** (nailon), según lo que se oiga en el A/B | CC0; 63 MB / 4,5 MB |
| Pad (synth) | Supersaw con las voces de Suno | Ya queda a ±1 dB y ±3 dB por octava | Mantenerlo. Si se quiere su textura exacta, un bucle por acorde sacado de la pista de Suno | — |
| Bajo | Supersaw filtrado | Ya queda cerca (timbre a 8 dB) | Mantenerlo | — |
| Maraca | **La de Suno** (bucle) | — | Hecho (v6) | Sin descarga |

A evitar: los `gm_…` de Strudel cargan por defecto fuentes de licencia desconocida (solo FluidR3 y GeneralUser GS son seguras, eligiéndolas con `n`); Sonatina Symphonic Orchestra prohíbe usarla en publicidad; Spitfire LABS no se puede extraer; Pianobook va pack a pack.

## Escuchar

Con el servidor en marcha (`node server.js`), abre http://127.0.0.1:8091/renders/11/ab/.

- **Qué hay:** Suno frente a la pieza original (v0) y a la versión final (v10), por pista y por sección. Para escuchar otra versión intermedia, ver [tools/analisis](../tools/analisis/README.md#segunda-fase-comparar-la-pieza-con-suno) (`07_ab.py --versiones`).
- **Igualados en sonoridad:** los dos lados suenan a −23 LUFS. La tabla de abajo da el nivel real de cada trozo en su mezcla, y el interruptor «nivel real» lo deja oír.
- **Cambiar de lado:** al pasar de A a B se salta al mismo compás aunque el tempo de Suno se mueva.
- **Teclas:** espacio toca o para; A, B o Tab cambian de lado. Hay modo a ciegas.

Los trozos de Suno se quedan en `renders/`, que git no sube.

Para rehacer todo el proceso con otra versión, ver [tools/analisis](../tools/analisis/README.md#segunda-fase-comparar-la-pieza-con-suno).
