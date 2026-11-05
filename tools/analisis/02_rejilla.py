# 2. Rejilla de compases: tempo exacto y dónde cae el «1».
#  · Tempo: la recta que mejor se ajusta a los pulsos que Essentia encontró en la mezcla (01_global.py).
#  · Fase: de las posiciones posibles sobre esos pulsos (y un ajuste fino de ± media semicorchea), la que deja la caja de la
#    batería en los pulsos 2 y 4 (pasos 4 y 12 de 16).
#  · El «1» o el «3»: donde más cambian los acordes de un pulso al siguiente.
# Todo lo demás (acordes, notas, mapa, batería) se cuenta en esta rejilla.
# Uso: python 02_rejilla.py <carpeta de pistas> <salida> [--mitad] [--desplaza 0]      → rejilla.json
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import argparse, json, numpy as np, librosa
from scipy.ndimage import maximum_filter1d
from comun import pistas, pista, guarda

ap = argparse.ArgumentParser(description='Tempo exacto y posición del primer compás')
ap.add_argument('pistas', help='carpeta con las pistas separadas de Suno')
ap.add_argument('salida', help='carpeta de resultados (la de 01_global.py)')
ap.add_argument('--mitad', action='store_true', help='medio tiempo: cada negra son 2 pulsos de Essentia (la caja en 2 y 4 suena muy separada)')
ap.add_argument('--bateria', default='drums', help='nombre de la pista de batería (drums)')
ap.add_argument('--desplaza', type=float, default=0, help='mueve el «1» este número de negras si a oído no cae donde debe')
a = ap.parse_args()
p = os.path.join(a.salida, 'global.json')
if not os.path.exists(p):
    sys.exit('Falta global.json: ejecuta antes 01_global.py')
g = json.load(open(p)); bt = np.array(g['pulsos']); dur = g['duracion']

# tempo: recta por mínimos cuadrados a los pulsos de Essentia (los que se saltó o duplicó quedan fuera)
d = float(np.median(np.diff(bt))); a0 = bt[0]
for _ in range(5):
    i = np.round((bt - a0) / d); ok = np.abs(bt - (a0 + i * d)) < 0.15 * d
    a0, d = np.linalg.lstsq(np.vstack([np.ones(ok.sum()), i[ok]]).T, bt[ok], rcond=None)[0]
res = bt - (a0 + np.round((bt - a0) / d) * d)
deriva = [np.mean(res[(bt >= t) & (bt < t + 30)]) for t in range(0, int(dur), 30) if ((bt >= t) & (bt < t + 30)).any()]
paso = 2 if a.mitad else 1          # pulsos de Essentia por negra
B = d * paso; bpm = 60 / B
print(f'tempo {bpm:.3f} BPM (recta a {ok.sum()} de {len(bt)} pulsos de Essentia' + (', a medio tiempo' if a.mitad else '') + ')')
print(f'  los pulsos se apartan de la recta {1000 * np.sqrt(np.mean(res[ok] ** 2)):.0f} ms de media; por tramos de 30 s, entre '
      f'{1000 * min(deriva):+.0f} y {1000 * max(deriva):+.0f} ms (el tempo de la canción no es del todo fijo)')

# fase: la caja en los pasos 4 y 12
SR, HOP = 22050, 64
y, _ = librosa.load(pista(a.pistas, a.bateria), sr=SR, mono=True)
S = np.abs(librosa.stft(y, n_fft=1024, hop_length=HOP)); f = librosa.fft_frequencies(sr=SR, n_fft=1024)
e = np.log1p(1000 * S[(f >= 1500) & (f < 5000)].sum(0))
v = maximum_filter1d(np.maximum(0, np.diff(e, prepend=e[0])), 2 * int(0.02 * SR / HOP) + 1)   # ataques en la banda de la caja (±20 ms)
n16 = int(dur / (B / 4)) + 16


def caja_en_2_y_4(b0):   # cuánto más fuerte es la banda de la caja en los pasos 4 y 12 que de media
    idx = ((b0 + np.arange(-16, n16) * B / 4) * SR / HOP).astype(int); ok = (idx >= 0) & (idx < len(v))
    perfil = np.bincount((np.arange(-16, n16) % 16)[ok], weights=v[idx[ok]], minlength=16)
    return (perfil[4] + perfil[12]) / (perfil.mean() + 1e-9)


cands = [(caja_en_2_y_4(a0 + r * d + s * B / 4), r, s) for r in range(4 * paso) for s in np.linspace(-0.5, 0.5, 21)]
puntos, r, s = max(cands)
inicio = (a0 + r * d + s * B / 4) % (2 * B)
print(f'caja en 2 y 4: {puntos:.2f} veces la media (pulso {r} de Essentia, ajuste fino {s:+.2f} semicorcheas)')

# ¿el compás empieza ahí o dos negras después? Donde más cambia la armonía de un pulso al siguiente
todas = pistas(a.pistas)
armonicas = [todas[n] for n in ('bass', 'keyboard', 'piano', 'synth', 'guitar', 'strings') if n in todas]
if armonicas:
    sen = [librosa.load(p, sr=SR, mono=True)[0] for p in armonicas]
    n = min(len(x) for x in sen); h = sum(x[:n] for x in sen)
    C = librosa.feature.chroma_stft(y=h, sr=SR, hop_length=512); tc = librosa.frames_to_time(np.arange(C.shape[1]), sr=SR, hop_length=512)

    def cambio(b0):
        dd = []
        for c0 in np.arange(b0 + 4 * B, dur - 4 * B, 4 * B):
            antes = C[:, (tc >= c0 - B) & (tc < c0)].mean(1); despues = C[:, (tc >= c0) & (tc < c0 + B)].mean(1)
            dd.append(1 - antes @ despues / (np.linalg.norm(antes) * np.linalg.norm(despues) + 1e-9))
        return float(np.mean(dd))

    c1, c3 = cambio(inicio), cambio(inicio + 2 * B)
    print(f'cambio de armonía medio al empezar el compás: {c1:.3f} con el «1» en {inicio:.3f} s, {c3:.3f} con el «1» en {inicio + 2 * B:.3f} s')
    if c3 > c1:
        inicio += 2 * B
else:
    print('sin pistas armónicas: el «1» puede estar dos negras desplazado (usa --desplaza 2 si los acordes cambian a mitad de compás)')

inicio = float((inicio + a.desplaza * B) % (4 * B))
nb = int(np.ceil((dur - inicio) / (4 * B)))
print(f'compás de {4 * B:.4f} s; el primer «1» cae en {inicio:.3f} s' + (' (lo de antes es anacrusa)' if inicio > 0.05 else ''))
print(f'{nb} compases; en Strudel: .cpm({bpm:.2f} / 4)')
guarda(a.salida, 'rejilla.json', {'bpm': bpm, 'pulso': B, 'compas': 4 * B, 'inicio': inicio, 'compases': nb, 'caja_en_2_y_4': float(puntos)})
print(f'→ {os.path.join(a.salida, "rejilla.json")}')
