# Transcribe una línea de una sola voz (el bajo, sobre todo) a mini-notación de Strudel, compás a compás.
# El ritmo sale de los ataques del audio (Basic Pitch junta notas repetidas y llega tarde en los graves); la nota, de
# Basic Pitch (la más pesada entre ataque y ataque, dentro del rango). Los compases son los de Suno alineados con la
# pieza (comparacion.json), así que siguen su tempo real.
#
#   09_linea.py <pistas> <comparación> <análisis> <pista> [--compases 8-23] [--umbral 0.45] [--rango e1-d3]
#               [--fmax 400] [--silencio 22]
#
#   <comparación>  carpeta con comparacion.json de 06_comparar.py
#   <análisis>     carpeta con bp_<pista>.csv de 04_notas.py
#   --umbral       fuerza mínima de un ataque (0–1, respecto a los ataques fuertes de toda la pista)
#   --silencio     un paso es silencio si su nivel queda tantos dB por debajo de lo más fuerte del compás
# Imprime cada compás («[a1@7 ~ a1@2 e2@6]») y, al final, cada tramo de 16 compases como una secuencia «<…>».
import os, sys, json, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from comun import pista, compases, midi, nota
import fidelidad as F


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pistas'); ap.add_argument('comparacion'); ap.add_argument('analisis'); ap.add_argument('pista')
    ap.add_argument('--compases', default=''); ap.add_argument('--umbral', type=float, default=0.45)
    ap.add_argument('--rango', default='e1-d3'); ap.add_argument('--fmax', type=float, default=400)
    ap.add_argument('--silencio', type=float, default=22); ap.add_argument('--amp', type=float, default=0.25)
    a = ap.parse_args()
    import librosa
    S = json.load(open(os.path.join(a.comparacion, 'comparacion.json'), encoding='utf-8'))['alineado']['inicios_suno']
    B = len(S) - 1
    lo, hi = [midi(x) for x in a.rango.split('-')]
    y = F.mono_f(F.carga(pista(a.pistas, a.pista)))
    hop = 128
    M = librosa.feature.melspectrogram(y=y, sr=F.SR_F, n_fft=2048, hop_length=hop, n_mels=40, fmin=25, fmax=a.fmax)
    env = librosa.onset.onset_strength(S=librosa.power_to_db(M), sr=F.SR_F, hop_length=hop)
    niv = 10 * np.log10(M.sum(axis=0) + 1e-12)
    ref = np.percentile(env[env > 0], 99) if (env > 0).any() else 1
    bp = [n for n in (F.notas_bp(os.path.join(a.analisis, f'bp_{a.pista.replace(" ", "_")}.csv'), a.amp) or []) if lo <= n[2] <= hi]
    fr = lambda t: int(round(t * F.SR_F / hop))
    salida = {}
    for k in compases(a.compases, B):
        paso = (S[k + 1] - S[k]) / 16
        fuerza, nivel = [], []
        for st in range(16):
            t = S[k] + st * paso
            fuerza.append(env[max(0, fr(t - paso * 0.45)):fr(t + paso * 0.45) + 1].max(initial=0) / ref)
            nivel.append(niv[fr(t):fr(t + paso) + 1].mean() if fr(t + paso) > fr(t) else -120)
        fuerza, nivel = np.array(fuerza), np.array(nivel)
        suena = nivel > nivel.max() - a.silencio
        ataques = [st for st in range(16) if fuerza[st] >= a.umbral and suena[st]
                   and fuerza[st] >= fuerza[max(0, st - 1)] and fuerza[st] >= fuerza[min(15, st + 1)]]
        if suena[0] and 0 not in ataques:      # la nota que viene del compás anterior se vuelve a escribir en el 1
            ataques = [0] + ataques
        eventos = []
        for i, st in enumerate(ataques):
            fin = ataques[i + 1] if i + 1 < len(ataques) else 16
            dur = fin - st
            for j in range(st + 1, fin):        # se corta donde deja de sonar
                if not suena[j]:
                    dur = j - st; break
            t0, t1 = S[k] + st * paso, S[k] + (st + dur) * paso
            w = {}
            for s, e, p, amp in bp:
                sol = min(e, t1) - max(s - 0.12, t0)   # Basic Pitch llega tarde en los graves
                if sol > 0:
                    w[p] = w.get(p, 0) + sol * amp
            if not w:
                continue
            pc = max(range(12), key=lambda c: sum(v for p, v in w.items() if p % 12 == c))
            p = max((p for p in w if p % 12 == pc), key=lambda p: w[p])
            eventos.append((st, dur, p))
        # a mini-notación de 16 pasos
        partes, pos = [], 0
        for st, dur, p in eventos:
            if st > pos:
                partes.append('~' + (f'@{st - pos}' if st - pos > 1 else ''))
            partes.append(nota(p) + (f'@{dur}' if dur > 1 else ''))
            pos = st + dur
        if pos < 16:
            partes.append('~' + (f'@{16 - pos}' if 16 - pos > 1 else ''))
        txt = '~' if all(x.startswith('~') for x in partes) else '[' + ' '.join(partes) + ']'
        salida[k] = txt
        print(f'{k:>3}  {txt:<60}  ataques ' + ' '.join('·' if v < 0.15 else str(min(9, int(v * 9))) for v in fuerza))
    ks = sorted(salida)
    print()
    for i in range(0, len(ks), 16):
        print(f'// {ks[i]}–{ks[min(i + 15, len(ks) - 1)]}')
        print('<' + ' '.join(salida[k] for k in ks[i:i + 16]) + '>')


if __name__ == '__main__':
    main()
