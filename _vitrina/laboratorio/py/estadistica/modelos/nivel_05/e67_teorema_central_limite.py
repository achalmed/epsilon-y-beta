"""simuladores/estadistica/modelos/nivel_05/e67_teorema_central_limite.py — el teorema central del límite (sección V, tema 67).

La «estrella» del currículo de estadística: aunque la población NO sea normal, la distribución de la media muestral
X̄ se acerca a una normal N(μ, σ²/n) al crecer n. El modelo parte de una población gamma de media 1 cuya asimetría se
regula con la forma k (k = 1 es la exponencial; k pequeño, muy sesgada; k grande, casi simétrica), simula muchas
muestras de tamaño n, dibuja el histograma de sus medias contra la normal teórica y mide cuánto se parecen (distancia
de Kolmogórov). La misma lógica que anima `animaciones/e67_tcl.py` (población exponencial, semilla fija), ahora como
modelo con parámetros, escenarios y los teoremas como verificaciones.
"""

import math

import numpy as np

from base import Ecuacion, Escenario, Ficha, Modelo, Parametro, Verificacion
import config

_SEMILLA = 42                     # aleatoriedad reproducible (regla del laboratorio)
_MU = 1.0                         # media de la población gamma(k, 1/k): siempre 1


def _medias(n, k, reps, semilla=_SEMILLA):
    """reps medias muestrales de tamaño n de una población gamma de forma k y media 1 (escala 1/k)."""
    rng = np.random.default_rng(semilla)
    return rng.gamma(shape=k, scale=1.0 / k, size=(int(reps), int(n))).mean(axis=1)


def _sigma(k):
    """Desviación estándar de la población gamma(k, 1/k): √k · (1/k) = 1/√k."""
    return 1.0 / math.sqrt(k)


def _densidad_poblacion(x, k):
    """Densidad gamma(k, escala 1/k), por logaritmos (estable para k grande)."""
    x = np.asarray(x, float)
    logf = k * math.log(k) - math.lgamma(k) + (k - 1) * np.log(x) - k * x
    return np.exp(logf)


def _densidad_normal(x, mu, sd):
    return np.exp(-0.5 * ((x - mu) / sd) ** 2) / (sd * math.sqrt(2 * math.pi))


_ERF = np.frompyfunc(math.erf, 1, 1)


def _distancia_ks(medias, mu, sd):
    """Distancia de Kolmogórov entre la distribución empírica de X̄ y la normal N(mu, sd²)."""
    x = np.sort(medias)
    m = len(x)
    phi = 0.5 * (1.0 + _ERF((x - mu) / (sd * math.sqrt(2))).astype(float))
    arriba = np.arange(1, m + 1) / m - phi
    abajo = phi - np.arange(0, m) / m
    return float(max(arriba.max(), abajo.max()))


def _asimetria(v):
    v = np.asarray(v, float)
    d = v - v.mean()
    return float(np.mean(d ** 3) / np.mean(d ** 2) ** 1.5)


def _curvas(p):
    n, k, reps = int(p["n"]), float(p["k"]), int(p["reps"])
    medias = _medias(n, k, reps)
    se = _sigma(k) / math.sqrt(n)
    # histograma de X̄ como contorno escalonado (densidad), sobre μ ± 4.5 errores estándar
    lo, hi = max(1e-6, _MU - 4.5 * se), _MU + 4.5 * se
    dens, bordes = np.histogram(medias, bins=40, range=(lo, hi), density=True)
    xs = np.repeat(bordes, 2)[1:-1]
    ys = np.repeat(dens, 2)
    xn = np.linspace(lo, hi, 200)
    yn = _densidad_normal(xn, _MU, se)
    # la población, en su rango útil; su densidad se recorta al alto de la figura (con k < 1 tiende a infinito en 0)
    x_max = max(3.0, _MU + 3.5 * _sigma(k))
    xp = np.linspace(x_max / 400, x_max, 300)
    tope = 1.15 * max(float(yn.max()), float(dens.max()))
    yp = np.minimum(_densidad_poblacion(xp, k), tope)
    ks = _distancia_ks(medias, _MU, se)
    return {"lineas": {"población (gamma, media 1)": (xp, yp, config.VERDE),
                       "$\\bar X$ simulada (histograma)": (xs, ys, config.AZUL2),
                       "normal teórica $N(\\mu, \\sigma^2/n)$": (xn, yn, config.ROJO)},
            "puntos": [(_MU, float(yn.max()), f"μ = 1, σ/√n = {se:.3f}")],
            "anotacion": (f"{reps} muestras de tamaño n = {n} de una población gamma (k = {k:g})\n"
                          f"asimetría: población {2 / math.sqrt(k):.2f} → X̄ {_asimetria(medias):.2f}\n"
                          f"distancia a la normal (Kolmogórov): {ks:.3f}")}


def _resultados(p):
    n, k, reps = int(p["n"]), float(p["k"]), int(p["reps"])
    medias = _medias(n, k, reps)
    se = _sigma(k) / math.sqrt(n)
    return {"tamaño de muestra n": float(n),
            "media de X̄ (simulada)": float(medias.mean()),
            "μ de la población": _MU,
            "desviación de X̄ (simulada)": float(medias.std(ddof=1)),
            "error estándar σ/√n": se,
            "asimetría de la población 2/√k": 2 / math.sqrt(k),
            "asimetría de X̄ (simulada)": _asimetria(medias),
            "asimetría de X̄ teórica 2/√(kn)": 2 / math.sqrt(k * n),
            "distancia a la normal (Kolmogórov)": _distancia_ks(medias, _MU, se)}


def _ecuaciones_calibradas(p):
    n, k = int(p["n"]), float(p["k"])
    se = _sigma(k) / math.sqrt(n)
    return [f"\\bar X = \\frac{{1}}{{{n}}}\\sum_{{i=1}}^{{{n}}} X_i,\\quad X_i \\sim \\text{{Gamma}}(k{{=}}{k:g},\\ \\text{{media }} 1)",
            f"\\bar X \\;\\dot\\sim\\; N\\!\\left(1,\\ \\frac{{{_sigma(k) ** 2:.3f}}}{{{n}}}\\right),\\quad \\sigma_{{\\bar X}} = {se:.3f}"]


_P0 = {"n": 5, "k": 1.0, "reps": 4000}


def _v_insesgada():
    m = _medias(10, 1.0, 20000, semilla=1)
    return abs(m.mean() - _MU) < 0.01, \
        (f"E[X̄] = μ: la media de 20000 medias muestrales (n = 10, población exponencial) es {m.mean():.4f} ≈ μ = 1 — "
         "la media muestral no se equivoca en promedio, sea cual sea la forma de la población")


def _v_error_estandar():
    m = _medias(25, 1.0, 20000, semilla=2)
    teorica = _sigma(1.0) / math.sqrt(25)
    razon = m.std(ddof=1) / teorica
    return abs(razon - 1) < 0.03, \
        (f"Var(X̄) = σ²/n: con n = 25 la desviación de X̄ es {m.std(ddof=1):.4f} y σ/√n = {teorica:.4f} "
         f"(razón {razon:.3f}) — la dispersión de la media cae con la raíz de n")


def _v_asimetria_raiz_n():
    s4 = _asimetria(_medias(4, 1.0, 40000, semilla=3))
    s64 = _asimetria(_medias(64, 1.0, 40000, semilla=4))
    razon = s4 / s64
    return 3.0 < razon < 5.2, \
        (f"la asimetría de X̄ decrece como 1/√n (teoría 2/√n): n = 4 → {s4:.3f}; n = 64 → {s64:.3f}; "
         f"razón {razon:.2f} ≈ √16 = 4 — por eso la forma de la media se «normaliza» al crecer n")


def _v_converge_a_normal():
    def ks(n, semilla):
        m = _medias(n, 1.0, 20000, semilla=semilla)
        return _distancia_ks(m, _MU, _sigma(1.0) / math.sqrt(n))
    d1, d5, d50 = ks(1, 5), ks(5, 6), ks(50, 7)
    return d1 > d5 > d50 and d50 < 0.03, \
        (f"TCL: la distancia de Kolmogórov entre X̄ y su normal cae al crecer n: n = 1 → {d1:.3f}, n = 5 → {d5:.3f}, "
         f"n = 50 → {d50:.3f} — partiendo de una población exponencial, nada normal")


def _v_forma_importa():
    def ks(k, semilla):
        m = _medias(30, k, 20000, semilla=semilla)
        return _distancia_ks(m, _MU, _sigma(k) / math.sqrt(30))
    sesgada, simetrica = ks(0.2, 8), ks(10.0, 9)
    return sesgada > simetrica, \
        (f"la «regla de n ≥ 30» no es ley: con n = 30, una población muy sesgada (k = 0.2) deja X̄ a {sesgada:.3f} de la "
         f"normal y una casi simétrica (k = 10), a {simetrica:.3f} — la velocidad del TCL depende de la forma de la población")


MODELO = Modelo(
    id="e67", nivel=5,
    nombre="El teorema central del límite",
    xlabel="valor", ylabel="densidad",
    parametros=[
        Parametro("n", _P0["n"], 1, 100, 1, "Tamaño de cada muestra n", grupo="muestreo",
                  definicion="cuántas observaciones promedia cada muestra; con n = 1, X̄ es la población misma"),
        Parametro("k", _P0["k"], 0.2, 10, 0.1, "Forma de la población k", grupo="población",
                  definicion="gamma de media 1: k = 1 es la exponencial; k pequeño, muy sesgada; k grande, casi simétrica"),
        Parametro("reps", _P0["reps"], 500, 8000, 500, "Muestras simuladas", grupo="simulación",
                  definicion="cuántas medias se simulan para dibujar su distribución (más, histograma más liso)"),
    ],
    curvas=_curvas,
    resultados=_resultados,
    ecuaciones_calibradas=_ecuaciones_calibradas,
    ficha=Ficha(
        pregunta=("Si la población no es normal, ¿por qué la media de una muestra sí termina pareciéndose a una normal, "
                  "y cuán grande tiene que ser la muestra para que eso sea verdad?"),
        variables=[("X_i", "observaciones independientes de una población con media μ y varianza σ² finita"),
                   ("\\bar X", "media muestral de n observaciones"),
                   ("n", "tamaño de la muestra"),
                   ("k", "forma de la población gamma (regula su asimetría 2/√k)")],
        derivacion=["E[\\bar X] = \\frac{1}{n}\\sum E[X_i] = \\mu",
                    "\\operatorname{Var}(\\bar X) = \\frac{1}{n^2}\\sum \\operatorname{Var}(X_i) = \\frac{\\sigma^2}{n}",
                    "Z_n = \\frac{\\bar X - \\mu}{\\sigma/\\sqrt{n}}",
                    "Z_n \\xrightarrow{d} N(0,1) \\quad (n \\to \\infty)",
                    "\\text{asimetría}(\\bar X) = \\frac{\\text{asimetría}(X)}{\\sqrt{n}}"],
        contexto=("Abraham de Moivre descubrió en 1733 que el número de caras en muchos lanzamientos de una moneda se "
                  "distribuye según una curva en forma de campana; Pierre-Simon Laplace lo generalizó en 1810 a sumas de "
                  "variables cualesquiera, y la prueba rigurosa llegó con Lyapunov (1901) y Lindeberg (1922). El "
                  "resultado explica por qué la normal aparece en todas partes: muchas magnitudes son sumas o promedios "
                  "de muchos efectos pequeños e independientes. En la práctica es el teorema que sostiene casi toda la "
                  "inferencia clásica: los intervalos de confianza y las pruebas sobre una media usan la normal aunque "
                  "nadie sepa la forma de la población, porque lo que se distribuye como normal es la media, no los "
                  "datos. El modelo lo pone a prueba con una población deliberadamente asimétrica (una gamma, como el "
                  "ingreso o el tiempo de espera) y deja ver cuánto tarda la media en «olvidar» esa forma."),
        autores=("De Moivre (1733), Laplace (1810), Lyapunov (1901), Lindeberg (1922) — menciones. Conocimiento "
                 "estadístico general."),
        supuestos=[
            "Observaciones independientes e idénticamente distribuidas (muestreo aleatorio con reposición o población grande).",
            "La población tiene varianza finita: sin ella (Cauchy, colas muy pesadas) el teorema no se cumple.",
            "El resultado es asintótico: dice a dónde va la distribución de X̄ cuando n crece, no cuán cerca está con un n dado.",
            "La población del modelo es una gamma de media 1 y varianza 1/k: la forma k controla su asimetría (2/√k).",
        ],
        ecuaciones=[
            Ecuacion("E[\\bar X] = \\mu, \\quad \\operatorname{Var}(\\bar X) = \\frac{\\sigma^2}{n}", "momentos de la media",
                     "valen para cualquier población con varianza finita y cualquier n: la media muestral está centrada "
                     "en μ y su dispersión cae con la raíz de n (el error estándar σ/√n)."),
            Ecuacion("\\frac{\\bar X - \\mu}{\\sigma/\\sqrt{n}} \\xrightarrow{d} N(0, 1)", "teorema central del límite",
                     "la media tipificada converge en distribución a la normal estándar, sea cual sea la forma de la "
                     "población: la campana es un destino, no un supuesto."),
            Ecuacion("\\text{asimetría}(\\bar X) = \\frac{2}{\\sqrt{k\\,n}}", "velocidad de convergencia",
                     "en la población gamma la asimetría de X̄ es la de la población dividida por √n: cuanto más sesgada "
                     "la población, más grande tiene que ser n para que la normal sea una buena aproximación."),
        ],
        intuicion=("Al promediar, los valores extremos de un lado se compensan con los del otro: la media de muchas "
                   "observaciones casi nunca es extrema aunque cada observación pueda serlo. Esa compensación borra "
                   "poco a poco la forma de la población —su asimetría se divide por √n— y lo que queda es la campana. "
                   "Por eso una encuestadora puede dar un margen de error con la normal sin conocer la distribución del "
                   "ingreso: lo que se comporta como normal es el promedio de la muestra. Pero el teorema no regala "
                   "nada: con una población muy sesgada la media tarda en normalizarse, y la famosa «regla de n ≥ 30» "
                   "puede quedarse corta."),
        equilibrio=("La distribución de X̄ tiene media μ y desviación σ/√n para todo n; su forma converge a la normal "
                    "cuando n → ∞, y la distancia a la normal cae con la asimetría de la población dividida por √n."),
        limitaciones=[
            "Es asintótico: no dice qué n basta; con poblaciones muy asimétricas o con colas pesadas hacen falta muestras grandes, y la «regla de 30» es solo una costumbre.",
            "Exige independencia y varianza finita: con datos dependientes (series de tiempo, conglomerados) o colas muy pesadas, la normal de X̄ falla o necesita otra versión del teorema.",
            "Habla de la media (o de sumas), no de los datos: la población sigue siendo asimétrica aunque X̄ sea casi normal.",
            "La simulación usa un número finito de muestras: el histograma tiene ruido propio, que baja con más muestras simuladas.",
        ],
        evolucion=("Parte de la ley de los grandes números (e64: X̄ → μ) y le añade la forma de la fluctuación alrededor "
                   "de μ. Funda el error estándar (e89), los intervalos de confianza (e92) y las pruebas sobre medias "
                   "(sección VIII); el bootstrap (e174) es la salida cuando la aproximación normal no es fiable."),
    ),
    escenarios=[
        Escenario("poblacion", "n = 1: la media de una sola observación es la población",
                  {"n": 1},
                  "con n = 1 no hay nada que promediar: el histograma de X̄ reproduce la población exponencial, "
                  "asimétrica y lejos de la normal teórica. Es el punto de partida del teorema.",
                  cadena=["n = 1", "X̄ = X", "la distribución de X̄ es la de la población",
                          "asimetría 2: muy lejos de la normal"]),
        Escenario("n_30", "n = 30: la «regla de 30» con una población exponencial",
                  {"n": 30},
                  "con 30 observaciones la media ya casi no conserva la asimetría de la población (2/√30 ≈ 0,37): "
                  "el histograma se pega a la normal teórica y la distancia de Kolmogórov es pequeña.",
                  cadena=["↑n a 30", "los extremos se compensan al promediar", "asimetría de X̄ = 2/√30 ≈ 0,37",
                          "X̄ casi normal, centrada en μ con σ/√n"]),
        Escenario("muy_sesgada", "población muy sesgada (k = 0,2) con n = 30",
                  {"n": 30, "k": 0.2},
                  "la misma n = 30 no basta cuando la población es muy asimétrica (asimetría 4,5): la media conserva "
                  "una cola larga a la derecha (2/√6 ≈ 0,82). La regla de 30 es una costumbre, no un teorema.",
                  cadena=["↓k a 0,2", "población con asimetría 2/√0,2 ≈ 4,5", "con n = 30, X̄ conserva 0,82",
                          "la normal aún no es buena aproximación"]),
        Escenario("casi_simetrica", "población casi simétrica (k = 10) con n = 5",
                  {"n": 5, "k": 10.0},
                  "si la población ya es casi simétrica, cinco observaciones bastan: la asimetría de X̄ es 2/√50 ≈ 0,28 "
                  "y el histograma coincide con la normal. El TCL trabaja rápido cuando tiene poco que corregir.",
                  cadena=["↑k a 10", "población casi simétrica (0,63)", "con n = 5, X̄ queda en 0,28",
                          "X̄ casi normal con muestras pequeñas"]),
    ],
    verificaciones=[
        Verificacion("E[X̄] = μ (la media muestral es insesgada)", _v_insesgada),
        Verificacion("Var(X̄) = σ²/n (error estándar σ/√n)", _v_error_estandar),
        Verificacion("la asimetría de X̄ decrece como 1/√n", _v_asimetria_raiz_n),
        Verificacion("TCL: X̄ converge a la normal partiendo de una población no normal", _v_converge_a_normal),
        Verificacion("la velocidad de convergencia depende de la forma de la población", _v_forma_importa),
    ],
    notas=("TCL: (X̄−μ)/(σ/√n) → N(0,1) para cualquier población con varianza finita. Población gamma de media 1 y "
           "forma k (asimetría 2/√k); la asimetría de X̄ es 2/√(kn). Mide la distancia de Kolmogórov a la normal. La "
           "regla de n ≥ 30 depende de la forma de la población."),
)
