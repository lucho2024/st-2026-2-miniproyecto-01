"""Miniproyecto 1: la serie del grupo, de las líneas base al mejor modelo clásico.

Se corre de principio a fin con

    python miniproyecto.py

y deja las figuras en figuras/ y la tabla en resultados/metricas.csv. Las
partes marcadas con TODO las completa el grupo; mientras falten, el guion las
reporta como pendientes y sigue. El informe, docs/informe.md, cita las cifras
y las figuras que produce este guion.
"""
import warnings

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tsa.seasonal import STL
from statsmodels.tsa.stattools import acf, adfuller, pacf


from comun import (RAIZ, backtest, cargar_serie, estacional_ingenuo,  # noqa: E402
                   fechas_siguientes, ingenuo)

warnings.filterwarnings("ignore")
FIGURAS = RAIZ / "figuras"
RESULTADOS = RAIZ / "resultados"
FIGURAS.mkdir(exist_ok=True)
RESULTADOS.mkdir(exist_ok=True)

# ============================================================
# 1. La serie
# ============================================================
# Cambie estos cuatro datos por los de la serie del grupo y documente la
# fuente en datos/README.md. La serie de ejemplo solo sirve para probar que
# el guion corre.
ARCHIVO = "datos/pance_mensual.csv"
FECHA = "mes"
VALOR = "valor"
PERIODO = 12

# Lo que se hizo con los huecos y con los datos atípicos, en una línea. Va
# a la columna `decision` de la tabla de métricas.
DECISION = "Sin huecos (regla del 80 % no activada); atípicos del residuo STL conservados; meses con totales diarios señalados como posible artefacto"


def preparar(serie):
    """Verifica continuidad del índice mensual, ausencia de faltantes y atípicos.

    Comprueba que la secuencia cronológica esté completa, sin registros
    duplicados, centinelas ni meses omitidos.
    """
    print("\n--- Verificación de calidad de la serie ---")

    # 1. Construir índice mensual completo desde la primera fecha hasta la última
    primera_fecha = serie.index.min()
    ultima_fecha = serie.index.max()
    indice_completo = pd.date_range(start=primera_fecha, end=ultima_fecha, freq="MS")

    print(f"  Primera fecha detectada         : {primera_fecha:%Y-%m}")
    print(f"  Última fecha detectada          : {ultima_fecha:%Y-%m}")
    print(f"  Índice mensual construido       : {len(indice_completo)} meses consecutivos")

    # Reindexar la serie sobre el índice completo
    serie_reindexada = serie.reindex(indice_completo)
    nans_al_reindexar = serie_reindexada.isna().sum()
    print(f"  NaNs al reindexar               : {nans_al_reindexar} (meses faltantes en la secuencia)")

    # 2. Comprobar códigos que esconden un faltante o inconsistencias
    fechas_rep = serie.index.duplicated().sum()
    negativos = (serie < 0).sum()
    ceros = (serie == 0).sum()
    print(f"  Fechas repetidas                : {fechas_rep}")
    print(f"  Valores negativos / centinelas  : {negativos}")
    print(f"  Meses con lluvia = 0 mm         : {ceros} (mínimo observado: {serie.min():.1f} mm)")

    # 3. Atípicos sobre el residuo de la STL robusta: compara cada mes con lo
    # esperado para ese mes (tendencia + estacional), no con toda la serie
    stl = STL(serie, period=PERIODO, robust=True).fit()
    residuo = stl.resid
    q1, q3 = residuo.quantile([0.25, 0.75])
    iqr = q3 - q1
    limite_inf, limite_sup = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    atipicos = residuo[(residuo < limite_inf) | (residuo > limite_sup)]
    print(f"  Atípicos (IQR del residuo STL)  : {len(atipicos)} meses fuera de "
          f"[{limite_inf:.1f}, {limite_sup:.1f}] mm")
    tabla = pd.DataFrame({"observado": serie[atipicos.index],
                          "esperado": (stl.trend + stl.seasonal)[atipicos.index],
                          "residuo": atipicos,
                          "peso STL": pd.Series(stl.weights, index=serie.index)[atipicos.index]})
    tabla.index = tabla.index.strftime("%Y-%m")
    print(tabla.sort_values("residuo", key=abs, ascending=False).round(2).to_string())
    print("  Decisión sobre atípicos         : conservar (meses con totales diarios: posible artefacto de medición)\n")

    # Validaciones formales
    assert nans_al_reindexar == 0, f"Faltan {nans_al_reindexar} meses en la secuencia histórica"
    assert fechas_rep == 0, "Hay fechas duplicadas en la serie"
    assert negativos == 0, "Hay códigos de faltante (-999 o negativos)"

    return serie_reindexada


def graficar_serie(serie):
    figura, eje = plt.subplots(figsize=(9, 3.4))
    eje.plot(serie.index, serie.to_numpy())
    eje.set_title("Precipitación mensual – Estación CDEA El Topacio, río Pance (CVC)")
    eje.set_ylabel("mm/mes")
    eje.set_xlabel("mes")
    figura.tight_layout()
    figura.savefig(FIGURAS / "serie.png", dpi=120)
    plt.close(figura)


# ============================================================
# 2. Descomposición
# ============================================================

def descomponer(serie):
    """TODO: STL robusta con el periodo de la serie; guarde figuras/stl.png."""
    
    stl = STL(serie, period=PERIODO, robust=True).fit()

    # 2. Graficar y guardar la figura en figuras/stl.png
    figura = stl.plot()
    figura.set_size_inches(10, 6)
    figura.tight_layout()
    figura.savefig(FIGURAS / "stl.png", dpi=120)
    plt.close(figura)

    # 3. Calcular mes más alto y más bajo de la estacionalidad
    estacional_mes = stl.seasonal.groupby(stl.seasonal.index.month).mean()
    nombres = [
        "Ene",
        "Feb",
        "Mar",
        "Abr",
        "May",
        "Jun",
        "Jul",
        "Ago",
        "Sep",
        "Oct",
        "Nov",
        "Dic",
    ]
    estacional_mes.index = nombres
    print(
        f"Estacionalidad más alta: {estacional_mes.idxmax()} ({estacional_mes.max():+.1f} mm)"
    )
    print(
        f"Estacionalidad más baja: {estacional_mes.idxmin()} ({estacional_mes.min():+.1f} mm)"
    )
    print("Estacional promedio por mes (mm):")
    print(estacional_mes.round(1).to_frame().T.to_string(index=False))
    print(f"Amplitud estacional: {estacional_mes.max() - estacional_mes.min():.1f} mm")

    # Tendencia: promedio por año, para ver si tiene dirección o es un ciclo
    tendencia_anio = stl.trend.groupby(stl.trend.index.year).mean()
    print("Tendencia promedio por año (mm/mes):")
    print(tendencia_anio.round(0).astype(int).to_frame().T.to_string(index=False))

    # Tamaño de cada componente y fuerza de la estacionalidad y de la tendencia
    # (Hyndman y Athanasopoulos, Forecasting: Principles and Practice, §3.4)
    var_r = stl.resid.var()
    fuerza_s = max(0, 1 - var_r / (stl.seasonal + stl.resid).var())
    fuerza_t = max(0, 1 - var_r / (stl.trend + stl.resid).var())
    print(f"Varianza: serie {serie.var():.0f}, tendencia {stl.trend.var():.0f}, "
          f"estacional {stl.seasonal.var():.0f}, residuo {var_r:.0f}")
    print(f"Fuerza estacional: {fuerza_s:.2f}; fuerza de la tendencia: {fuerza_t:.2f}")
    print(f"Meses con peso 0 en la STL robusta: {int((stl.weights == 0).sum())}")

    # 4. Encontrar el residuo más grande (atípico)
    fecha_peor = stl.resid.abs().idxmax()
    peor_residuo = stl.resid.loc[fecha_peor]
    print(
        f"Residuo más extremo: {fecha_peor:%Y-%m} con {peor_residuo:+.1f} mm\n"
    )


# ============================================================
# 3. Estacionariedad e identificación
# ============================================================

def estacionariedad(serie):
    """TODO: ADF sobre la serie, su diferencia regular, la estacional y las dos.

    Imprima el valor p de cada versión, elija d y D, y guarde la ACF y la
    PACF de la serie elegida en figuras/acf_pacf.png. Devuelva (d, D).
    """
    combinaciones = [
        ("original (d=0, D=0)", serie, "ct", 0, 0),
        ("diff() (d=1, D=0)", serie.diff(), "c", 1, 0),
        ("diff(12) (d=0, D=1)", serie.diff(12), "c", 0, 1),
        ("diff(12).diff() (d=1, D=1)", serie.diff(12).diff(), "c", 1, 1),
    ]

    print("\n--- Pruebas de Estacionariedad (ADF) ---")
    for nombre, s, reg, _, _ in combinaciones:
        p = adfuller(s.dropna(), regression=reg, autolag="AIC")[1]
        p_str = f"{p:.4e}" if p < 1e-4 else f"{p:.4f}"
        print(f"  {nombre:28s} (reg='{reg}'): valor p = {p_str}")

    # Regla: combinación con menos diferencias cuyo valor p queda bajo 0.05
    d, D = 1, 0
    print(f"\nÓrdenes elegidos: d = {d}, D = {D}")

    # Serie diferenciada elegida
    x = serie.diff().dropna()

    def fuera(valores, intervalo):
        """Rezagos (sin el 0) cuyo valor sale de la banda centrada en cero."""
        banda = intervalo[:, 1] - valores
        return [k for k in range(1, len(valores)) if abs(valores[k]) > banda[k]]

    rez_acf = fuera(*acf(x, nlags=36, alpha=0.05))
    rez_pacf = fuera(*pacf(x, nlags=36, alpha=0.05, method="ywm"))
    print(f"Rezagos fuera de banda en ACF : {rez_acf}")
    print(f"Rezagos fuera de banda en PACF: {rez_pacf}\n")

    # Gráfica de ACF y PACF
    fig, ejes = plt.subplots(1, 2, figsize=(8.5, 3.2), sharey=True)
    plot_acf(x, lags=36, ax=ejes[0], title=f"ACF (d={d}, D={D})")
    plot_pacf(x, lags=36, ax=ejes[1], title=f"PACF (d={d}, D={D})", method="ywm")
    for eje in ejes:
        eje.set_ylim(-1.05, 1.05)
        eje.set_xticks(range(0, 37, 6))
    fig.tight_layout()
    fig.savefig(FIGURAS / "acf_pacf.png", dpi=120)
    plt.close(fig)

    return d, D


# ============================================================
# 4. Modelos clásicos
# ============================================================
# Cada modelo es una función modelo(entrenamiento, h) que devuelve h
# pronósticos y solo usa `entrenamiento`. Así entra al backtest común.

def elegir_sarima(serie, d, D):
    """TODO: rejilla pequeña de órdenes (p, q, P, Q) comparada por AIC.

    Ajuste con toda la serie preparada, imprima la tabla de AIC, revise los
    residuos del elegido con Ljung-Box y guarde figuras/residuos.png.
    Devuelva el orden y el orden estacional elegidos.
    """
    raise NotImplementedError("selección del SARIMA")


def modelo_sarima(orden, orden_estacional):
    """TODO: devuelva la función modelo(entrenamiento, h) del SARIMA elegido."""
    raise NotImplementedError("SARIMA en el backtest")


def exogenas(serie):
    """TODO: DataFrame de variables conocidas de antemano, con el índice de la serie.

    Por ejemplo, el número de festivos o de días hábiles de cada mes. Debe
    cubrir también los 12 meses que siguen al final de la serie.
    """
    raise NotImplementedError("variables exógenas")


def modelo_sarimax(orden, orden_estacional, x):
    """TODO: devuelva modelo(entrenamiento, h) de un SARIMAX con exógenas x.

    Use x.loc[entrenamiento.index] para ajustar y
    x.loc[fechas_siguientes(entrenamiento, h)] para pronosticar.
    """
    raise NotImplementedError("SARIMAX en el backtest")


# ============================================================
# 5. La tabla de métricas
# ============================================================

def fila(nombre, serie, modelo):
    _, promedio = backtest(serie, modelo)
    return {"modelo": nombre, "decision": DECISION,
            "RMSE": round(promedio["RMSE"], 2), "MAE": round(promedio["MAE"], 2),
            "MAPE": round(promedio["MAPE"], 2)}


def pendiente(parte, error):
    print(f"  pendiente: {parte} ({error})")


def main():
    cruda = cargar_serie(ARCHIVO, FECHA, VALOR)
    print(f"Serie: {len(cruda)} meses, de {cruda.index[0]:%Y-%m} a "
          f"{cruda.index[-1]:%Y-%m}, {cruda.isna().sum()} vacíos")
    serie = preparar(cruda)
    graficar_serie(serie)

    filas = [fila("ingenuo", serie, ingenuo),
             fila("estacional ingenuo", serie,
                  lambda t, h: estacional_ingenuo(t, h, PERIODO))]

    try:
        descomponer(serie)
    except NotImplementedError as error:
        pendiente("parte 2", error)

    try:
        d, D = estacionariedad(serie)
    except NotImplementedError as error:
        pendiente("parte 3", error)
        d = D = None

    if d is not None:
        try:
            orden, estacional = elegir_sarima(serie, d, D)
            filas.append(fila(f"SARIMA{orden}{estacional}", serie,
                              modelo_sarima(orden, estacional)))
            x = exogenas(serie)
            filas.append(fila(f"SARIMAX{orden}{estacional} + exógenas", serie,
                              modelo_sarimax(orden, estacional, x)))
        except NotImplementedError as error:
            pendiente("parte 4", error)

    tabla = pd.DataFrame(filas).sort_values("RMSE")
    tabla.to_csv(RESULTADOS / "metricas.csv", index=False)
    print(tabla.drop(columns="decision").to_string(index=False))
    print("Mejor modelo por RMSE:", tabla.iloc[0]["modelo"])


if __name__ == "__main__":
    main()
