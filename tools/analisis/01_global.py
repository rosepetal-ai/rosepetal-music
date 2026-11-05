# 1. Visión global de la canción: duración, tempo (Essentia y librosa), tonalidad con cuatro perfiles y nivel de cada pista
# Uso: python 01_global.py <mezcla.wav> <carpeta de pistas> <carpeta de salida>      → global.json
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import argparse, numpy as np, librosa, essentia.standard as es
from comun import pistas, guarda

ap = argparse.ArgumentParser(description='Tempo, tonalidad y nivel de cada pista')
ap.add_argument('mezcla', help='WAV de la canción entera')
ap.add_argument('pistas', help='carpeta con las pistas separadas de Suno')
ap.add_argument('salida', help='carpeta donde escribir los resultados')
a = ap.parse_args()
os.makedirs(a.salida, exist_ok=True)
SR = 44100

mix = es.MonoLoader(filename=a.mezcla, sampleRate=SR)()
dur = len(mix) / SR
bpm, beats, conf, _, _ = es.RhythmExtractor2013(method='multifeature')(mix)
lb = float(np.atleast_1d(librosa.beat.beat_track(y=mix.astype(np.float32), sr=SR, units='time')[0])[0])
print(f'duración {dur:.1f} s ({int(dur // 60)}:{dur % 60:04.1f})')
print(f'tempo: Essentia {bpm:.2f} BPM (confianza {conf:.2f}) · librosa {lb:.2f} BPM')
print(f'  si la caja suena en 2 y 4 a la mitad de este tempo, la canción va a medio tiempo: usa {bpm / 2:.2f} en 02_rejilla.py')

tonalidad = {}
for perfil in ['edma', 'krumhansl', 'temperley', 'bgate']:
    k, escala, fuerza = es.KeyExtractor(profileType=perfil)(mix)[:3]
    tonalidad[perfil] = f'{k} {escala}'
    print(f'tonalidad ({perfil}): {k} {escala} (fuerza {fuerza:.2f})')

niveles = {}
print('\npista              pico    media')
for nombre, ruta in pistas(a.pistas).items():
    y = es.MonoLoader(filename=ruta, sampleRate=SR)()
    pico = float(20 * np.log10(np.abs(y).max() + 1e-9)); media = float(20 * np.log10(np.sqrt(np.mean(y ** 2)) + 1e-9))
    niveles[nombre] = {'pico': round(pico, 1), 'media': round(media, 1)}
    print(f'{nombre:16s} {pico:6.1f} dB {media:6.1f} dB' + ('   ← casi muda' if media < -55 else ''))

guarda(a.salida, 'global.json', {'duracion': dur, 'bpm_essentia': float(bpm), 'confianza': float(conf), 'bpm_librosa': lb,
                                 'pulsos': [float(b) for b in beats], 'tonalidad': tonalidad, 'pistas': niveles})
print(f'\n→ {os.path.join(a.salida, "global.json")}')
