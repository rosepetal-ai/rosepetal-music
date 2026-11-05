# Espectrogramas en notas (CQT, de Do1 a Do8) de varias pistas en las ventanas de tiempo que elijas, para ver timbre,
# ataque, armónicos y registro de cada instrumento y elegir con qué sonido de Strudel imitarlo.
# Uso: python espectro_timbre.py <carpeta de pistas> <salida> "keyboard:3-11,synth:3-11,strings:94-102"      → timbre.png
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import argparse, numpy as np, librosa, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from comun import pista

ap = argparse.ArgumentParser(description='Espectrogramas CQT por pista y ventana')
ap.add_argument('pistas'); ap.add_argument('salida')
ap.add_argument('ventanas', help='pista:segundo inicial-segundo final, separadas por comas')
a = ap.parse_args()
SR = 22050
filas = []
for v in a.ventanas.split(','):
    nombre, _, rango = v.rpartition(':'); t0, t1 = map(float, rango.split('-')); filas.append((nombre.strip(), t0, t1))
fig, axs = plt.subplots(len(filas), 1, figsize=(16, 2.6 * len(filas)), squeeze=False)
for ax, (nombre, t0, t1) in zip(axs[:, 0], filas):
    y, _ = librosa.load(pista(a.pistas, nombre), sr=SR, mono=True, offset=t0, duration=t1 - t0)
    C = librosa.amplitude_to_db(np.abs(librosa.cqt(y, sr=SR, hop_length=256, fmin=librosa.note_to_hz('C1'), n_bins=84, bins_per_octave=12)), ref=np.max)
    ax.imshow(C, origin='lower', aspect='auto', extent=[t0, t1, 24, 108], cmap='magma', vmin=-60)
    ax.set_yticks(range(24, 109, 12)); ax.set_yticklabels([f'C{o}' for o in range(1, 9)])
    ax.set_title(f'{nombre} {t0:g}-{t1:g} s', fontsize=9)
plt.tight_layout(); out = os.path.join(a.salida, 'timbre.png'); plt.savefig(out, dpi=55)
print('→', out)
