# Compara una pieza de Strudel, renderizada capa a capa con public/render.html, con las pistas de Suno, compás a compás.
#
#   06_comparar.py <pistas> <análisis> <renders> <salida> [--grupos grupos-11.json] [--secciones "intro:8,A:16,…"]
#                  [--base <otra salida>/comparacion.json] [--bp <carpeta con bp_*.csv>]
#
#   <pistas>    carpeta con las pistas de Suno («1 Drums.wav»…)
#   <análisis>  carpeta de 02_rejilla.py (rejilla.json) y de 04_notas.py (bp_<pista>.csv; o --bp)
#   <renders>   carpeta con los renders de cada capa (<capa>.wav y .json); las que falten se buscan en la versión
#               de la que hereda (hereda.json: {"de": "../v0"})
#   --grupos    qué capas de la pieza corresponden a cada pista de Suno
#   --base      comparacion.json de una versión anterior: añade al informe qué mejora y qué empeora
#
# Primero alinea: cada compás de Suno se mueve hasta ±120 ms para que sus ataques cuadren con el render (el tempo
# de Suno se mueve un poco). Luego mide cada pista en cada compás y separa los errores en dos familias:
#   composición  arreglo (suena en uno y no en el otro), notas (croma y notas de Basic Pitch), ritmo (ataques)
#   producción   timbre (forma del espectro), dinámica (curva de nivel), efectos (relleno entre golpes y
#                correlación L/R), nivel en la mezcla, paneo y anchura
# Las comparaciones de timbre, notas y ritmo no dependen del volumen. Los errores de nivel se miden siempre
# respecto a la mezcla de cada uno, así que subir el volumen general no los arregla.
#
# Escribe comparacion.json, informe.md y errores.png en <salida>.
import os, sys, json, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from comun import pistas, rejilla, midi
import fidelidad as F

TIPOS = {  # tipo → (familia, confianza de partida)
    'arreglo': ('composición', 0.8), 'notas': ('composición', 0.75), 'ritmo': ('composición', 0.65),
    'timbre': ('producción', 0.6), 'dinámica': ('producción', 0.7), 'efectos': ('producción', 0.45),
    'nivel': ('producción', 0.85), 'paneo': ('producción', 0.6), 'anchura': ('producción', 0.5),
}
SIN_NOTAS = {'drums', 'percussion'}
BANDAS = [63, 125, 250, 500, 1000, 2000, 4000, 8000]


def sev(v, a, b):
    """0 por debajo de a, 1 por encima de b"""
    return float(np.clip((v - a) / (b - a), 0, 1))


def r1(v, n=2):
    return None if v is None else round(float(v), n)


def secciones(texto, B):
    out, k = [], 0
    for parte in texto.split(','):
        nombre, _, n = parte.rpartition(':')
        out.append((nombre.strip(), k, k + int(n)))
        k += int(n)
    if k != B:
        sys.exit(f'Las secciones suman {k} compases y la pieza tiene {B}')
    return out


def seccion_de(secs, k):
    return next(n for n, a, b in secs if a <= k < b)


def mide_pista(x, S, B, mezcla):
    """Medidas por compás que no dependen de las notas: nivel, nivel en la mezcla, paneo, anchura, relleno"""
    T = F.Tramos(x)
    out = []
    for k in range(B):
        m = T.mide(S[k], S[k + 1])
        m['rel'] = m['lufs'] - mezcla[k]
        env = T.envolvente(S[k], S[k + 1])
        m['relleno'] = None if env is None else float(np.percentile(env, 10) - np.percentile(env, 90))
        out.append(m)
    integ = F.lufs_integrado(T.xk)
    del T
    return out, integ


def notas_render(notas, S, R):
    out = []
    for n in notas:
        v = n.get('note', n.get('n'))
        if v is None or n.get('s') in ('white', 'pink', 'brown'):
            continue
        try:
            p = int(round(float(v))) if not isinstance(v, str) else midi(v)
        except (SystemExit, ValueError):
            continue
        out.append((F.a_tiempo_suno(n['t'], S, R), p))
    return out


def compara(nombre, xs, xr, notas_r, bp, S, R, B, mez_s, mez_r, corr):
    pitched = nombre not in SIN_NOTAS
    ms, Ls = mide_pista(xs, S, B, mez_s)
    if xr is not None:
        mr, Lr = mide_pista(xr, R, B, mez_r)
    else:
        mr, Lr = [None] * B, -120.0
    fs_ = F.Rasgos(F.mono_f(xs), croma=pitched)
    fr_ = F.Rasgos(F.mono_f(xr), croma=pitched) if xr is not None else None
    umbral_s, umbral_r = max(Ls - 20, -60), max(Lr - 20, -60)
    nr = notas_render(notas_r, S, R) if pitched else []
    compases, eq_s, eq_r = [], np.zeros(64), np.zeros(64)
    for k in range(B):
        s = ms[k]; r = mr[k]
        a_s = s['lufs'] > umbral_s
        a_r = r is not None and r['lufs'] > umbral_r
        c = {'k': k, 's': {q: r1(v) for q, v in s.items()}, 'r': None if r is None else {q: r1(v) for q, v in r.items()},
             'activo_s': bool(a_s), 'activo_r': bool(a_r), 'err': {}}
        prom_rel = s['rel'] if a_s or r is None else r['rel']
        c['prominencia'] = r1(np.clip(10 ** (prom_rel / 20) * 2, 0.03, 1), 3)
        alin = float(np.clip(0.5 + corr[k], 0.5, 1))
        sep = 0.7 if s['rel'] < -25 else 1.0
        err = c['err']
        if a_s != a_r and (a_s or a_r):
            L, u = (s['lufs'], umbral_s) if a_s else (r['lufs'], umbral_r)
            err['arreglo'] = (max(0.3, sev(L - u, 0, 10)), TIPOS['arreglo'][1] * sep,
                              'falta en Strudel' if a_s else 'sobra en Strudel')
        if a_s and a_r:
            # notas: croma de audio y, si hay, notas de Basic Pitch (por clase de nota)
            if pitched:
                mitad = (S[k + 1] - S[k]) / 2
                cs = [F.coseno(fs_.croma_tramo(S[k] + i * mitad, S[k] + (i + 1) * mitad),
                               fr_.croma_tramo(R[k] + i * (R[k + 1] - R[k]) / 2, R[k] + (i + 1) * (R[k + 1] - R[k]) / 2))
                      for i in range(2)]
                cs = [v for v in cs if v is not None]
                c['croma'] = r1(np.mean(cs), 3) if cs else None
                f1c = f1e = None
                if bp is not None:
                    a = [(t, p) for t, _, p, _ in bp if S[k] <= t < S[k + 1]]
                    b = [(t, p) for t, p in nr if S[k] <= t < S[k + 1]]
                    f1c, f1e = F.f1(b, a, clase=True), F.f1(b, a)
                c['f1_clase'], c['f1_nota'] = r1(f1c, 3), r1(f1e, 3)
                parts = []
                if c['croma'] is not None:
                    parts.append((sev(0.95 - c['croma'], 0, 0.35), 0.8))
                if f1c is not None:
                    parts.append((sev(0.8 - f1c, 0, 0.6), 0.55))
                if parts:
                    v = float(np.average([p[0] for p in parts], weights=[p[1] for p in parts]))
                    conf = max(p[1] for p in parts) + (0.1 if len(parts) == 2 and abs(parts[0][0] - parts[1][0]) < 0.3 else 0)
                    err['notas'] = (v, min(0.9, conf) * alin * sep, '')
            # ritmo: perfil de ataques en 16 pasos (la batería, por bandas)
            if nombre in SIN_NOTAS:
                sims, pes = [], []
                for bnd in range(3):
                    ps, pr = fs_.perfil(S[k], S[k + 1], banda=bnd), fr_.perfil(R[k], R[k + 1], banda=bnd)
                    v = F.coseno(ps, pr)
                    if v is not None:
                        sims.append(v); pes.append(float(ps.sum()))
                rit = float(np.average(sims, weights=pes)) if sims and sum(pes) > 0 else None
            else:
                rit = F.coseno(fs_.perfil(S[k], S[k + 1]), fr_.perfil(R[k], R[k + 1]))
            c['ritmo'] = r1(rit, 3)
            if rit is not None:
                err['ritmo'] = (sev(0.9 - rit, 0, 0.5), TIPOS['ritmo'][1] * alin * sep, '')
            # timbre: forma del espectro (mel en dB, sin el nivel)
            es, er = fs_.mel_medio(S[k], S[k + 1]), fr_.mel_medio(R[k], R[k + 1])
            eq_s += es; eq_r += er
            ds, dr = 10 * np.log10(es + 1e-12), 10 * np.log10(er + 1e-12)
            vis = (ds > ds.max() - 45) | (dr > dr.max() - 45)
            ds, dr = ds - np.average(ds[vis], weights=es[vis]), dr - np.average(dr[vis], weights=er[vis])
            dist = float(np.sqrt(np.mean((dr[vis] - ds[vis]) ** 2)))
            c['timbre_db'] = r1(dist, 1)
            c['centroide'] = [r1(fs_.cent[fs_.fr(S[k]):fs_.fr(S[k + 1])].mean(), 0), r1(fr_.cent[fr_.fr(R[k]):fr_.fr(R[k + 1])].mean(), 0)]
            err['timbre'] = (sev(dist, 3, 12), TIPOS['timbre'][1] * sep, '')
            # dinámica: el compás frente a la sonoridad de toda la pista, en cada lado
            dev = (r['lufs'] - Lr) - (s['lufs'] - Ls)
            c['dinamica_db'] = r1(dev, 1)
            err['dinámica'] = (sev(abs(dev), 2, 9), TIPOS['dinámica'][1] * sep, f'{dev:+.1f} dB')
            # mezcla
            dn = r['rel'] - s['rel']
            err['nivel'] = (sev(abs(dn), 1.5, 7.5), TIPOS['nivel'][1] * sep, f'{dn:+.1f} dB')
            dp = r['pan_db'] - s['pan_db']
            err['paneo'] = (sev(abs(dp), 1, 6), TIPOS['paneo'][1] * sep, f'{dp:+.1f} dB')
            dw = r['anchura_db'] - s['anchura_db']
            err['anchura'] = (sev(abs(dw), 3, 12), TIPOS['anchura'][1] * sep, f'{dw:+.1f} dB')
            if s['relleno'] is not None and r['relleno'] is not None:
                drl = r['relleno'] - s['relleno']
                err['efectos'] = (max(sev(abs(drl), 4, 14), sev(abs(r['icc'] - s['icc']), 0.15, 0.6)),
                                  TIPOS['efectos'][1] * sep, f'relleno {drl:+.1f} dB · L/R {r["icc"] - s["icc"]:+.2f}')
        c['err'] = {t: {'sev': r1(v[0], 3), 'conf': r1(v[1], 3), 'nota': v[2]} for t, v in err.items()}
        compases.append(c)
    eq = None
    if eq_s.sum() > 0 and eq_r.sum() > 0:
        ds, dr = 10 * np.log10(eq_s + 1e-12), 10 * np.log10(eq_r + 1e-12)
        bandas = []
        for f0 in BANDAS:
            sel = (fs_.mel_f >= f0 / np.sqrt(2)) & (fs_.mel_f < f0 * np.sqrt(2))
            bandas.append(float(10 * np.log10(eq_r[sel].sum() / eq_r.sum() + 1e-12) - 10 * np.log10(eq_s[sel].sum() / eq_s.sum() + 1e-12)) if sel.any() else None)
        eq = dict(zip([str(b) for b in BANDAS], [r1(b, 1) for b in bandas]))
    return {'lufs_s': r1(Ls, 1), 'lufs_r': r1(Lr, 1), 'compases': compases, 'eq': eq}


def problemas(nombre, res, secs):
    """Tramos de compases seguidos con el mismo error (se admite un compás de hueco)"""
    out = []
    B = len(res['compases'])
    for tipo, (fam, _) in TIPOS.items():
        fila = [c['err'].get(tipo) for c in res['compases']]
        k = 0
        while k < B:
            if not fila[k] or fila[k]['sev'] < 0.35:
                k += 1; continue
            a = k; ult = k
            while k + 1 < B and ((fila[k + 1] and fila[k + 1]['sev'] >= 0.35) or
                                 (k + 2 < B and fila[k + 2] and fila[k + 2]['sev'] >= 0.35 and tipo != 'arreglo')):
                k += 1
                if fila[k] and fila[k]['sev'] >= 0.35:
                    ult = k
            b = ult
            ks = [j for j in range(a, b + 1) if fila[j]]
            if tipo == 'arreglo':  # no mezclar «falta» y «sobra»
                ks = [j for j in ks if fila[j]['nota'] == fila[a]['nota']]
            sv = float(np.mean([fila[j]['sev'] for j in ks]))
            pr = float(np.mean([res['compases'][j]['prominencia'] for j in ks]))
            cf = float(np.mean([fila[j]['conf'] for j in ks]))
            out.append({'pista': nombre, 'tipo': tipo, 'familia': fam, 'compases': [a, b],
                        'secciones': sorted({seccion_de(secs, j) for j in ks}, key=lambda n: [s[0] for s in secs].index(n)),
                        'severidad': r1(sv, 2), 'prominencia': r1(pr, 2), 'confianza': r1(cf, 2),
                        'puntos': r1(sv * pr * cf * np.sqrt(len(ks)), 3), 'evidencia': evidencia(tipo, res, ks, fila)})
            k += 1
    return out


def media(vals):
    vals = [v for v in vals if v is not None]
    return None if not vals else float(np.mean(vals))


def evidencia(tipo, res, ks, fila):
    cs = [res['compases'][j] for j in ks]
    if tipo == 'arreglo':
        lado = fila[ks[0]]['nota']
        if lado == 'falta en Strudel':
            return f"{lado}: en Suno suena a {media([c['s']['rel'] for c in cs]):+.1f} dB de la mezcla"
        return f"{lado}: en Strudel suena a {media([c['r']['rel'] for c in cs]):+.1f} dB de la mezcla"
    if tipo == 'notas':
        cr, f1c = media([c.get('croma') for c in cs]), media([c.get('f1_clase') for c in cs])
        return 'croma ' + ('–' if cr is None else f'{cr:.2f}') + (' · notas (clase) F1 ' + f'{f1c:.2f}' if f1c is not None else '')
    if tipo == 'ritmo':
        return f"perfil de ataques {media([c.get('ritmo') for c in cs]):.2f} (1 = igual)"
    if tipo == 'timbre':
        ce = [c['centroide'] for c in cs if c.get('centroide')]
        return (f"espectro a {media([c.get('timbre_db') for c in cs]):.1f} dB de media · brillo (centroide) "
                f"Suno {media([x[0] for x in ce]):.0f} Hz, Strudel {media([x[1] for x in ce]):.0f} Hz")
    if tipo == 'dinámica':
        return f"el compás va {media([c.get('dinamica_db') for c in cs]):+.1f} dB respecto a la curva de Suno"
    if tipo == 'nivel':
        return (f"en la mezcla: Suno {media([c['s']['rel'] for c in cs]):+.1f} dB, Strudel {media([c['r']['rel'] for c in cs]):+.1f} dB")
    if tipo == 'paneo':
        return (f"izquierda − derecha: Suno {media([c['s']['pan_db'] for c in cs]):+.1f} dB, "
                f"Strudel {media([c['r']['pan_db'] for c in cs]):+.1f} dB")
    if tipo == 'anchura':
        return (f"lados frente a centro: Suno {media([c['s']['anchura_db'] for c in cs]):+.1f} dB, "
                f"Strudel {media([c['r']['anchura_db'] for c in cs]):+.1f} dB")
    if tipo == 'efectos':
        return (f"relleno entre golpes Suno {media([c['s']['relleno'] for c in cs]):.1f} dB, Strudel {media([c['r']['relleno'] for c in cs]):.1f} dB"
                f" · correlación L/R Suno {media([c['s']['icc'] for c in cs]):.2f}, Strudel {media([c['r']['icc'] for c in cs]):.2f}")
    return ''


def resumen(res):
    cs = res['compases']
    ambos = [c for c in cs if c['activo_s'] and c['activo_r']]
    abs_ = lambda q: media([abs(c['err'][q]['sev']) for c in ambos if q in c['err']])
    return {
        'compases_suno': sum(c['activo_s'] for c in cs), 'compases_strudel': sum(c['activo_r'] for c in cs),
        'faltan': sum(c['activo_s'] and not c['activo_r'] for c in cs), 'sobran': sum(c['activo_r'] and not c['activo_s'] for c in cs),
        'croma': r1(media([c.get('croma') for c in ambos]), 3), 'f1_clase': r1(media([c.get('f1_clase') for c in ambos]), 3),
        'ritmo': r1(media([c.get('ritmo') for c in ambos]), 3), 'timbre_db': r1(media([c.get('timbre_db') for c in ambos]), 1),
        'nivel_db': r1(media([c['r']['rel'] - c['s']['rel'] for c in ambos]), 1),
        'nivel_abs_db': r1(media([abs(c['r']['rel'] - c['s']['rel']) for c in ambos]), 1),
        'dinamica_abs_db': r1(media([abs(c['dinamica_db']) for c in ambos if c.get('dinamica_db') is not None]), 1),
        'paneo_db': r1(media([c['r']['pan_db'] - c['s']['pan_db'] for c in ambos]), 1),
        'anchura_db': r1(media([c['r']['anchura_db'] - c['s']['anchura_db'] for c in ambos]), 1),
        'relleno_db': r1(media([c['r']['relleno'] - c['s']['relleno'] for c in ambos if c['r']['relleno'] is not None and c['s']['relleno'] is not None]), 1),
        'sev_media': {t: r1(abs_(t), 3) for t in TIPOS if t != 'arreglo'},
    }


def figura(res_todas, secs, ruta):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    nombres = list(res_todas)
    B = len(next(iter(res_todas.values()))['compases'])
    fig, axs = plt.subplots(2, 1, figsize=(16, 1 + 0.42 * len(nombres) * 2), sharex=True)
    for ax, fam in zip(axs, ['composición', 'producción']):
        M = np.zeros((len(nombres), B))
        for i, n in enumerate(nombres):
            for c in res_todas[n]['compases']:
                v = [e['sev'] * e['conf'] for t, e in c['err'].items() if TIPOS[t][0] == fam]
                M[i, c['k']] = (max(v) if v else 0) * c['prominencia']
        ax.imshow(M, aspect='auto', cmap='magma', vmin=0, vmax=0.6, interpolation='nearest')
        ax.set_yticks(range(len(nombres))); ax.set_yticklabels(nombres)
        ax.set_title(f'Errores de {fam} (gravedad × confianza × peso en la mezcla)', loc='left')
        for n, a, b in secs:
            ax.axvline(a - 0.5, color='w', lw=0.6)
            ax.text(a, -0.7, n, color='k', fontsize=8, va='bottom')
    axs[-1].set_xlabel('compás')
    fig.tight_layout()
    fig.savefig(ruta, dpi=110)


ACCION = {
    'arreglo': lambda p: 'Añadir la parte en esos compases.' if 'falta' in p['evidencia'] else 'Quitar o bajar la parte en esos compases.',
    'notas': lambda p: 'Revisar la transcripción de esos compases con ver_notas.py / ver_melodia.py.',
    'ritmo': lambda p: 'Revisar el patrón rítmico (ver_bateria.py para la batería, ver_notas.py para el resto).',
    'timbre': lambda p: 'Cambiar el sonido (otro sample o síntesis) o ecualizar.',
    'dinámica': lambda p: 'Ajustar la curva de ganancia en esa sección.',
    'nivel': lambda p: 'Ajustar el volumen de la capa en esa sección.',
    'paneo': lambda p: 'Ajustar pan().',
    'anchura': lambda p: 'Abrir o cerrar la imagen estéreo (pan alterno, reverb, capas dobladas).',
    'efectos': lambda p: 'Ajustar reverb (room/size) o el release.',
}


def informe(res_todas, probs, secs, args, alin, base):
    nivel = lambda c: 'alta' if c >= 0.7 else 'media' if c >= 0.5 else 'baja'
    L = ['# Comparación con Suno', '',
         f'Pistas: `{args.pistas}` · render: `{args.renders}`.', '',
         f'Alineado: cada compás de Suno se mueve entre {min(alin["desfase_ms"]):+.0f} y {max(alin["desfase_ms"]):+.0f} ms respecto a la rejilla recta '
         f'de rejilla.json para que sus ataques cuadren con el render; correlación media de ataques {np.mean(alin["correlacion"]):.2f}. '
         'Tempo de Suno por sección: ' + ', '.join(
             f'{n} {240 * (b - a) / (alin["inicios_suno"][b] - alin["inicios_suno"][a]):.2f}' for n, a, b in secs) +
         f' BPM (la pieza va a {240 / (alin["inicios_strudel"][1] - alin["inicios_strudel"][0]):.2f}).', '',
         'Los errores de **composición** (arreglo, notas, ritmo) y de **producción** (timbre, dinámica, efectos, nivel, paneo, anchura) se miden por compás. '
         '«Puntos» = gravedad × peso de la pista en la mezcla de Suno × confianza × √compases. Timbre, notas y ritmo no dependen del volumen; '
         'el nivel se compara siempre respecto a la mezcla de cada lado.', '',
         '## Prioridades', '',
         '| # | Pista | Familia | Tipo | Compases | Secciones | Evidencia | Gravedad | Confianza | Puntos | Qué hacer |',
         '|---|---|---|---|---|---|---|---|---|---|---|']
    for i, p in enumerate(probs[:40], 1):
        a, b = p['compases']
        L.append(f"| {i} | {p['pista']} | {p['familia']} | {p['tipo']} | {a}–{b} | {', '.join(p['secciones'])} | {p['evidencia']} | "
                 f"{p['severidad']:.2f} | {nivel(p['confianza'])} ({p['confianza']:.2f}) | {p['puntos']:.3f} | {ACCION[p['tipo']](p)} |")
    L += ['', '## Por pista', '',
          '| Pista | LUFS Suno | LUFS Strudel | Compases Suno / Strudel | Faltan / sobran | Croma | Notas F1 | Ritmo | Timbre (dB) | Nivel en mezcla | Dinámica | Paneo | Anchura | Relleno |',
          '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|']
    f = lambda v, fmt: '–' if v is None else format(v, fmt)
    for n, r in res_todas.items():
        s = r['resumen']
        L.append(f"| {n} | {r['lufs_s']} | {r['lufs_r']} | {s['compases_suno']} / {s['compases_strudel']} | {s['faltan']} / {s['sobran']} | "
                 f"{f(s['croma'], '.2f')} | {f(s['f1_clase'], '.2f')} | {f(s['ritmo'], '.2f')} | {f(s['timbre_db'], '.1f')} | "
                 f"{f(s['nivel_db'], '+.1f')} dB | ±{f(s['dinamica_abs_db'], '.1f')} dB | {f(s['paneo_db'], '+.1f')} | {f(s['anchura_db'], '+.1f')} | {f(s['relleno_db'], '+.1f')} |")
    L += ['', 'Croma y notas: 1 = iguales. Ritmo: 1 = mismo perfil de ataques. Timbre: diferencia media de la forma del espectro. '
          'Nivel, paneo, anchura y relleno: Strudel menos Suno (relleno negativo = más seco).', '',
          '## Ecualización: Strudel frente a Suno', '', '| Pista | ' + ' | '.join(f'{b} Hz' for b in BANDAS) + ' |', '|---|' + '---|' * len(BANDAS)]
    for n, r in res_todas.items():
        if r['eq']:
            L.append(f'| {n} | ' + ' | '.join(f(r['eq'][str(b)], '+.1f') for b in BANDAS) + ' |')
    L += ['', 'Positivo: Strudel tiene más energía relativa en esa octava (habría que recortarla).', '']
    L += ['## Por sección', '']
    for n, r in res_todas.items():
        fila = []
        for nombre, a, b in secs:
            cs = [c for c in r['compases'][a:b] if c['activo_s'] and c['activo_r']]
            fal = sum(c['activo_s'] and not c['activo_r'] for c in r['compases'][a:b])
            sob = sum(c['activo_r'] and not c['activo_s'] for c in r['compases'][a:b])
            if not cs:
                fila.append(f'{nombre}: ' + ('falta' if fal else 'sobra' if sob else '—'))
                continue
            dn = media([c['r']['rel'] - c['s']['rel'] for c in cs])
            cr = media([c.get('croma') for c in cs]); ri = media([c.get('ritmo') for c in cs]); tb = media([c.get('timbre_db') for c in cs])
            fila.append(f"{nombre}: nivel {dn:+.1f}" + (f' · croma {cr:.2f}' if cr is not None else '') +
                        (f' · ritmo {ri:.2f}' if ri is not None else '') + f' · timbre {tb:.1f}' +
                        (f' · faltan {fal}' if fal else '') + (f' · sobran {sob}' if sob else ''))
        L.append(f'- **{n}**: ' + ' — '.join(fila))
    if base:
        L += ['', f'## Cambios respecto a `{args.base}`', '',
              '| Pista | Croma | Notas F1 | Ritmo | Timbre (dB) | Nivel abs (dB) | Dinámica (dB) | Faltan / sobran | Puntos |', '|---|---|---|---|---|---|---|---|---|']
        for n, r in res_todas.items():
            if n not in base['pistas']:
                continue
            a, b = base['pistas'][n]['resumen'], r['resumen']
            pa = sum(p['puntos'] for p in base['problemas'] if p['pista'] == n)
            pb = sum(p['puntos'] for p in probs if p['pista'] == n)

            def d(q, mejor_alto, fmt='.2f'):
                if a.get(q) is None or b.get(q) is None:
                    return '–'
                delta = b[q] - a[q]
                peor = (delta < -0.02) if mejor_alto else (delta > 0.3)
                mejor = (delta > 0.02) if mejor_alto else (delta < -0.3)
                return f"{format(a[q], fmt)} → {format(b[q], fmt)}" + (' ⚠' if peor else ' ✓' if mejor else '')
            L.append(f"| {n} | {d('croma', True)} | {d('f1_clase', True)} | {d('ritmo', True)} | {d('timbre_db', False, '.1f')} | "
                     f"{d('nivel_abs_db', False, '.1f')} | {d('dinamica_abs_db', False, '.1f')} | {a['faltan']}/{a['sobran']} → {b['faltan']}/{b['sobran']} | "
                     f"{pa:.2f} → {pb:.2f}{' ⚠' if pb > pa * 1.1 + 0.02 else ' ✓' if pb < pa * 0.9 else ''} |")
        L += ['', '⚠ = empeora (posible regresión) · ✓ = mejora.']
    L += ['', '## Cómo leer la confianza', '',
          '- **Alta (≥ 0,7)**: nivel en la mezcla y partes que faltan o sobran; se miden directamente sobre el audio.',
          '- **Media**: notas (croma y Basic Pitch coinciden), ritmo y dinámica. Bajan si el alineado del compás es dudoso o si la pista de Suno es muy floja (más restos de otras pistas).',
          '- **Baja (< 0,5)**: efectos (reverb) y anchura, que se estiman de forma indirecta; y cualquier medida en pistas de Suno a menos de −25 dB de la mezcla.',
          '- Las pistas de Suno salen de separar la mezcla: llevan algo de las demás, sobre todo las flojas. Basic Pitch añade armónicos (octavas, quintas).', '']
    return '\n'.join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pistas'); ap.add_argument('analisis'); ap.add_argument('renders'); ap.add_argument('salida')
    ap.add_argument('--grupos', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'grupos-11.json'))
    ap.add_argument('--secciones', default='intro:8,A:16,B:16,B2:16,parón:8,final:8,cierre:5')
    ap.add_argument('--base'); ap.add_argument('--bp'); ap.add_argument('--amp', type=float, default=0.3)
    ap.add_argument('--solo', help='solo estas pistas (separadas por comas); el resto se copia de --base si se da')
    args = ap.parse_args()
    os.makedirs(args.salida, exist_ok=True)
    grupos = {k: v for k, v in json.load(open(args.grupos, encoding='utf-8')).items() if not k.startswith('_')}
    meta = F.meta_render(args.renders)
    B, barSec = meta['bars'], meta['barSec']
    secs = secciones(args.secciones, B)
    R = np.arange(B + 1) * barSec
    rej = rejilla(args.analisis)
    S0 = rej['inicio'] + np.arange(B + 1) * rej['compas']
    rutas = pistas(args.pistas)
    base = json.load(open(args.base, encoding='utf-8')) if args.base else None

    # Mezclas: Suno = suma de sus pistas; Strudel = suma de las capas (lo mismo que la pieza entera, porque todo es
    # lineal, y así una versión solo necesita renderizar las capas que cambian)
    n = int((S0[-1] + 2) * F.SR)
    mez_s = None
    for nombre, ruta in rutas.items():
        x = F.a_largo(F.carga(ruta), n)
        mez_s = x if mez_s is None else mez_s + x
    mez_r, _, _ = F.render(args.renders, [t for v in grupos.values() for t in v])
    print('alineando…', flush=True)
    env_s, env_r = F.envolvente_alineado(F.mono_f(mez_s)), F.envolvente_alineado(F.mono_f(mez_r))
    S, des, corr = F.alinea(env_s, env_r, S0, R, max_lag=0.9)
    alin = {'inicios_suno': [round(float(v), 4) for v in S], 'inicios_strudel': [round(float(v), 4) for v in R],
            'tempo_suno': [round(240 / float(S[k + 1] - S[k]), 2) for k in range(B)],
            'desfase_ms': [round(float(v) * 1000, 1) for v in des], 'correlacion': [round(float(v), 3) for v in corr]}
    print(f'  desfase {des.min() * 1000:+.0f}…{des.max() * 1000:+.0f} ms · correlación media {corr.mean():.2f}', flush=True)
    Ts, Tr = F.Tramos(mez_s), F.Tramos(mez_r)
    lm_s = [Ts.mide(S[k], S[k + 1])['lufs'] for k in range(B)]
    lm_r = [Tr.mide(R[k], R[k + 1])['lufs'] for k in range(B)]
    res_todas = {'mezcla': compara('mezcla', mez_s, mez_r, [], None, S, R, B, lm_s, lm_r, corr)}
    del Ts, Tr, mez_s, mez_r

    solo = set(x.strip() for x in args.solo.split(',')) if args.solo else None
    for nombre, tags in grupos.items():
        if nombre not in rutas:
            continue
        if solo and nombre not in solo and base and nombre in base['pistas']:
            res_todas[nombre] = base['pistas'][nombre]
            continue
        print(f'{nombre}…', flush=True)
        xs = F.carga(rutas[nombre])
        xr, notas_r = None, []
        if tags:
            xr, notas_r, _ = F.render(args.renders, tags)
        bp = F.notas_bp(os.path.join(args.bp or args.analisis, f'bp_{nombre.replace(" ", "_")}.csv'), args.amp)
        res = compara(nombre, xs, xr, notas_r, bp, S, R, B, lm_s, lm_r, corr)
        res_todas[nombre] = res
        del xs, xr
    for n, r in res_todas.items():
        r['resumen'] = resumen(r)
    probs = sorted([p for n, r in res_todas.items() if n != 'mezcla' for p in problemas(n, r, secs)] +
                   [p for p in problemas('mezcla', res_todas['mezcla'], secs) if p['familia'] == 'producción'],
                   key=lambda p: -p['puntos'])
    datos = {'renders': args.renders, 'meta': meta, 'secciones': secs, 'alineado': alin, 'pistas': res_todas, 'problemas': probs}
    with open(os.path.join(args.salida, 'comparacion.json'), 'w', encoding='utf-8') as fh:
        json.dump(datos, fh, ensure_ascii=False)
    with open(os.path.join(args.salida, 'informe.md'), 'w', encoding='utf-8') as fh:
        fh.write(informe(res_todas, probs, secs, args, alin, base))
    figura(res_todas, secs, os.path.join(args.salida, 'errores.png'))
    print(f'{len(probs)} problemas · informe en {os.path.join(args.salida, "informe.md")}')
    for p in probs[:15]:
        print(f"  {p['puntos']:.3f}  {p['pista']:<10} {p['tipo']:<9} {p['compases'][0]:>2}–{p['compases'][1]:<2} {p['evidencia']}")


if __name__ == '__main__':
    main()
