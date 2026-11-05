# Línea superior (la melodía) de una pista: en cada corchea, la nota más aguda de Basic Pitch por encima de un mínimo.
# Sale en mini-notación casi lista para Strudel: 8 casillas por compás, «~» = silencio, «@n» = dura n corcheas.
# Uso: python ver_melodia.py <salida> <pista> --desde a4 --compases 8-15 [--amp 0.3] [--division 8]
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import argparse, csv
from comun import nota, midi, rejilla, compases

ap = argparse.ArgumentParser(description='Melodía (nota más aguda) de una pista')
ap.add_argument('salida'); ap.add_argument('pista')
ap.add_argument('--desde', default='c4', help='ignora notas por debajo de esta (c4)')
ap.add_argument('--compases', help='p. ej. 8-15 (por defecto todos)')
ap.add_argument('--amp', type=float, default=0.3, help='descarta notas más flojas que esto (0,3)')
ap.add_argument('--division', type=int, default=8, help='casillas por compás: 8 = corcheas, 16 = semicorcheas')
a = ap.parse_args()
r = rejilla(a.salida); b0, paso, n = r['inicio'], r['compas'] / a.division, a.division
lo = midi(a.desde)
mejor = {}
for x in csv.DictReader(open(os.path.join(a.salida, f"bp_{a.pista.lower().replace(' ', '_')}.csv"))):
    s, e, p, amp = float(x['start']), float(x['end']), int(x['pitch']), float(x['amp'])
    if p < lo or amp < a.amp:
        continue
    q = int(round((s - b0) / paso)); d = max(1, int(round((e - s) / paso)))
    if q not in mejor or p > mejor[q][0]:
        mejor[q] = (p, d)
for bar in compases(a.compases, r['compases']):
    celdas = []
    for k in range(n):
        v = mejor.get(bar * n + k)
        celdas.append(nota(v[0]) + ('' if v[1] == 1 else f'@{v[1]}') if v else '~')
    print(f'{bar:3d} ' + ' '.join(f'{c:7s}' for c in celdas))
