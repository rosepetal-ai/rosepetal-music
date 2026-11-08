# Equilibrio de la mezcla: qué ganancia dar a cada pista para que su peso en la mezcla, sección a sección, sea el de
# Suno. Como todo se mide respecto a la mezcla, subir una pista cambia lo que miden las demás; por eso se buscan todas
# las ganancias a la vez, recalculando la mezcla (con las correlaciones entre pistas) en cada paso.
#
#   12_balance.py <pistas> <comparación> <renders> [--fija drums] [--grupos grupos-11.json]
#
#   --fija   pista que no se toca (la referencia; por defecto la batería, que marca el margen hasta 0 dBFS)
# Imprime, por pista, cuántos dB subir o bajar toda la capa y el error medio por sección antes y después.
import os, sys, json, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from scipy.optimize import minimize
from comun import pistas
import fidelidad as F


def potencias(señales, T, secs):
    """Por sección: matriz de productos cruzados de las señales con filtro K (mezcla = gᵀ C g)"""
    out = []
    for _, a, b in secs:
        i0, i1 = int(T[a] * F.SR), int(T[b] * F.SR)
        X = np.stack([s[:, i0:i1].reshape(-1) for s in señales]).astype(np.float64)
        out.append(X @ X.T / X.shape[1])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pistas'); ap.add_argument('comparacion'); ap.add_argument('renders')
    ap.add_argument('--fija', default='drums')
    ap.add_argument('--grupos', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'grupos-11.json'))
    a = ap.parse_args()
    comp = json.load(open(os.path.join(a.comparacion, 'comparacion.json'), encoding='utf-8'))
    S, R, secs = comp['alineado']['inicios_suno'], comp['alineado']['inicios_strudel'], comp['secciones']
    grupos = {k: v for k, v in json.load(open(a.grupos, encoding='utf-8')).items() if not k.startswith('_') and v}
    nombres = list(grupos)
    rutas = pistas(a.pistas)
    n = int((S[-1] + 2) * F.SR)
    # Suno: las pistas con capas en la pieza y, aparte, el resto (voz, «other»…), que también suma en su mezcla
    suno = [F.filtro_k(F.a_largo(F.carga(rutas[k]), n)) for k in nombres]
    resto = None
    for k, r in rutas.items():
        if k not in grupos:
            x = F.a_largo(F.carga(r), n); resto = x if resto is None else resto + x
    suno.append(F.filtro_k(resto))
    Cs = potencias(suno, S, secs); del suno
    strudel = [F.filtro_k(F.a_largo(F.render(a.renders, grupos[k])[0], n)) for k in nombres]
    Cr = potencias(strudel, R, secs); del strudel
    k = len(nombres)
    objetivo, pesos = [], []
    for s, C in enumerate(Cs):
        mez = C.sum()
        for i in range(k):
            rel = 10 * np.log10(C[i, i] / mez + 1e-15)
            activo = rel > -35 and Cr[s][i, i] > 1e-12
            objetivo.append(rel if activo else np.nan)
            pesos.append((secs[s][2] - secs[s][1]) * (10 ** (rel / 20) if activo else 0))
    objetivo, pesos = np.array(objetivo), np.array(pesos)
    fija = nombres.index(a.fija)

    def rels(gdb):
        g = 10 ** (np.asarray(gdb) / 20)
        out = []
        for C in Cr:
            mez = g @ C @ g
            out += [10 * np.log10(g[i] ** 2 * C[i, i] / mez + 1e-15) for i in range(k)]
        return np.array(out)

    def error(libres):
        gdb = np.insert(libres, fija, 0.0)
        d = rels(gdb) - objetivo
        ok = ~np.isnan(objetivo)
        return float(np.sum(pesos[ok] * d[ok] ** 2) / pesos[ok].sum()) + 0.002 * float(np.sum(libres ** 2))

    antes = rels(np.zeros(k)) - objetivo
    res = minimize(error, np.zeros(k - 1), method='L-BFGS-B', bounds=[(-12, 12)] * (k - 1))
    gdb = np.insert(res.x, fija, 0.0)
    despues = rels(gdb) - objetivo
    ok = ~np.isnan(objetivo)
    print(f'error medio por sección (ponderado): {np.average(np.abs(antes[ok]), weights=pesos[ok]):.1f} dB → '
          f'{np.average(np.abs(despues[ok]), weights=pesos[ok]):.1f} dB')
    for i, nombre in enumerate(nombres):
        sel = [s * k + i for s in range(len(secs)) if ok[s * k + i]]
        e0 = np.average(np.abs(antes[sel]), weights=pesos[sel]) if sel else float('nan')
        e1 = np.average(np.abs(despues[sel]), weights=pesos[sel]) if sel else float('nan')
        print(f'{nombre:<11} {gdb[i]:+5.1f} dB   (error {e0:.1f} → {e1:.1f} dB)' + ('   [referencia]' if i == fija else ''))
    print('por sección, después (Strudel − Suno, dB):')
    for i, nombre in enumerate(nombres):
        print(f'  {nombre:<11} ' + '  '.join(f'{secs[s][0]} {despues[s * k + i]:+.1f}' for s in range(len(secs)) if ok[s * k + i]))


if __name__ == '__main__':
    main()
