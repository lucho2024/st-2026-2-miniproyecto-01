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
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.tsa.arima.model import ARIMA
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
        # Extra: la original con 'c'. Su p (≈0.10) muestra que la tendencia es
        # débil; 'ct' se usa para no confundir una posible recta con una raíz
        # unitaria, no porque la tendencia sea evidente (ver parte 2).
        ("original (d=0, D=0)", serie, "c", 0, 0),
        ("diff() (d=1, D=0)", serie.diff(), "c", 1, 0),
        ("diff(12) (d=0, D=1)", serie.diff(12), "c", 0, 1),
        ("diff(12).diff() (d=1, D=1)", serie.diff(12).diff(), "c", 1, 1),
    ]

    print("\n--- Pruebas de Estacionariedad (ADF) ---")
    for nombre, s, reg, _, _ in combinaciones:
        p = adfuller(s.dropna(), regression=reg, autolag="AIC")[1]
        p_str = f"{p:.4e}" if p < 1e-4 else f"{p:.4f}"
        print(f"  {nombre:28s} (reg='{reg}'): valor p = {p_str}")

    # Regla del curso: la combinación con menos diferencias cuyo valor p queda
    # bajo 0.05. Aquí hay un empate: diff() (d=1, D=0) y diff(12) (d=0, D=1)
    # pasan las dos con una sola diferencia.
    #
    # Modificación: antes se elegía (d, D) = (1, 0). Se cambia a (0, 1) porque:
    # - la serie no tiene tendencia sino un ciclo anual (parte 2), así que la
    #   diferencia que corresponde es la estacional;
    # - con diff() el ciclo anual no se va: la ACF conserva una barra positiva
    #   en el rezago 12, y la barra negativa en 1 junto con la PACF negativa en
    #   los rezagos 1 a 5 son señal de diferenciar de más;
    # - ADF no detecta raíces unitarias estacionales, así que su p bajo con
    #   diff() no garantiza que la estacionalidad se haya ido;
    # - es la misma elección del taller 1.
    d, D = 0, 1
    print(f"\nÓrdenes elegidos: d = {d}, D = {D}")

    # Serie diferenciada elegida, construida a partir de d y D para que la
    # figura y los rezagos correspondan siempre a la elección
    x = serie.copy()
    if D:
        x = x.diff(PERIODO)
    if d:
        x = x.diff()
    x = x.dropna()

    def fuera(valores, intervalo):
        """Rezagos (sin el 0) cuyo valor sale de la banda centrada en cero."""
        banda = intervalo[:, 1] - valores
        return [k for k in range(1, len(valores)) if abs(valores[k]) > banda[k]]

    def con_valores(rezagos, valores):
        return ", ".join(f"{k} ({valores[k]:+.2f})" for k in rezagos)

    valores_acf, intervalo_acf = acf(x, nlags=36, alpha=0.05)
    valores_pacf, intervalo_pacf = pacf(x, nlags=36, alpha=0.05, method="ywm")
    rez_acf = fuera(valores_acf, intervalo_acf)
    rez_pacf = fuera(valores_pacf, intervalo_pacf)
    print(f"Serie elegida: {len(x)} datos, banda aproximada ±{1.96 / np.sqrt(len(x)):.3f}")
    print(f"Rezagos fuera de banda en ACF : {con_valores(rez_acf, valores_acf)}")
    print(f"Rezagos fuera de banda en PACF: {con_valores(rez_pacf, valores_pacf)}")

    # Comparación con la alternativa descartada, diff() (d=1, D=0): respalda
    # la elección con las cifras que se citan en el informe
    alterna = serie.diff().dropna()
    valores_alt, intervalo_alt = acf(alterna, nlags=36, alpha=0.05)
    valores_palt, intervalo_palt = pacf(alterna, nlags=36, alpha=0.05, method="ywm")
    print("Alternativa descartada diff() (d=1, D=0):")
    print(f"  ACF  fuera de banda: {con_valores(fuera(valores_alt, intervalo_alt), valores_alt)}")
    print(f"  PACF fuera de banda: {con_valores(fuera(valores_palt, intervalo_palt), valores_palt)}\n")

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

# La lluvia está en cientos de mm. Como en la sesión 5 (B3), los modelos se
# ajustan con la serie dividida por 100 para que el optimizador se mueva, y
# el pronóstico se multiplica por 100 al final. Es la misma constante para
# todos los meses, así que no introduce fuga.
ESCALA = 100


def ajustar(y, orden, orden_estacional, exog=None):
    """SARIMA(p,d,q)(P,D,Q)m sobre y en la escala de ajuste; con exog, SARIMAX."""
    return ARIMA(y, exog=exog, order=orden, seasonal_order=orden_estacional).fit()


def elegir_sarima(serie, d, D):
    """Rejilla pequeña de órdenes (p, q, P, Q) comparada por AIC.

    Ajusta con toda la serie preparada, imprime la tabla de AIC, revisa los
    residuos del elegido con Ljung-Box y guarda figuras/residuos.png.
    Devuelve el orden y el orden estacional elegidos.
    """
    y = serie / ESCALA
    filas = []
    for p in range(3):
        for q in range(3):
            for P in range(2):
                for Q in range(2):
                    ajuste = ajustar(y, (p, d, q), (P, D, Q, PERIODO))
                    filas.append({"orden": (p, d, q), "estacional": (P, D, Q, PERIODO),
                                  "parámetros": p + q + P + Q,
                                  "AIC": round(ajuste.aic, 1), "BIC": round(ajuste.bic, 1)})
    tabla = pd.DataFrame(filas).sort_values("AIC").reset_index(drop=True)
    print("\n--- Rejilla SARIMA por AIC ---")
    print(f"{len(tabla)} modelos ajustados; los cinco primeros:")
    print(tabla.head(5).to_string())
    print(f"El peor: {tabla.iloc[-1]['orden']}{tabla.iloc[-1]['estacional']} con AIC {tabla.iloc[-1]['AIC']}")

    # Con empates (AIC a menos de 2 puntos del mejor) se elige el más simple,
    # como en la sesión 5 (B5)
    cercanos = tabla[tabla["AIC"] <= tabla["AIC"].iloc[0] + 2]
    elegido = cercanos.sort_values(["parámetros", "AIC"]).iloc[0]
    orden, orden_estacional = elegido["orden"], elegido["estacional"]
    print(f"Elegido: SARIMA{orden}{orden_estacional}, AIC {elegido['AIC']}, "
          f"{elegido['parámetros']} parámetro(s) además de la varianza")

    # Diagnóstico de residuos. Los primeros d + m·D son de arranque: el modelo
    # no tiene con qué pronosticarlos, así que se descartan (sesión 5, B6)
    ajuste = ajustar(y, orden, orden_estacional)
    print("Coeficientes:", {k: round(v, 3) for k, v in ajuste.params.items()})
    residuos = ajuste.resid.iloc[d + PERIODO * D:] * ESCALA
    ljung = acorr_ljungbox(residuos, lags=[12, 24])
    for h, fila_lb in ljung.iterrows():
        print(f"Ljung-Box h={h}: estadístico {fila_lb['lb_stat']:.2f}, valor p {fila_lb['lb_pvalue']:.3f}")
    print(f"Residuos: desviación {residuos.std():.1f} mm; más grande "
          f"{residuos.abs().idxmax():%Y-%m} ({residuos[residuos.abs().idxmax()]:+.1f} mm)")

    figura, (arriba, abajo) = plt.subplots(2, 1, figsize=(9, 5.5))
    arriba.plot(residuos.index, residuos.to_numpy())
    arriba.axhline(0, color="black", linewidth=0.8)
    arriba.set_title(f"Residuos del SARIMA{orden}{orden_estacional}")
    arriba.set_ylabel("mm/mes")
    plot_acf(residuos, lags=36, ax=abajo, title="ACF de los residuos")
    abajo.set_ylim(-1.05, 1.05)
    abajo.set_xticks(range(0, 37, 6))
    figura.tight_layout()
    figura.savefig(FIGURAS / "residuos.png", dpi=120)
    plt.close(figura)

    return orden, orden_estacional


def modelo_sarima(orden, orden_estacional):
    """Devuelve la función modelo(entrenamiento, h) del SARIMA elegido."""
    def modelo(entrenamiento, h):
        ajuste = ajustar(entrenamiento / ESCALA, orden, orden_estacional)
        return ajuste.forecast(h).to_numpy() * ESCALA
    return modelo


def exogenas(serie):
    """Variables conocidas de antemano, con el índice de la serie y 12 meses más.

    La lluvia del mes es una suma, así que un mes más largo acumula más: el
    número de días del mes sale del calendario y se conoce con certeza para
    cualquier mes futuro, sin fuga. Con la diferencia estacional (D = 1) solo
    cambia de un año a otro en febrero (28 o 29 días).
    """
    meses = pd.date_range(serie.index[0], serie.index[-1] + pd.DateOffset(months=12), freq="MS")
    return pd.DataFrame({"dias_mes": meses.days_in_month.astype(float)}, index=meses)


def describir_sarimax(serie, orden, orden_estacional, x):
    """Ajusta el SARIMAX con toda la serie e imprime el efecto de la exógena."""
    ajuste = ajustar(serie / ESCALA, orden, orden_estacional, exog=x.loc[serie.index])
    for nombre in x.columns:
        print(f"\nSARIMAX, {nombre}: {ajuste.params[nombre] * ESCALA:+.1f} mm por unidad, "
              f"valor p {ajuste.pvalues[nombre]:.3f}; AIC {ajuste.aic:.1f}")


def modelo_sarimax(orden, orden_estacional, x):
    """Devuelve modelo(entrenamiento, h) de un SARIMAX con exógenas x.

    Ajusta con x.loc[entrenamiento.index] y pronostica con
    x.loc[fechas_siguientes(entrenamiento, h)]: solo usa los días de los meses
    futuros, que se conocen en el origen.
    """
    def modelo(entrenamiento, h):
        ajuste = ajustar(entrenamiento / ESCALA, orden, orden_estacional,
                         exog=x.loc[entrenamiento.index])
        futuro = x.loc[fechas_siguientes(entrenamiento, h)]
        return ajuste.forecast(h, exog=futuro).to_numpy() * ESCALA
    return modelo


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

    # Cómo es el backtest: orígenes y meses de prueba (las cifras de la sección 3)
    origenes, _ = backtest(serie, ingenuo)
    print(f"Backtest: {len(origenes)} orígenes, de {origenes['origen'].iloc[0]:%Y-%m} "
          f"a {origenes['origen'].iloc[-1]:%Y-%m}; horizonte 1 a 12; meses de prueba "
          f"{serie.index[-24]:%Y-%m} a {serie.index[-1]:%Y-%m}\n")

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
            describir_sarimax(serie, orden, estacional, x)
            filas.append(fila(f"SARIMAX{orden}{estacional} + exógenas", serie,
                              modelo_sarimax(orden, estacional, x)))
        except NotImplementedError as error:
            pendiente("parte 4", error)

    tabla = pd.DataFrame(filas).sort_values("RMSE")
    tabla.to_csv(RESULTADOS / "metricas.csv", index=False)
    print(tabla.drop(columns="decision").to_string(index=False))
    print("Mejor modelo por RMSE:", tabla.iloc[0]["modelo"])

    # Cuánto mejora el mejor modelo a la mejor línea base, en cada métrica
    mejor = tabla.iloc[0]
    bases = tabla[tabla["modelo"].isin(["ingenuo", "estacional ingenuo"])]
    base = bases.iloc[0]
    if mejor["modelo"] != base["modelo"]:
        print(f"Frente a la mejor línea base ({base['modelo']}):")
        for metrica in ["RMSE", "MAE", "MAPE"]:
            cambio = 100 * (mejor[metrica] - base[metrica]) / base[metrica]
            print(f"  {metrica}: {base[metrica]:.2f} -> {mejor[metrica]:.2f} ({cambio:+.1f} %)")


if __name__ == "__main__":
    main()
