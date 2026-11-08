# Comparación de una pieza de Strudel con las pistas de Suno: carga, alineado, sonoridad y métricas por compás.
# Lo usan 06_comparar.py (informe) y 07_ab.py (escucha A/B).
import os, sys, json, glob
import numpy as np
import soundfile as sf
from scipy.signal import lfilter

SR = 48000          # las pistas de Suno y los renders de render.html van a 48 kHz
SR_F = 22050        # para croma, mel y ataques
HOP_F = 256         # ~11,6 ms a 22 050 Hz
HOP_A = 128         # ~5,8 ms: envolvente de ataques para alinear


# ── Audio ──

def carga(ruta, escala=1.0):
    x, sr = sf.read(ruta, dtype='float32', always_2d=True)
    x = x.T / escala
    if x.shape[0] == 1:
        x = np.vstack([x, x])
    if sr != SR:
        import librosa
        x = librosa.resample(x, orig_sr=sr, target_sr=SR)
    return np.ascontiguousarray(x[:2])


def a_largo(x, n):
    return x[:, :n] if x.shape[1] >= n else np.pad(x, ((0, 0), (0, n - x.shape[1])))


def mono_f(x):
    import librosa
    return librosa.resample(x.mean(axis=0), orig_sr=SR, target_sr=SR_F, res_type='soxr_hq')


# ── Renders de render.html ──

def capa(carpeta, tag, ext='.wav'):
    """Ruta de una capa renderizada. Una versión solo guarda las capas que cambian: si falta, se busca en la versión
    de la que hereda (hereda.json: {"de": "../v0"})."""
    d = carpeta
    for _ in range(30):
        p = os.path.join(d, tag + ext)
        if os.path.exists(p):
            return p
        h = os.path.join(d, 'hereda.json')
        if not os.path.exists(h):
            break
        d = os.path.normpath(os.path.join(d, json.load(open(h, encoding='utf-8'))['de']))
    sys.exit(f'No encuentro la capa «{tag}» en {carpeta} ni en las versiones de las que hereda')


def render(carpeta, tags):
    """Suma las capas renderizadas (<carpeta>/<tag>.wav) y junta sus notas. Devuelve (audio, notas, meta)."""
    total, notas, meta = None, [], None
    for t in tags:
        m = json.load(open(capa(carpeta, t, '.json'), encoding='utf-8'))
        x = carga(capa(carpeta, t), m['escala'])
        total = x if total is None else _suma(total, x)
        notas += m['notas']
        meta = meta or m
    return total, notas, meta


def _suma(a, b):
    n = max(a.shape[1], b.shape[1])
    return a_largo(a, n) + a_largo(b, n)


def meta_render(carpeta):
    d = carpeta
    for _ in range(30):
        for f in sorted(glob.glob(os.path.join(d, '*.json'))):
            m = json.load(open(f, encoding='utf-8'))
            if 'barSec' in m:
                return {k: v for k, v in m.items() if k != 'notas'}
        h = os.path.join(d, 'hereda.json')
        if not os.path.exists(h):
            break
        d = os.path.normpath(os.path.join(d, json.load(open(h, encoding='utf-8'))['de']))
    sys.exit(f'No hay renders de render.html en {carpeta}')


# ── Sonoridad (ITU-R BS.1770, filtro K a 48 kHz) ──

_SHELF = ([1.53512485958697, -2.69169618940638, 1.19839281085285], [1.0, -1.69065929318241, 0.73248077421585])
_HPF = ([1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621])


def filtro_k(x):
    return lfilter(*_HPF, lfilter(*_SHELF, x, axis=-1), axis=-1).astype(np.float32)


def lufs_integrado(xk):
    """Sonoridad integrada con las dos puertas (−70 LUFS y −10 LU) sobre audio ya filtrado con filtro_k"""
    blq, paso = int(0.4 * SR), int(0.1 * SR)
    p = (xk.astype(np.float64) ** 2).sum(axis=0)
    c = np.concatenate([[0], np.cumsum(p)])
    ini = np.arange(0, max(1, len(p) - blq + 1), paso)
    ms = (c[np.minimum(ini + blq, len(p))] - c[ini]) / blq
    l = -0.691 + 10 * np.log10(ms + 1e-12)
    l = l[l > -70]
    if not len(l):
        return -120.0
    rel = -0.691 + 10 * np.log10(np.mean(10 ** ((l + 0.691) / 10))) - 10
    l = l[l > rel]
    return float(-0.691 + 10 * np.log10(np.mean(10 ** ((l + 0.691) / 10))))


class Tramos:
    """Sumas acumuladas para medir trozos (compases) deprisa: sonoridad, paneo, anchura y correlación L/R"""

    def __init__(self, x):
        xk = filtro_k(x).astype(np.float64)
        self.xk = xk
        L, R = xk
        cs = lambda v: np.concatenate([[0], np.cumsum(v)])
        self.l2, self.r2, self.lr = cs(L * L), cs(R * R), cs(L * R)

    def mide(self, t0, t1):
        a, b = max(0, int(t0 * SR)), max(1, int(t1 * SR))
        b = min(b, len(self.l2) - 1)
        n = max(1, b - a)
        l2, r2, lr = (self.l2[b] - self.l2[a]) / n, (self.r2[b] - self.r2[a]) / n, (self.lr[b] - self.lr[a]) / n
        ms = l2 + r2
        mid, side = (l2 + r2 + 2 * lr) / 4, (l2 + r2 - 2 * lr) / 4
        return {
            'lufs': float(-0.691 + 10 * np.log10(ms + 1e-12)),
            'pan_db': float(10 * np.log10((l2 + 1e-12) / (r2 + 1e-12))),       # + = más a la izquierda
            'anchura_db': float(10 * np.log10((side + 1e-12) / (mid + 1e-12))),  # lado frente a centro
            'icc': float(lr / np.sqrt(l2 * r2 + 1e-24)),
        }

    def envolvente(self, t0, t1, hop=512):
        """Nivel (dB) de cada ventana de ~10 ms dentro del trozo: para el relleno entre golpes y la pegada"""
        a, b = int(t0 * SR), int(t1 * SR)
        p = (self.xk[:, a:b] ** 2).sum(axis=0)
        n = len(p) // hop
        if n < 4:
            return None
        return 10 * np.log10(p[:n * hop].reshape(n, hop).mean(axis=1) + 1e-12)


# ── Rasgos espectrales (mono a 22 050 Hz) ──

class Rasgos:
    def __init__(self, y, croma=True):
        import librosa
        self.n = len(y)
        S = np.abs(librosa.stft(y, n_fft=2048, hop_length=HOP_F)) ** 2
        self.mel = librosa.feature.melspectrogram(S=S, sr=SR_F, n_mels=64, fmin=30, fmax=11000)
        self.mel_f = librosa.mel_frequencies(n_mels=64, fmin=30, fmax=11000)
        self.cent = librosa.feature.spectral_centroid(S=np.sqrt(S), sr=SR_F)[0]
        self.pot = S.sum(axis=0)
        del S
        # ataques en tres bandas (grave < 150 Hz, medio, agudo > 5 kHz) y en total, con el mismo paso que el mel
        lm = librosa.power_to_db(self.mel, ref=np.max)
        b1 = int(np.searchsorted(self.mel_f, 150)); b2 = int(np.searchsorted(self.mel_f, 5000))
        self.ataques = librosa.onset.onset_strength_multi(S=lm, sr=SR_F, hop_length=HOP_F, channels=[0, b1, b2, 64])
        self.ataque = librosa.onset.onset_strength(S=lm, sr=SR_F, hop_length=HOP_F)
        self.croma = None
        if croma:
            C = np.abs(librosa.cqt(y, sr=SR_F, hop_length=512, fmin=librosa.note_to_hz('C1'), n_bins=84 * 3,
                                   bins_per_octave=36)) ** 2
            self.croma = librosa.feature.chroma_cqt(C=np.sqrt(C), sr=SR_F, hop_length=512, bins_per_octave=36,
                                                    n_chroma=12, norm=None)
            self.croma_hop = 512

    def fr(self, t, hop=HOP_F):
        return int(round(t * SR_F / hop))

    def mel_medio(self, t0, t1):
        a, b = self.fr(t0), max(self.fr(t0) + 1, self.fr(t1))
        return self.mel[:, a:b].mean(axis=1)

    def croma_tramo(self, t0, t1):
        a, b = self.fr(t0, self.croma_hop), max(self.fr(t0, self.croma_hop) + 1, self.fr(t1, self.croma_hop))
        return self.croma[:, a:b].sum(axis=1)

    def perfil(self, t0, t1, pasos=16, banda=None):
        """Ataques del compás doblados en «pasos» casillas (semicorcheas), cada casilla con su máximo"""
        env = self.ataque if banda is None else self.ataques[banda]
        a, b = self.fr(t0), self.fr(t1)
        seg = env[a:b]
        if len(seg) < pasos:
            return None
        bordes = np.linspace(0, len(seg), pasos + 1).astype(int)
        return np.array([seg[bordes[i]:max(bordes[i] + 1, bordes[i + 1])].max() for i in range(pasos)])


def envolvente_alineado(y):
    import librosa
    return librosa.onset.onset_strength(y=y, sr=SR_F, hop_length=HOP_A)


# ── Alineado compás a compás ──

def alinea(env_s, env_r, S0, R, max_lag=0.9, coste=0.025):
    """Desfase de cada compás de Suno respecto a la rejilla recta (S0), buscando la correlación de ataques con el
    render (compases R). Un Viterbi castiga los saltos entre compases vecinos (coste por paso de 5,8 ms): el desfase
    puede crecer poco a poco (el tempo de Suno se mueve: en «Quiet Beauty», ~0,6 s en 35 compases) pero no saltar
    una corchea, que es lo que haría una correlación compás a compás suelta.
    Devuelve (inicios de Suno, desfase de cada compás en s, correlación de cada compás)."""
    hop = HOP_A / SR_F
    L = int(round(max_lag / hop))
    lags = np.arange(-L, L + 1)
    B = len(R) - 1
    C = np.zeros((B, len(lags)))
    for k in range(B):
        r0, r1 = int(R[k] / hop), int(R[k + 1] / hop)
        sr_ = env_r[r0:r1]
        if len(sr_) < 8 or sr_.std() < 1e-6:
            continue
        sr_ = (sr_ - sr_.mean()) / sr_.std()
        s0 = int(round(S0[k] / hop))
        for j, lg in enumerate(lags):
            a = s0 + lg
            if a < 0 or a + len(sr_) > len(env_s):
                continue
            ss = env_s[a:a + len(sr_)]
            if ss.std() < 1e-6:
                continue
            C[k, j] = float(np.mean(sr_ * (ss - ss.mean()) / ss.std()))
    # Viterbi: maximiza la correlación con saltos caros
    pen = coste * np.abs(lags[:, None] - lags[None, :])
    acum = C[0].copy()
    atras = np.zeros((B, len(lags)), dtype=int)
    for k in range(1, B):
        tot = acum[:, None] - pen
        atras[k] = tot.argmax(axis=0)
        acum = tot.max(axis=0) + C[k]
    camino = np.zeros(B, dtype=int)
    camino[-1] = int(acum.argmax())
    for k in range(B - 1, 0, -1):
        camino[k - 1] = atras[k, camino[k]]
    des = lags[camino] * hop
    S = np.array(S0, dtype=float)
    S[:B] += des
    S[B] += des[-1]
    corr = C[np.arange(B), camino]
    return S, des, corr


# ── Notas ──

def notas_bp(ruta, amp=0.3):
    import csv
    if not os.path.exists(ruta):
        return None
    return [(float(r['start']), float(r['end']), int(r['pitch']), float(r['amp']))
            for r in csv.DictReader(open(ruta)) if float(r['amp']) >= amp]


def a_tiempo_suno(t, S, R):
    """Tiempo del render → tiempo de Suno, compás a compás"""
    k = int(np.clip(np.searchsorted(R, t, side='right') - 1, 0, len(R) - 2))
    return S[k] + (t - R[k]) * (S[k + 1] - S[k]) / (R[k + 1] - R[k])


def empareja(a, b, tol=0.08, clase=False):
    """Pares (tiempo, midi): cuántas notas de a encuentran pareja en b (ataque a menos de tol, misma nota o misma clase)"""
    usado = np.zeros(len(b), bool)
    hits = 0
    for t, p in sorted(a):
        mejor, md = -1, tol
        for j, (u, q) in enumerate(b):
            if usado[j] or abs(u - t) > md:
                continue
            if (p % 12 == q % 12) if clase else (p == q):
                mejor, md = j, abs(u - t)
        if mejor >= 0:
            usado[mejor] = True
            hits += 1
    return hits


def f1(r, s, tol=0.08, clase=False):
    if not r and not s:
        return None
    h = empareja(r, s, tol, clase)
    p = h / len(r) if r else 0.0
    q = h / len(s) if s else 0.0
    return 0.0 if p + q == 0 else 2 * p * q / (p + q)


def coseno(a, b):
    if a is None or b is None:
        return None
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na < 1e-9 or nb < 1e-9:
        return None
    return float(np.dot(a, b) / (na * nb))
