# 5. Mapa de la canción compás a compás: nivel de cada pista (dB RMS) y acorde de cada mitad; debajo, una tira por pista
# que deja ver de un vistazo dónde entra y sale cada instrumento (las secciones).
# Uso: python 05_mapa.py <carpeta de pistas> <salida>      → mapa.json (necesita rejilla.json; acordes.json si existe)
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import argparse, json, numpy as np, soundfile as sf
from comun import pistas, rejilla, guarda

ap = argparse.ArgumentParser(description='Nivel de cada pista y acordes por compás')
ap.add_argument('pistas'); ap.add_argument('salida')
a = ap.parse_args()
r = rejilla(a.salida); B, b0, nb = r['pulso'], r['inicio'], r['compases']
p = os.path.join(a.salida, 'acordes.json')
ch = {(x['compas'], x['mitad']): x['acorde'] for x in json.load(open(p))} if os.path.exists(p) else {}

niveles = {}
for nombre, ruta in pistas(a.pistas).items():
    y, sr = sf.read(ruta, always_2d=True); y = y.mean(1); fila = []
    for b in range(nb):
        seg = y[int(max(0, b0 + b * 4 * B) * sr):int((b0 + (b + 1) * 4 * B) * sr)]
        fila.append(round(float(20 * np.log10(np.sqrt(np.mean(seg ** 2)) + 1e-9)), 1) if len(seg) else -99.0)
    niveles[nombre] = fila

nombres = list(niveles)
if b0 > 0.05:
    print(f'(antes del compás 0 hay {b0:.2f} s de anacrusa)')
print('comp tiempo ' + ' '.join(f'{n[:5]:>5s}' for n in nombres) + '   acordes')
for b in range(nb):
    print(f'{b:3d} {b0 + b * 4 * B:6.1f}s ' + ' '.join(f'{niveles[n][b]:5.0f}' for n in nombres) + f'   {ch.get((b, 0), "-"):6s} {ch.get((b, 1), "-"):6s}')

print('\nmapa, un carácter por compás (█ > −30 dB, ▓ > −40, ░ > −50, · silencio):')
print(' ' * 17 + ''.join(str((i // 10) % 10) if i % 10 == 0 else ' ' for i in range(nb)))
for n in nombres:
    print(f'{n[:16]:16s} ' + ''.join('█' if v > -30 else '▓' if v > -40 else '░' if v > -50 else '·' for v in niveles[n]))
guarda(a.salida, 'mapa.json', {'inicio': b0, 'compas': 4 * B, 'niveles': niveles})
print(f'\n→ {os.path.join(a.salida, "mapa.json")}')
