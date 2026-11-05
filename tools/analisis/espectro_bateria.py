# Espectrograma de la batería en tramos de 2 compases con la rejilla de semicorcheas dibujada encima (cian = pulsos):
# el bombo es la mancha de abajo, la caja la del medio y el charles la de arriba. Para transcribir a ojo.
# Uso: python espectro_bateria.py <carpeta de pistas> <salida> <compases, p. ej. 6,20,40> [--bateria drums]      → bateria.png
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import argparse, numpy as np, librosa, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from comun import pista, rejilla

ap = argparse.ArgumentParser(description='Espectrograma de batería con rejilla')
ap.add_argument('pistas'); ap.add_argument('salida'); ap.add_argument('compases', help='primer compás de cada tramo, separados por comas')
ap.add_argument('--bateria', default='drums')
a = ap.parse_args()
r = rejilla(a.salida); B, ini = r['pulso'], r['inicio']; SR = 22050
y, _ = librosa.load(pista(a.pistas, a.bateria), sr=SR, mono=True)
bars = [int(b) for b in a.compases.split(',')]
fig, axs = plt.subplots(len(bars), 1, figsize=(16, 3.2 * len(bars)), squeeze=False)
for ax, b in zip(axs[:, 0], bars):
    t0 = ini + b * 4 * B; seg = y[int(t0 * SR):int((t0 + 8 * B) * SR)]
    M = librosa.power_to_db(librosa.feature.melspectrogram(y=seg, sr=SR, n_mels=80, hop_length=96, fmax=11000), ref=np.max)
    ax.imshow(M, origin='lower', aspect='auto', extent=[0, 32, 0, 80], cmap='magma', vmin=-65)
    for k in range(33):
        ax.axvline(k, color='cyan' if k % 4 == 0 else 'white', lw=1.4 if k % 16 == 0 else (0.9 if k % 4 == 0 else 0.3), alpha=0.8)
    ax.set_xticks(np.arange(32) + 0.5); ax.set_xticklabels([str(k % 16) for k in range(32)], fontsize=7)
    ax.set_title(f'{a.bateria}, compases {b}-{b + 1} ({t0:.1f} s): semicorcheas 0-15', fontsize=9)
plt.tight_layout(); out = os.path.join(a.salida, 'bateria.png'); plt.savefig(out, dpi=55)
print('→', out)
