# Saca samples de las pistas de Suno para la pieza: bucles de uno o varios compases, ya alineados y estirados a la
# duración exacta del compás de la pieza (el tempo de Suno se mueve y el de Strudel no).
#
#   10_samples_suno.py <pistas> <comparación> <carpeta> nombre=pista:compases [nombre=pista:compases …]
#
#   <comparación>  carpeta con comparacion.json de 06_comparar.py (compases de Suno alineados con la pieza)
#   <carpeta>      dónde dejar los WAV; con samples/Suno el servidor hace de cada archivo un banco con su nombre
#   compases       «24» (un compás), «24-25» (un bucle de dos) o «66-67+70-71»: varios tramos del mismo largo se
#                  promedian (menos ruido de fondo de las otras pistas; solo para texturas que se repiten igual)
#   --lufs -20     lleva cada sample a esa sonoridad (las pistas de Suno salen muy bajas); imprime cuánto se subió,
#                  para saber qué ganancia le corresponde en la pieza
#
# Ejemplo: qb_maraca=percussion:70-71 --lufs -20  →  samples/Suno/qb_maraca.wav (dos compases, 48 kHz, estéreo)
# Para tocarlo: s("<qb_maraca ~>") cada dos compases (dura justo eso).
import os, sys, json, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly
from comun import pista
import fidelidad as F


def tramo(x, S, a, b, largo):
    """Compases a..b (incluido) de Suno, compás a compás estirados a la duración de la pieza y pegados"""
    trozos = []
    for k in range(a, b + 1):
        t0, t1 = S[k], S[k + 1]
        seg = x[:, int(t0 * F.SR):int(t1 * F.SR)]
        n = int(round(largo * F.SR))
        # remuestreo racional fino: n / len(seg)
        from fractions import Fraction
        fr = Fraction(n, seg.shape[1]).limit_denominator(2000)
        y = resample_poly(seg, fr.numerator, fr.denominator, axis=1)
        trozos.append(F.a_largo(y, n))
    return np.concatenate(trozos, axis=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pistas'); ap.add_argument('comparacion'); ap.add_argument('carpeta'); ap.add_argument('cortes', nargs='+')
    ap.add_argument('--lufs', type=float)
    a = ap.parse_args()
    comp = json.load(open(os.path.join(a.comparacion, 'comparacion.json'), encoding='utf-8'))
    S = comp['alineado']['inicios_suno']
    largo = comp['meta']['barSec']
    os.makedirs(a.carpeta, exist_ok=True)
    cache = {}
    for c in a.cortes:
        nombre, _, resto = c.partition('=')
        p, _, comps = resto.partition(':')
        if p not in cache:
            cache[p] = F.carga(pista(a.pistas, p))
        x = cache[p]
        partes = []
        for trozo in comps.split('+'):
            ini, _, fin = trozo.partition('-')
            partes.append(tramo(x, S, int(ini), int(fin or ini), largo))
        y = np.mean(partes, axis=0) if len(partes) > 1 else partes[0]
        f = int(0.003 * F.SR)                      # 3 ms de fundido para que el bucle no haga clic
        y[:, :f] *= np.linspace(0, 1, f); y[:, -f:] *= np.linspace(1, 0, f)
        ruta = os.path.join(a.carpeta, nombre + '.wav')
        L = F.lufs_integrado(F.filtro_k(y))
        sube = 0.0
        if a.lufs is not None:
            sube = a.lufs - L
            y = y * 10 ** (sube / 20)
            pico = np.abs(y).max()
            if pico > 0.98:
                y *= 0.98 / pico; sube += 20 * np.log10(0.98 / pico)
        sf.write(ruta, y.T.astype(np.float32), F.SR, subtype='PCM_24')
        print(f'{ruta}: {y.shape[1] / F.SR:.3f} s ({len(comps.split("+"))} tramo(s) de {p}, compases {comps}), '
              f'{L:.1f} LUFS en Suno' + (f', subido {sube:+.1f} dB' if sube else ''))


if __name__ == '__main__':
    main()
