# 4. Transcripción de notas con Basic Pitch (Spotify) de cada pista melódica o armónica → bp_<pista>.csv y bp_<pista>.mid
# Basic Pitch añade notas de más con los armónicos: lee el resultado con ver_notas.py / ver_melodia.py y filtra a oído.
# Uso: python 04_notas.py <carpeta de pistas> <salida> [--solo bass,keyboard] [--inicio 0.5] [--nota 0.3]
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import argparse, csv, json
from basic_pitch.inference import predict
from basic_pitch import ICASSP_2022_MODEL_PATH
from comun import pistas, lista

ap = argparse.ArgumentParser(description='Notas de cada pista con Basic Pitch')
ap.add_argument('pistas'); ap.add_argument('salida')
ap.add_argument('--solo', help='solo estas pistas, por nombre y separadas por comas (por defecto todas menos batería y percusión)')
ap.add_argument('--inicio', type=float, default=0.5, help='umbral de ataque de nota de Basic Pitch (0,5; más alto = menos notas)')
ap.add_argument('--nota', type=float, default=0.3, help='umbral de nota sostenida de Basic Pitch (0,3)')
a = ap.parse_args()
os.makedirs(a.salida, exist_ok=True)

# pista: (frecuencia mínima Hz, máxima Hz, duración mínima de nota en ms)
RANGOS = {'bass': (30, 400, 80), 'keyboard': (60, 2500, 60), 'piano': (60, 2500, 60), 'synth': (60, 3000, 60),
          'guitar': (70, 2500, 60), 'strings': (60, 3000, 100), 'brass': (60, 2000, 100), 'woodwinds': (100, 3000, 100),
          'lead vocals': (80, 1500, 100), 'backing vocals': (80, 1500, 100)}
OTRAS = (40, 4000, 80)
SIN_NOTAS = {'drums', 'percussion'}
p = os.path.join(a.salida, 'rejilla.json')
tempo = json.load(open(p))['bpm'] if os.path.exists(p) else 120      # el MIDI sale al tempo de la canción si ya hay rejilla

for nombre, ruta in pistas(a.pistas).items():
    if (a.solo and nombre not in lista(a.solo)) or (not a.solo and nombre in SIN_NOTAS):
        continue
    lo, hi, ml = RANGOS.get(nombre, OTRAS)
    _, md, notas = predict(ruta, ICASSP_2022_MODEL_PATH, onset_threshold=a.inicio, frame_threshold=a.nota, minimum_note_length=ml,
                           minimum_frequency=lo, maximum_frequency=hi, melodia_trick=True, midi_tempo=tempo)
    base = os.path.join(a.salida, 'bp_' + nombre.replace(' ', '_'))
    with open(base + '.csv', 'w', newline='') as fh:
        w = csv.writer(fh); w.writerow(['start', 'end', 'pitch', 'amp'])
        for s, e, nota, amp, _ in sorted(notas):
            w.writerow([f'{s:.4f}', f'{e:.4f}', int(nota), f'{amp:.3f}'])
    md.write(base + '.mid')
    print(f'{nombre:16s} {len(notas):5d} notas → {base}.csv / .mid', flush=True)
