# Perfil medio de ataques en 16 pasos de una pista de Suno y de su render, por tramos de compases alineados.
# Sirve para ver el ritmo de cualquier pista (bajo, teclado, guitarra) sin fiarse de Basic Pitch, que junta notas
# repetidas sin ataque claro.
#
#   ver_ataques.py <pistas> <comparación> <pista> [--tramos 8-23,24-39] [--renders renders/11/v0] [--banda agudo]
#
#   <comparación>  carpeta con el comparacion.json de 06_comparar.py (compases de Suno alineados con la pieza)
#   --renders      también el render de las capas de esa pista (grupos-11.json)
#   --banda        solo graves (< 150 Hz: bombo), medios (caja) o agudos (> 5 kHz: charles)
# Cada paso va de 0 a 9 (9 = el ataque más fuerte del tramo, en cada lado); «·» = casi nada.
import os, sys, json, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from comun import pista, tramos
import fidelidad as F


def perfil(r, S, a, b, banda=None):
    filas = [p for k in range(a, b) if (p := r.perfil(S[k], S[k + 1], banda=banda)) is not None]
    return np.mean(filas, axis=0) if filas else None


def dibuja(p):
    if p is None or p.max() <= 0:
        return '(silencio)'
    q = p / p.max()
    return ' '.join('·' if v < 0.15 else str(int(round(v * 9))) for v in q)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pistas'); ap.add_argument('comparacion'); ap.add_argument('pista')
    ap.add_argument('--tramos', default=''); ap.add_argument('--renders')
    ap.add_argument('--banda', choices=['grave', 'medio', 'agudo'])
    ap.add_argument('--grupos', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'grupos-11.json'))
    a = ap.parse_args()
    comp = json.load(open(os.path.join(a.comparacion, 'comparacion.json'), encoding='utf-8'))
    S, R = comp['alineado']['inicios_suno'], comp['alineado']['inicios_strudel']
    B = len(R) - 1
    rs = F.Rasgos(F.mono_f(F.carga(pista(a.pistas, a.pista))), croma=False)
    rr = None
    if a.renders:
        tags = json.load(open(a.grupos, encoding='utf-8'))[a.pista]
        rr = F.Rasgos(F.mono_f(F.render(a.renders, tags)[0]), croma=False)
    bd = None if not a.banda else ['grave', 'medio', 'agudo'].index(a.banda)
    print('pasos:         ' + ' '.join(str(i % 10) for i in range(16)))
    for x, y in tramos(a.tramos, B):
        print(f'{x:>2}–{y - 1:<2} Suno    ' + dibuja(perfil(rs, S, x, y, bd)))
        if rr is not None:
            print(f'      Strudel ' + dibuja(perfil(rr, R, x, y, bd)))


if __name__ == '__main__':
    main()
