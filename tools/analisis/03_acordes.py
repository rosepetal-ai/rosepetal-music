# 3. Acordes por medio compás: HPCP de Essentia sobre la suma de las pistas armónicas, comparado con plantillas de acordes;
# y la nota más fuerte del bajo. Sale el acorde más probable, la alternativa y las cuatro notas más presentes.
# Uso: python 03_acordes.py <carpeta de pistas> <salida> [--armonia keyboard,synth,guitar,strings] [--bajo bass]      → acordes.json
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import argparse, numpy as np, essentia.standard as es
from comun import pistas, lista, rejilla, guarda

ap = argparse.ArgumentParser(description='Acordes por medio compás')
ap.add_argument('pistas'); ap.add_argument('salida')
ap.add_argument('--armonia', default='keyboard,piano,synth,guitar,strings', help='pistas que se suman para leer los acordes')
ap.add_argument('--bajo', default='bass', help='pista del bajo')
a = ap.parse_args()
r = rejilla(a.salida); B, b0, nb = r['pulso'], r['inicio'], r['compases']
SR = 44100
todas = pistas(a.pistas)
usar = [n for n in lista(a.armonia) if n in todas]
if not usar:
    sys.exit(f'Ninguna de las pistas {a.armonia} está en {a.pistas}')
print('armonía de:', ', '.join(usar), '· bajo:', a.bajo if a.bajo in todas else '(no hay)')
carga = lambda n: es.MonoLoader(filename=todas[n], sampleRate=SR)()
sen = [carga(n) for n in usar]; n = min(len(s) for s in sen); harm = sum(s[:n] for s in sen).astype(np.float32)
bajo = carga(a.bajo).astype(np.float32) if a.bajo in todas else None

W, H = 8192, 2048
win = es.Windowing(type='blackmanharris62'); spec = es.Spectrum()
picos = es.SpectralPeaks(orderBy='magnitude', magnitudeThreshold=1e-5, minFrequency=40, maxFrequency=5000, maxPeaks=60)
hpcp = es.HPCP(size=12, referenceFrequency=440, harmonics=8, bandPreset=False, minFrequency=40, maxFrequency=5000, weightType='cosine', nonLinear=False, windowSize=1.0)


def croma(y):
    return np.array([hpcp(*picos(spec(win(fr)))) for fr in es.FrameGenerator(y, frameSize=W, hopSize=H, startFromZero=True)])


C = croma(harm); CB = croma(bajo) if bajo is not None else None
tf = np.arange(len(C)) * H / SR + W / 2 / SR
NOMBRES = ['A', 'A#', 'B', 'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#']   # el HPCP de Essentia empieza en La
TIPOS = {'': [0, 4, 7], 'm': [0, 3, 7], 'maj7': [0, 4, 7, 11], 'm7': [0, 3, 7, 10], '7': [0, 4, 7, 10],
         'sus2': [0, 2, 7], 'sus4': [0, 5, 7], 'add9': [0, 2, 4, 7]}
plantillas = {}
for raiz in range(12):
    for tipo, iv in TIPOS.items():
        v = np.zeros(12); v[[(raiz + i) % 12 for i in iv]] = 1; plantillas[NOMBRES[raiz] + tipo] = v / np.linalg.norm(v)

res = []
for bar in range(nb):
    for mitad in range(2):
        ini = b0 + bar * 4 * B + mitad * 2 * B; m = (tf >= ini) & (tf < ini + 2 * B)
        fila = {'compas': bar, 'mitad': mitad, 'inicio': round(float(ini), 3), 'acorde': '-', 'alternativa': '-', 'puntuacion': 0, 'bajo': '-', 'notas': ''}
        if m.any() and C[m].mean(0).sum() > 1e-6:
            c = C[m].mean(0); cn = c / (np.linalg.norm(c) + 1e-9)
            orden = sorted(((float(cn @ v), k) for k, v in plantillas.items()), reverse=True)
            fila.update(acorde=orden[0][1], alternativa=orden[1][1], puntuacion=round(orden[0][0], 2),
                        notas=' '.join(NOMBRES[i] for i in np.argsort(-c)[:4]))
            if CB is not None and CB[m].mean(0).sum() > 1e-6:
                fila['bajo'] = NOMBRES[int(np.argmax(CB[m].mean(0)))]
        res.append(fila)
        print(f"{bar:3d}.{mitad} {fila['inicio']:6.1f}s  {fila['acorde']:6s} (alt {fila['alternativa']:6s} {fila['puntuacion']:.2f})  bajo {fila['bajo']:3s} | notas fuertes {fila['notas']}")
guarda(a.salida, 'acordes.json', res)
print(f'→ {os.path.join(a.salida, "acordes.json")}')
