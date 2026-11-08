# Utilidades compartidas por los scripts de análisis (pistas de Suno, rejilla de compases, nombres de nota)
import os, re, sys, json

NOTAS = ['c', 'c#', 'd', 'eb', 'e', 'f', 'f#', 'g', 'ab', 'a', 'bb', 'b']


def nota(p):
    """Número MIDI → nombre de nota de Strudel (60 → c4)"""
    return NOTAS[p % 12] + str(p // 12 - 1)


def midi(texto):
    """«a4», «f#3», «eb5» o un número MIDI → número MIDI"""
    if str(texto).isdigit():
        return int(texto)
    m = re.match(r'^([a-g])([#b]?)(-?\d)$', texto.lower())
    if not m:
        sys.exit(f'No entiendo la nota «{texto}» (usa a4, f#3, eb5 o un número MIDI)')
    base = {'c': 0, 'd': 2, 'e': 4, 'f': 5, 'g': 7, 'a': 9, 'b': 11}[m.group(1)]
    return base + {'#': 1, 'b': -1, '': 0}[m.group(2)] + 12 * (int(m.group(3)) + 1)


def pistas(carpeta):
    """Pistas que exporta Suno («1 Drums.wav», «4 Keyboard.wav»…) → {nombre en minúsculas: ruta}, en orden de número"""
    out = []
    for f in os.listdir(carpeta):
        m = re.match(r'^(\d+)\s+(.+)\.wav$', f, re.I)
        if m:
            out.append((int(m.group(1)), m.group(2).lower(), os.path.join(carpeta, f)))
    if not out:
        sys.exit(f'No hay pistas de Suno («<número> <Nombre>.wav») en {carpeta}')
    return {nombre: ruta for _, nombre, ruta in sorted(out)}


def pista(carpeta, nombre):
    todas = pistas(carpeta)
    if nombre.lower() not in todas:
        sys.exit(f'No encuentro la pista «{nombre}» en {carpeta} (hay: {", ".join(todas)})')
    return todas[nombre.lower()]


def lista(texto):
    return [x.strip().lower() for x in texto.split(',') if x.strip()]


def rejilla(salida):
    p = os.path.join(salida, 'rejilla.json')
    if not os.path.exists(p):
        sys.exit(f'Falta {p}: ejecuta antes 02_rejilla.py')
    return json.load(open(p))


def compases(texto, total):
    """«3-10,15» → [3, 4, …, 10, 15]; vacío → todos los compases"""
    if not texto:
        return list(range(total))
    r = []
    for parte in texto.split(','):
        a, _, b = parte.partition('-')
        r += list(range(int(a), int(b or a) + 1))
    return r


def tramos(texto, total, largo=8):
    """«6-11,12-16» → [(6, 12), (12, 17)]; vacío → tramos de «largo» compases"""
    if not texto:
        return [(a, min(total, a + largo)) for a in range(0, total, largo)]
    out = []
    for parte in texto.split(','):
        a, _, b = parte.partition('-')
        out.append((int(a), int(b or a) + 1))
    return out


def guarda(salida, nombre, datos):
    with open(os.path.join(salida, nombre), 'w', encoding='utf-8') as fh:
        json.dump(datos, fh, ensure_ascii=False, indent=1)


def inicios(salida, comparacion=None):
    """Inicio de cada compás de Suno: los alineados con la pieza (comparacion.json de 06_comparar.py), que siguen el
    tempo real de Suno, o la rejilla recta de rejilla.json"""
    r = rejilla(salida)
    if comparacion:
        return json.load(open(comparacion, encoding='utf-8'))['alineado']['inicios_suno']
    return [r['inicio'] + k * r['compas'] for k in range(r['compases'] + 1)]


def en_rejilla(t, S, pasos=16):
    """Tiempo → (compás, paso redondeado) con compases de duración variable"""
    import bisect
    k = max(0, min(len(S) - 2, bisect.bisect_right(S, t) - 1))
    st = int(round((t - S[k]) / (S[k + 1] - S[k]) * pasos))
    return (k + 1, st - pasos) if st >= pasos else (k, st)
