# Patrón de batería por tramos: ataques de bombo, caja y charles (por bandas de frecuencia) plegados en un compás de
# 16 semicorcheas y promediados en cada tramo. La fase se reajusta en cada tramo (± media semicorchea, porque el tempo de
# Suno no es del todo fijo) para que la caja caiga en los pasos 4 y 12.
# Más fiable que clasificar golpe a golpe; si dudas, mira un par de compases con espectro_bateria.py.
# Uso: python ver_bateria.py <carpeta de pistas> <salida> [--tramos 6-11,12-16] [--bateria drums]
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import argparse, numpy as np, librosa
from comun import pista, rejilla, tramos

ap = argparse.ArgumentParser(description='Patrón medio de batería por tramos')
ap.add_argument('pistas'); ap.add_argument('salida')
ap.add_argument('--tramos', help='p. ej. 6-11,12-16 (por defecto, de 8 en 8 compases)')
ap.add_argument('--bateria', default='drums', help='pista a analizar (drums, percussion…)')
a = ap.parse_args()
r = rejilla(a.salida); B = r['pulso']
SR, HOP = 22050, 64
y, _ = librosa.load(pista(a.pistas, a.bateria), sr=SR, mono=True)
S = np.abs(librosa.stft(y, n_fft=1024, hop_length=HOP)); f = librosa.fft_frequencies(sr=SR, n_fft=1024)
env = {}
for k, (lo, hi) in {'bombo': (35, 90), 'caja': (1500, 5000), 'charles': (7500, 11000)}.items():
    e = np.log1p(1000 * S[(f >= lo) & (f < hi)].sum(0)); env[k] = np.maximum(0, np.diff(e, prepend=e[0]))


def perfil(v, b0, a_, b_):
    p = np.zeros(16)
    for bar in range(a_, b_):
        for st in range(16):
            c = b0 + (bar * 16 + st) * B / 4; i0, i1 = int((c - 0.025) * SR / HOP), int((c + 0.025) * SR / HOP)
            if 0 <= i0 < len(v):
                p[st] += v[i0:max(i0 + 1, i1)].max()
    return p / max(1, b_ - a_)


tira = lambda p: ''.join('█' if x > 0.75 * p.max() else '▓' if x > 0.5 * p.max() else '░' if x > 0.3 * p.max() else '·' for x in p)
print('pasos             0123456789abcdef  (█ fuerte, ▓ medio, ░ flojo; la caja debería caer en 4 y c)')
for a_, b_ in tramos(a.tramos, r['compases']):
    if perfil(env['caja'], r['inicio'], a_, b_).max() < 1e-3:
        print(f'compases {a_:2d}-{b_ - 1:2d}: sin batería'); continue
    mejor = max(((perfil(env['caja'], r['inicio'] + d * B / 4, a_, b_), d) for d in np.linspace(-0.5, 0.5, 21)),
                key=lambda x: (x[0][4] + x[0][12]) / (x[0].mean() + 1e-9))
    b0 = r['inicio'] + mejor[1] * B / 4
    print(f'compases {a_:2d}-{b_ - 1:2d} ({b0 + a_ * 4 * B:5.1f} s, desfase {mejor[1]:+.2f}):  '
          + '  '.join(f'{k} {tira(perfil(env[k], b0, a_, b_))}' for k in env))
