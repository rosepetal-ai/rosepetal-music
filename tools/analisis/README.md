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
