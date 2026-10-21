"""simuladores/navegador.py — el adaptador que corre el mismo `base.Modelo` en el navegador (Pyodide) y lo serializa.

Objetivo: que la vitrina de los pubs (web/_aula) ejecute el modelo SIN reescribir sus ecuaciones en JavaScript: el
  navegador carga Pyodide y numpy, escribe en su sistema de archivos los .py mínimos (base.py, este módulo, el
  config.py de la disciplina y el módulo del modelo con sus auxiliares) e importa el MODELO como lo hace el escritorio.
Método: `preparar()` registra un matplotlib vacío (los config.py lo importan, pero solo lo usan para el estilo de las
  figuras de escritorio, que el navegador no dibuja); `calcular()` une los valores pedidos a los de por defecto,
  los ajusta al rango de cada Parametro, llama a `curvas` y `resultados` y devuelve un dict JSON estricto (sin numpy,
  sin NaN) con el contrato de dibujo de base.py: lineas, barras, puntos, equilibrio y anotacion. El mismo código
  escribe la vista inicial de navegador.json (`main.py web`), así que el escritorio, el exportador y el navegador
  serializan igual.
Uso (en Pyodide, desde web/_aula): import navegador; navegador.preparar(); navegador.calcular_json(MODELO, '{"G": 250}')
Límite: solo importa la biblioteca estándar; numpy llega con los datos que devuelve el modelo. No dibuja nada.
"""
from __future__ import annotations

import json
import math
import sys
import types
import warnings

CIFRAS = 6          # cifras significativas en el JSON: bastan para dibujar y aligeran la transferencia


def preparar(forzar: bool = False) -> None:
    """Registra un `matplotlib` mínimo si no está instalado (o si `forzar`): config.py lo importa para su estilo."""
    if not forzar and "matplotlib" in sys.modules:
        return
    if not forzar:
        try:
            import matplotlib  # noqa: F401  (en el escritorio existe y se usa el de verdad)
            return
        except ImportError:
            pass
    vacio = types.ModuleType("matplotlib")
    vacio.rcParams = {}
    vacio.__doc__ = "matplotlib vacío de simuladores/navegador.py: el navegador no dibuja con matplotlib"
    sys.modules["matplotlib"] = vacio


def _numero(v, cifras=CIFRAS):
    """float JSON: redondeado a `cifras` significativas; NaN e infinito pasan a None (JSON estricto)."""
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(f):
        return None
    return float(f"{f:.{cifras}g}")


def _lista(v, cifras=CIFRAS):
    if hasattr(v, "tolist"):
        v = v.tolist()
    if isinstance(v, (int, float)) or not hasattr(v, "__iter__"):
        return [_numero(v, cifras)]
    return [_numero(x, cifras) for x in v]


def _ralear(xs: list, ys: list, max_puntos: int | None) -> tuple[list, list]:
    """Toma `max_puntos` puntos a intervalos regulares (con el primero y el último); para la vista inicial guardada."""
    n = len(xs)
    if not max_puntos or n <= max_puntos:
        return xs, ys
    idx = sorted({round(i * (n - 1) / (max_puntos - 1)) for i in range(max_puntos)})
    return [xs[i] for i in idx], [ys[i] for i in idx]


def serializar(datos: dict, cifras: int = CIFRAS, max_puntos: int | None = None) -> dict:
    """El dict de `Modelo.curvas` (ver la cabecera de base.py) en JSON estricto, conservando el orden de las líneas."""
    salida = {}
    lineas = []
    for etiqueta, (x, y, color) in (datos.get("lineas") or {}).items():
        xs, ys = _lista(x, cifras), _lista(y, cifras)
        if len(xs) == 1 and len(ys) > 1:              # x escalar: línea vertical u horizontal declarada así
            xs = xs * len(ys)
        if len(ys) == 1 and len(xs) > 1:
            ys = ys * len(xs)
        xs, ys = _ralear(xs, ys, max_puntos)
        lineas.append({"etiqueta": str(etiqueta), "x": xs, "y": ys, "color": str(color)})
    if lineas:
        salida["lineas"] = lineas
    barras = datos.get("barras")
    if barras:
        cats, vals, cols = barras
        cols = [cols] * len(vals) if isinstance(cols, str) else list(cols)
        salida["barras"] = {"categorias": [str(c) for c in cats], "valores": _lista(vals, cifras),
                            "colores": [str(c) for c in cols]}
    puntos = [{"x": _numero(px, cifras), "y": _numero(py, cifras), "etiqueta": str(etq)}
              for (px, py, etq) in (datos.get("puntos") or [])]
    if puntos:
        salida["puntos"] = puntos
    eq = datos.get("equilibrio")
    if eq is not None:
        salida["equilibrio"] = {"x": _numero(eq[0], cifras), "y": _numero(eq[1], cifras)}
    if datos.get("anotacion"):
        salida["anotacion"] = str(datos["anotacion"])
    return salida


def valores(modelo, pedidos: dict | None = None) -> dict:
    """Los valores de por defecto del modelo con los `pedidos`, cada uno ajustado al rango de su Parametro."""
    p = modelo.dict_params()
    for nombre, v in (pedidos or {}).items():
        if nombre not in p:
            continue
        par = modelo.parametro(nombre)
        p[nombre] = min(max(float(v), par.minimo), par.maximo)
    return p


def resultados(modelo, p: dict, cifras: int = CIFRAS) -> list:
    """[[magnitud, valor]] de `Modelo.resultados` (o del equilibrio), en el orden del modelo."""
    filas = []
    for k, v in (modelo.calcular(**p) or {}).items():
        filas.append([str(k), _numero(v, cifras) if isinstance(v, (int, float)) or hasattr(v, "dtype") else str(v)])
    return filas


def calcular(modelo, pedidos: dict | None = None, cifras: int = CIFRAS, max_puntos: int | None = None) -> dict:
    """Curvas y resultados del modelo con los valores pedidos: lo que el navegador dibuja."""
    p = valores(modelo, pedidos)
    with warnings.catch_warnings():             # una división por cero de numpy en un extremo del rango da inf, que
        warnings.simplefilter("ignore", RuntimeWarning)   # aquí ya pasa a None: no se ensucia la consola del navegador
        return {"valores": {k: _numero(v, cifras) for k, v in p.items()},
                "curvas": serializar(modelo.curvas(p), cifras, max_puntos),
                "resultados": resultados(modelo, p, cifras)}


def calcular_json(modelo, pedidos_json: str = "{}") -> str:
    """Puente con JavaScript: recibe y devuelve texto JSON (evita convertir objetos entre Pyodide y el navegador)."""
    return json.dumps(calcular(modelo, json.loads(pedidos_json or "{}")), ensure_ascii=False, allow_nan=False,
                      separators=(",", ":"))
