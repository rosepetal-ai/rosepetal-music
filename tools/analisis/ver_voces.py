# Notas sostenidas de una pista (pads, cuerdas, metales) compás a compás, ordenadas por peso (duración × volumen).
# Basic Pitch trocea las notas largas con vibrato o modulación en muchas cortas; sumando por compás se ve el acorde.
#
#   ver_voces.py <salida> <pista> [--compases 8-15] [--amp 0.3] [--top 6] [--mitades] [--comparacion comparacion.json]
#
# Usa bp_<pista>.csv de 04_notas.py. Con --comparacion (de 06_comparar.py) los compases son los de Suno alineados con
# la pieza (el tempo de Suno se mueve); si no, la rejilla recta de rejilla.json. Imprime cada compás como acorde de
# Strudel: [d3,a3,f#4,b4].
import os, sys, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import json
import numpy as np
from comun import nota, rejilla, compases
import fidelidad as F


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('salida'); ap.add_argument('pista')
    ap.add_argument('--compases', default=''); ap.add_argument('--amp', type=float, default=0.3)
    ap.add_argument('--top', type=int, default=6); ap.add_argument('--mitades', action='store_true')
    ap.add_argument('--minimo', type=float, default=0.12, help='peso mínimo respecto a la nota más fuerte del compás')
    ap.add_argument('--comparacion')
    a = ap.parse_args()
    rej = rejilla(a.salida)
    B = rej['compases']
    S = (np.array(json.load(open(a.comparacion, encoding='utf-8'))['alineado']['inicios_suno']) if a.comparacion
         else rej['inicio'] + np.arange(B + 1) * rej['compas'])
    notas = F.notas_bp(os.path.join(a.salida, f'bp_{a.pista.replace(" ", "_")}.csv'), a.amp)
    if notas is None:
        sys.exit(f'Falta bp_{a.pista}.csv en {a.salida}: ejecuta antes 04_notas.py')
    for k in compases(a.compases, B):
        trozos = [(S[k], (S[k] + S[k + 1]) / 2), ((S[k] + S[k + 1]) / 2, S[k + 1])] if a.mitades else [(S[k], S[k + 1])]
        fila = []
        for t0, t1 in trozos:
            w = {}
            for s, e, p, amp in notas:
                solape = min(e, t1) - max(s, t0)
                if solape > 0:
                    w[p] = w.get(p, 0) + solape * amp
            if not w:
                fila.append('~'); continue
            top = sorted(w.items(), key=lambda x: -x[1])[:a.top]
            m = top[0][1]
            top = [(p, v) for p, v in top if v >= a.minimo * m]
            fila.append('[' + ','.join(nota(p) for p, _ in sorted(top)) + ']  ' + ' '.join(f'{nota(p)}:{v / m:.2f}' for p, v in top))
        print(f'{k:>3}  ' + '   |   '.join(fila))


if __name__ == '__main__':
    main()
