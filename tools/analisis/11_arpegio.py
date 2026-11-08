# Transcribe un acompañamiento de acordes partidos (arpegios de piano, guitarra…) a mini-notación, compás a compás.
# En cada semicorchea se queda con la nota de Basic Pitch más fuerte que empiece ahí dentro del registro pedido (así
# se deja fuera la melodía de encima) y la alarga hasta la siguiente. Los compases son los de Suno alineados con la
# pieza (comparacion.json).
#
#   11_arpegio.py <comparación> <análisis> <pista> [--compases 8-23] [--rango a2-b4] [--amp 0.3] [--voces 1]
#
#   --voces   notas por semicorchea (1: solo la más fuerte; 2: las dos más fuertes, como acorde)
#   --minimo  descarta pasos cuya nota más fuerte no llegue a esta fracción de la más fuerte del compás
import os, sys, json, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from comun import compases, midi, nota
import fidelidad as F


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('comparacion'); ap.add_argument('analisis'); ap.add_argument('pista')
    ap.add_argument('--compases', default=''); ap.add_argument('--rango', default='a2-b4')
    ap.add_argument('--amp', type=float, default=0.3); ap.add_argument('--voces', type=int, default=1)
    ap.add_argument('--minimo', type=float, default=0.35)
    a = ap.parse_args()
    S = json.load(open(os.path.join(a.comparacion, 'comparacion.json'), encoding='utf-8'))['alineado']['inicios_suno']
    B = len(S) - 1
    lo, hi = [midi(x) for x in a.rango.split('-')]
    bp = [n for n in F.notas_bp(os.path.join(a.analisis, f'bp_{a.pista.replace(" ", "_")}.csv'), a.amp) if lo <= n[2] <= hi]
    salida = {}
    for k in compases(a.compases, B):
        paso = (S[k + 1] - S[k]) / 16
        pasos = []
        for st in range(16):
            t = S[k] + st * paso
            cand = sorted([(amp * min(1.0, (e - s) / paso), p) for s, e, p, amp in bp if t - paso / 2 <= s < t + paso / 2], reverse=True)
            vistos, elegidas = set(), []
            for w, p in cand:
                if p not in vistos:
                    vistos.add(p); elegidas.append((w, p))
            pasos.append(elegidas[:a.voces])
        tope = max((x[0][0] for x in pasos if x), default=0)
        ev = [(st, sorted(p for _, p in x)) for st, x in enumerate(pasos) if x and x[0][0] >= a.minimo * tope]
        partes, pos = [], 0
        for i, (st, ps) in enumerate(ev):
            fin = ev[i + 1][0] if i + 1 < len(ev) else 16
            if st > pos:
                partes.append('~' + (f'@{st - pos}' if st - pos > 1 else ''))
            n = ','.join(nota(p) for p in ps)
            partes.append((f'[{n}]' if len(ps) > 1 else n) + (f'@{fin - st}' if fin - st > 1 else ''))
            pos = fin
        if pos < 16:
            partes.append('~' + (f'@{16 - pos}' if 16 - pos > 1 else ''))
        txt = '~' if not ev else '[' + ' '.join(partes) + ']'
        salida[k] = txt
        print(f'{k:>3}  {len(ev):>2} notas  {txt}')
    ks = sorted(salida)
    print()
    for i in range(0, len(ks), 16):
        print(f'// {ks[i]}–{ks[min(i + 15, len(ks) - 1)]}')
        print('<' + ' '.join(salida[k] for k in ks[i:i + 16]) + '>')


if __name__ == '__main__':
    main()
