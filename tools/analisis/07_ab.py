# Escucha A/B por pista y sección: Suno frente a una o varias versiones de la pieza, a la misma sonoridad.
#
#   07_ab.py <pistas> <comparación> <salida> --versiones v0=renders/11/v0,v1=renders/11/v1 [--grupos grupos-11.json]
#
#   <comparación>  carpeta con el comparacion.json de 06_comparar.py (de ahí salen el alineado y las secciones)
#   <salida>       carpeta servida por el servidor (p. ej. renders/11/ab → http://127.0.0.1:8091/renders/11/ab/)
#
# Cada trozo (pista × sección × versión) se recorta alineado al compás, se lleva a −23 LUFS y se guarda en FLAC
# (--formato opus ocupa diez veces menos, pero libsndfile tarda ~16 s en codificar 50 s de audio).
# Así la diferencia de volumen no se confunde con una diferencia de calidad; el nivel que tenía cada trozo en su
# mezcla se guarda aparte y la página lo enseña (y deja oírlo con «nivel real»).
import os, sys, json, shutil, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import soundfile as sf
from comun import pistas
import fidelidad as F

OBJETIVO = -23.0
COLA = 1.5


def recorta(x, t0, t1):
    a, b = max(0, int(t0 * F.SR)), int(t1 * F.SR)
    return F.a_largo(x[:, a:b], b - a)


def guarda(x, ruta, mezcla_lufs, formato='flac', medir=None):
    """medir: segundos del principio que cuentan para la sonoridad (la sección, sin la cola, que ya es la siguiente)"""
    xk = F.filtro_k(x[:, :int(medir * F.SR)] if medir else x)
    L = F.lufs_integrado(xk)
    if L < -60:
        return None
    g = 10 ** ((OBJETIVO - L) / 20)
    y = x * g
    pico = np.abs(y).max()
    if pico > 0.98:            # sin recortar: si no cabe, se baja todo el trozo y se apunta
        y *= 0.98 / pico
        g *= 0.98 / pico
    fade = int(0.3 * F.SR)
    y[:, -fade:] *= np.linspace(1, 0, fade)
    if formato == 'opus':
        sf.write(ruta, y.T, F.SR, format='OGG', subtype='OPUS')
    else:
        sf.write(ruta, y.T, F.SR, format='FLAC', subtype='PCM_16')
    return {'archivo': os.path.basename(ruta), 'lufs': round(L, 1), 'en_mezcla': round(L - mezcla_lufs, 1),
            'ganancia_db': round(20 * np.log10(g), 1)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pistas'); ap.add_argument('comparacion'); ap.add_argument('salida')
    ap.add_argument('--versiones', required=True)
    ap.add_argument('--grupos', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'grupos-11.json'))
    ap.add_argument('--solo', help='solo estas pistas (las demás se conservan del manifest anterior)')
    ap.add_argument('--formato', choices=['flac', 'opus'], default='flac')
    args = a_ = ap.parse_args()
    comp = json.load(open(os.path.join(args.comparacion, 'comparacion.json'), encoding='utf-8'))
    S, R = comp['alineado']['inicios_suno'], comp['alineado']['inicios_strudel']
    secs = comp['secciones']
    grupos = {k: v for k, v in json.load(open(args.grupos, encoding='utf-8')).items() if not k.startswith('_') and v}
    versiones = dict(v.split('=', 1) for v in args.versiones.split(','))
    rutas = pistas(args.pistas)
    os.makedirs(args.salida, exist_ok=True)
    man_ruta = os.path.join(args.salida, 'manifest.json')
    man = json.load(open(man_ruta, encoding='utf-8')) if os.path.exists(man_ruta) else {}
    # inicio de cada compás dentro del trozo, en cada lado: la página cambia de lado en el mismo punto musical aunque
    # el tempo de Suno no sea el de la pieza
    man.update({'objetivo_lufs': OBJETIVO, 'secciones': [
        {'nombre': n, 'desde': a, 'hasta': b, 'compases_suno': [round(S[k] - S[a], 4) for k in range(a, b + 1)],
         'compases_strudel': [round(R[k] - R[a], 4) for k in range(a, b + 1)]} for n, a, b in secs]})
    man.setdefault('pistas', {})
    man['versiones'] = sorted(set(man.get('versiones', [])) | set(versiones))
    solo = set(x.strip() for x in args.solo.split(',')) if args.solo else None

    # mezclas (para el nivel de cada trozo dentro de su mezcla)
    n = int((S[-1] + 2) * F.SR)
    mez_s = None
    for ruta in rutas.values():
        x = F.a_largo(F.carga(ruta), n)
        mez_s = x if mez_s is None else mez_s + x
    todas_capas = [t for v in grupos.values() for t in v]
    mez_r = {v: F.render(d, todas_capas)[0] for v, d in versiones.items()}

    def nivel(x, t0, t1):
        return F.lufs_integrado(F.filtro_k(recorta(x, t0, t1)))

    todas = [('mezcla', None)] + [(k, v) for k, v in grupos.items() if k in rutas]
    for nombre, tags in todas:
        if solo and nombre not in solo:
            continue
        print(nombre, flush=True)
        carpeta = os.path.join(args.salida, nombre.replace(' ', '_'))
        os.makedirs(carpeta, exist_ok=True)
        xs = mez_s if tags is None else F.carga(rutas[nombre])
        entrada = man['pistas'].setdefault(nombre, {})
        xr = {v: (mez_r[v] if tags is None else F.render(d, tags)[0]) for v, d in versiones.items()}
        for sn, a, b in secs:
            e = entrada.setdefault(sn, {'versiones': {}})
            ext = '.ogg' if a_.formato == 'opus' else '.flac'
            e['suno'] = guarda(recorta(xs, S[a], S[b] + COLA), os.path.join(carpeta, f'{sn}-suno{ext}'), nivel(mez_s, S[a], S[b]), a_.formato, S[b] - S[a])
            for v in versiones:
                e['versiones'][v] = guarda(recorta(xr[v], R[a], R[b] + COLA), os.path.join(carpeta, f'{sn}-{v}{ext}'),
                                           nivel(mez_r[v], R[a], R[b]), a_.formato, R[b] - R[a])
        del xs, xr
    with open(man_ruta, 'w', encoding='utf-8') as fh:
        json.dump(man, fh, ensure_ascii=False, indent=1)
    shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ab.html'), os.path.join(args.salida, 'index.html'))
    print('listo:', os.path.join(args.salida, 'index.html'))


if __name__ == '__main__':
    main()
