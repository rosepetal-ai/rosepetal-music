# Medida rápida de una pista mientras se ajusta su sonido: nivel en la mezcla por sección, ecualización por octavas,
# anchura y paneo, Suno frente al render. Tarda segundos (06_comparar.py, minutos), así que sirve para tantear la
# ganancia, el filtro o el paneo antes de la comparación completa.
#
#   08_ajuste.py <pistas> <comparación> <renders> <pista> [--mezcla renders/11/v0]
#
#   <comparación>  carpeta con comparacion.json (alineado y secciones)
#   <renders>      versión a medir (hereda las capas que no tenga)
#   --mezcla       versión cuya mezcla se toma como referencia (por defecto, la misma <renders>)
import os, sys, json, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from scipy.signal import butter, sosfilt
from comun import pistas
import fidelidad as F

OCTAVAS = [63, 125, 250, 500, 1000, 2000, 4000, 8000]


def bandas(x):
    out = []
    for f0 in OCTAVAS:
        sos = butter(4, [f0 / 1.414, f0 * 1.414], btype='band', fs=F.SR, output='sos')
        y = sosfilt(sos, x, axis=-1)
        out.append(float(np.mean(y ** 2)))
    return np.array(out)


def estereo(x):
    L, R = x.astype(np.float64)
    l2, r2, lr = (L * L).mean(), (R * R).mean(), (L * R).mean()
    mid, side = (l2 + r2 + 2 * lr) / 4, (l2 + r2 - 2 * lr) / 4
    return 10 * np.log10(side / mid + 1e-12), 10 * np.log10(l2 / r2 + 1e-12), lr / np.sqrt(l2 * r2 + 1e-24)


def trozo(x, t0, t1):
    return x[:, int(t0 * F.SR):int(t1 * F.SR)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pistas'); ap.add_argument('comparacion'); ap.add_argument('renders'); ap.add_argument('pista')
    ap.add_argument('--mezcla'); ap.add_argument('--grupos', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'grupos-11.json'))
    a = ap.parse_args()
    comp = json.load(open(os.path.join(a.comparacion, 'comparacion.json'), encoding='utf-8'))
    S, R, secs = comp['alineado']['inicios_suno'], comp['alineado']['inicios_strudel'], comp['secciones']
    grupos = {k: v for k, v in json.load(open(a.grupos, encoding='utf-8')).items() if not k.startswith('_')}
    rutas = pistas(a.pistas)
    n = int((S[-1] + 2) * F.SR)
    mez_s = None
    for r in rutas.values():
        x = F.a_largo(F.carga(r), n); mez_s = x if mez_s is None else mez_s + x
    xs = F.carga(rutas[a.pista])
    xr = F.render(a.renders, grupos[a.pista])[0]
    otras = [t for k, v in grupos.items() if k != a.pista for t in v]
    mez_r = F.render(a.mezcla or a.renders, otras)[0]
    mez_r = F.a_largo(mez_r, max(mez_r.shape[1], xr.shape[1])) + F.a_largo(xr, max(mez_r.shape[1], xr.shape[1]))
    L = lambda x: F.lufs_integrado(F.filtro_k(x))
    print(f'{"sección":<8} {"Suno":>7} {"Strudel":>8} {"dif":>6}   (nivel en la mezcla, dB)')
    difs = []
    for nombre, x0, x1 in secs:
        ls = L(trozo(xs, S[x0], S[x1])) - L(trozo(mez_s, S[x0], S[x1]))
        lr = L(trozo(xr, R[x0], R[x1])) - L(trozo(mez_r, R[x0], R[x1]))
        ok = ls > -45 and lr > -45
        if ok:
            difs.append((lr - ls, x1 - x0))
        print(f'{nombre:<8} {ls:>7.1f} {lr:>8.1f} {lr - ls:>+6.1f}' + ('' if ok else '   (casi en silencio)'))
    if difs:
        print(f'media ponderada {np.average([d for d, _ in difs], weights=[w for _, w in difs]):+.1f} dB')
    # ecualización y estéreo sobre los compases donde suenan las dos
    act = [k for k in range(len(R) - 1) if L(trozo(xs, S[k], S[k + 1])) > -50 and L(trozo(xr, R[k], R[k + 1])) > -50]
    cat = lambda x, T: np.concatenate([trozo(x, T[k], T[k + 1]) for k in act], axis=1) if act else x[:, :1]
    cs, cr = cat(xs, S), cat(xr, R)
    bs, br = bandas(cs), bandas(cr)
    eq = 10 * np.log10(br / br.sum() + 1e-12) - 10 * np.log10(bs / bs.sum() + 1e-12)
    print('octavas (Strudel − Suno, dB):  ' + '  '.join(f'{f}:{v:+.1f}' for f, v in zip(OCTAVAS, eq)))
    print('forma Suno (dB respecto a su octava más fuerte): ' + '  '.join(f'{f}:{v:+.0f}' for f, v in zip(OCTAVAS, 10 * np.log10(bs / bs.max() + 1e-12))))
    ws, ps, cs_ = estereo(cs); wr, pr, cr_ = estereo(cr)
    print(f'lado/centro Suno {ws:+.1f} · Strudel {wr:+.1f} dB   izq−dcha Suno {ps:+.1f} · Strudel {pr:+.1f} dB   corr L/R Suno {cs_:.2f} · Strudel {cr_:.2f}')


if __name__ == '__main__':
    main()
