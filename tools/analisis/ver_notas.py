# Notas de Basic Pitch de una pista, cuantizadas a semicorcheas en la rejilla: una línea por compás con
# «paso:nota(duración en pasos)»; las notas que empiezan a la vez salen juntas (acordes).
# Uso: python ver_notas.py <salida> <pista> [--compases 8-23] [--amp 0.25]
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import argparse, csv
from comun import nota, rejilla, compases

ap = argparse.ArgumentParser(description='Notas por compás de una pista')
ap.add_argument('salida'); ap.add_argument('pista', help='nombre de la pista (bass, keyboard, lead vocals…)')
ap.add_argument('--compases', help='p. ej. 8-23 o 0-7,40 (por defecto todos)')
ap.add_argument('--amp', type=float, default=0.25, help='descarta notas más flojas que esto (0–1; 0,25)')
a = ap.parse_args()
r = rejilla(a.salida); b0, paso = r['inicio'], r['pulso'] / 4
filas = [x for x in csv.DictReader(open(os.path.join(a.salida, f"bp_{a.pista.lower().replace(' ', '_')}.csv"))) if float(x['amp']) >= a.amp]
por = {}
for x in filas:
    s, e, p = float(x['start']), float(x['end']), int(x['pitch'])
    bar, st = divmod(int(round((s - b0) / paso)), 16)
    por.setdefault(bar, {}).setdefault(st, []).append((p, max(1, int(round((e - s) / paso)))))
for bar in compases(a.compases, r['compases']):
    if bar in por:
        print(f'{bar:3d} ' + '  '.join(f'{st}:' + ','.join(nota(p) for p, _ in sorted(v)) + f'({max(d for _, d in v)})'
                                       for st, v in sorted(por[bar].items())))
