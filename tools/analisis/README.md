# Análisis de canciones de referencia

Con estos scripts se analizó «Quiet Beauty», una canción de Suno con pistas separadas, para recrearla en Strudel como la pieza 11 («Belleza callada»). Sirven para cualquier canción que Suno exporte con pistas: los archivos se llaman `<número> <Instrumento>.wav` (`1 Drums.wav`, `2 Bass.wav`, `4 Keyboard.wav`…). Las pistas se nombran sin el número y en minúsculas: `drums`, `bass`, `keyboard`, `lead vocals`.

## Instalar (una vez)

Essentia no tiene versión para Windows, así que el análisis corre en WSL (Ubuntu 22.04, Python 3.10). Si Ubuntu no trae `ensurepip`, crea el entorno sin pip e instálalo con get-pip:

```bash
python3 -m venv --without-pip ~/qbenv
curl -sSO https://bootstrap.pypa.io/get-pip.py && ~/qbenv/bin/python get-pip.py && rm get-pip.py
~/qbenv/bin/pip install -r tools/analisis/requirements.txt
```

## Paso a paso

Desde la carpeta del repositorio, dentro de WSL. Las carpetas de Windows están en `/mnt/c/…`. `P` es la carpeta de las pistas y `O` una carpeta para los resultados:

```bash
PY="$HOME/qbenv/bin/python -I"
P="/mnt/c/Users/<usuario>/Downloads/Mi canción Stems"
O=/tmp/analisis-mi-cancion
$PY tools/analisis/01_global.py "/mnt/c/Users/<usuario>/Downloads/Mi canción.wav" "$P" $O   # tempo, tonalidad, nivel de cada pista
$PY tools/analisis/02_rejilla.py "$P" $O --mitad    # tempo exacto y dónde cae el «1» (--mitad si va a medio tiempo)
$PY tools/analisis/03_acordes.py "$P" $O            # acorde de cada medio compás
$PY tools/analisis/04_notas.py "$P" $O              # notas con Basic Pitch (unos minutos)
$PY tools/analisis/05_mapa.py "$P" $O               # nivel por compás: las secciones
```

| Script | Qué hace | Escribe |
|---|---|---|
| `01_global.py` | Duración y tempo con Essentia y librosa. Tonalidad con cuatro perfiles distintos. Pico y nivel medio de cada pista (avisa de las pistas casi mudas). | `global.json` |
| `02_rejilla.py` | Tempo exacto: la recta que mejor se ajusta a los pulsos de Essentia en la mezcla. Fase: la que deja la caja de la batería en 2 y 4. Para decidir si el compás empieza en el pulso 1 o en el 3, mira dónde cambian más los acordes. Si a oído no cuadra, `--desplaza n` mueve el «1» n negras. Imprime el `.cpm(…)` para Strudel. | `rejilla.json` |
| `03_acordes.py` | HPCP de Essentia sobre la suma de las pistas armónicas, comparado con plantillas de acordes. Da el acorde, la alternativa, la nota del bajo y las cuatro notas más fuertes. | `acordes.json` |
| `04_notas.py` | Basic Pitch en cada pista que no sea de percusión, con un rango de notas por instrumento. `--solo bass,keyboard` analiza solo esas. | `bp_<pista>.csv`, `bp_<pista>.mid` |
| `05_mapa.py` | Nivel de cada pista en cada compás y los acordes. Debajo, una tira por pista: se ve dónde entra y sale cada instrumento. | `mapa.json` |
| `ver_notas.py` | Notas de una pista, compás a compás, en semicorcheas («paso:nota(duración)»). Filtra por volumen con `--amp`. | — |
| `ver_melodia.py` | La línea más aguda de una pista en corcheas, casi en mini-notación (`b5@2 a5 ~ …`). `--desde a4` ignora el acompañamiento. | — |
| `ver_bateria.py` | Patrón medio de bombo, caja y charles en 16 pasos, por tramos de compases (`--tramos 6-11,12-16`). | — |
| `espectro_bateria.py` | Espectrograma de 2 compases de batería con la rejilla dibujada, para transcribir a ojo. | `bateria.png` |
| `espectro_timbre.py` | Espectrogramas en notas de las pistas y ventanas que elijas (`"keyboard:3-11,strings:94-102"`). Sirven para ver el timbre y el registro. | `timbre.png` |

Dos utilidades más, en Node y sin dependencias, para samples sueltos:

- `wavinfo.js <archivo.wav>…`: formato, envolvente y notas dominantes. Sirve para saber en qué nota está un sample antes de afinarlo con `speed`.
- `metricas-sonidos.js <carpeta> <salida.png>`: métricas de ruido, barrido, glitch y tonalidad de todos los WAV de un pack, más una hoja de espectrogramas. Con ellas se descartaron los sonidos «raros» de Dronny Darko en la pieza 10.

## Lo que hay que saber

- **Medio tiempo.** Essentia y librosa marcaron 161,5 BPM en «Quiet Beauty», pero la caja sonaba en 2 y 4 a la mitad (80,75). Escucha antes de fiarte del tempo y usa `--mitad` en `02_rejilla.py` cuando haga falta.
- **El tempo de Suno no es del todo fijo.** En «Quiet Beauty» los pulsos se apartan de la recta entre −44 y +30 ms según el tramo. `02_rejilla.py` lo muestra. Por eso `ver_bateria.py` reajusta la fase en cada tramo.
- **Basic Pitch.** Añade notas de más con los armónicos (sobre todo octavas y quintas por encima). Sube `--amp` en `ver_notas.py`. Usa `ver_melodia.py --desde` para quedarte con la melodía y redondea a mano.
- **Batería.** Clasificar los golpes uno a uno por bandas falla con baterías procesadas. Los perfiles medios por tramo (`ver_bateria.py`) y el espectrograma con rejilla dan un patrón aproximado, no una transcripción exacta.
- **Pistas casi mudas.** Suno exporta todas las pistas aunque estén vacías. En «Quiet Beauty» la voz era casi silencio, así que la pieza es instrumental. `01_global.py` lo avisa.
- Los scripts se ejecutan con `python -I` y leen los WAV solo como datos. Las canciones y los resultados no se suben al repositorio.

Para comprobar la pieza resultante sin abrir la página, usa el verificador [`tools/strudel-check`](../strudel-check/check.mjs).

## Segunda fase: comparar la pieza con Suno

Cuando la pieza ya existe, estos pasos dicen qué falla y dónde, instrumento a instrumento.

1. **Marca cada capa** de la pieza con `.tag('nombre')` (comillas simples: con dobles Strudel lo toma como un patrón). No cambia el sonido.
2. **Renderiza cada capa** con el mismo Strudel de la página, sin tiempo real: `http://127.0.0.1:8091/render-lote.html?track=<pieza>&tags=bombo,caja,bajo&out=11/v0` las hace una detrás de otra (`render.html` hace una sola). Guarda `renders/11/v0/<capa>.wav` y `.json` (las notas). `renders/` no se sube a git.
   - **Versiones:** guarda cada versión de la pieza en `renders/11/versiones/` y renderiza solo las capas que cambian (`src=/renders/11/versiones/v2.strudel&out=11/v2`). Un `hereda.json` (`{"de": "../v1"}`) en `renders/11/v2` dice de dónde tomar las demás. La mezcla es la suma de las capas.
   - Con la pestaña oculta Chrome frena la página, pero el render no usa temporizadores y sigue; tarda más.
3. **Compara** (en WSL). `grupos-11.json` dice qué capas corresponden a cada pista de Suno:
   ```bash
   $PY tools/analisis/06_comparar.py "$P" $O renders/11/v0 renders/11/v0/comparacion
   ```
   Alinea cada compás de Suno con el render (el tempo de Suno se mueve), y mide por compás errores de **composición** (arreglo, notas, ritmo) y de **producción** (timbre, dinámica, efectos, nivel en la mezcla, paneo, anchura). Escribe `informe.md` con los problemas ordenados por prioridad, su evidencia y su confianza, y `errores.png`. Con `--base renders/11/v0/comparacion/comparacion.json` añade qué ha mejorado y qué ha empeorado respecto a otra versión.
4. **Escucha A/B**, Suno frente a cada versión, por pista y sección, a la misma sonoridad (−23 LUFS):
   ```bash
   $PY tools/analisis/07_ab.py "$P" renders/11/v1/comparacion renders/11/ab --versiones v0=renders/11/v0,v1=renders/11/v1
   ```
   y abre `http://127.0.0.1:8091/renders/11/ab/`. Espacio toca o para; A, B o Tab cambian de lado sin perder el punto. Hay modo a ciegas y un interruptor para oír el nivel real de cada trozo en su mezcla.

| Script | Qué hace | Escribe |
|---|---|---|
| `06_comparar.py` | Lo del paso 3. Timbre, notas y ritmo no dependen del volumen; el nivel se compara siempre respecto a la mezcla de cada lado. | `comparacion.json`, `informe.md`, `errores.png` |
| `07_ab.py` | Trozos alineados y a la misma sonoridad, en FLAC (o Opus con `--formato opus`, más lento), y la página de escucha (`ab.html`). | `manifest.json`, `index.html`, `<pista>/<sección>-<versión>.flac` |
| `08_ajuste.py` | Medida rápida de una pista mientras se ajusta: nivel en la mezcla por sección, ecualización por octavas, anchura y paneo, Suno frente al render. Segundos, no minutos. | — |
| `09_linea.py` | Transcribe una línea de una voz (el bajo) a mini-notación: ritmo de los ataques del audio, nota de Basic Pitch. Con bajos de notas largas que «baten» marca ataques de más: compruébalo con un espectrograma. | — |
| `10_samples_suno.py` | Saca samples de una pista de Suno (bucles de N compases, alineados y estirados al compás de la pieza) para cuando la síntesis no llega. | `<carpeta>/<nombre>.wav` |
| `12_balance.py` | Equilibrio de la mezcla: la ganancia de cada pista para que su peso en la mezcla, sección a sección, sea el de Suno. Las busca todas a la vez, porque subir una cambia lo que miden las demás. | — |
| `11_arpegio.py` | Transcribe un acompañamiento de acordes partidos: en cada semicorchea, la nota más fuerte dentro de un registro. | — |
| `ver_voces.py` | Notas sostenidas de una pista (pads, cuerdas, metales) sumadas por compás: el acorde de cada compás. | — |
| `ver_ataques.py` | Perfil medio de ataques en 16 pasos, Suno frente al render, por tramos y (con `--banda`) por bandas: el ritmo sin pasar por Basic Pitch. | — |
| `fidelidad.py` | Lo que comparten: carga, filtro K y LUFS (BS.1770), alineado por compás, croma, mel y ataques. | — |

### Lo que se aprendió con «Quiet Beauty»

- **El tempo de Suno se mueve, y mucho.** «Quiet Beauty» va a ~80,3 BPM hasta el compás 35 y a ~80,76 después: con una rejilla recta, el compás 0 cae ~0,6 s tarde. `06_comparar.py` alinea cada compás contra el render con una búsqueda de ±0,9 s que no deja saltar una corchea, y guarda los inicios reales en `comparacion.json`. `ver_notas.py`, `ver_voces.py`, `09_linea.py` y `11_arpegio.py` aceptan `--comparacion` para transcribir con esos compases.
- **Los pulsos de Essentia no sirven para seguir ese tempo:** se saltan alguno y acumulan casi una corchea de error.
- **Ajustar el nivel pista a pista no converge:** como se mide respecto a la mezcla, al corregir una se descuadran las otras. Primero el sonido y las notas de cada pista; al final, `12_balance.py` para todas a la vez.
- **Basic Pitch trocea las notas largas** con vibrato o modulación (el pad salía como un arpegio en semicorcheas). Sumando por compás (`ver_voces.py`) se ve el acorde.
