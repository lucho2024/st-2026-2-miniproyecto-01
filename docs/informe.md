# Informe del miniproyecto 1

Llene cada sección reemplazando los marcadores `{{...}}`, sin quitar las
secciones. Las cifras salen de lo que imprime `python miniproyecto.py` y las
figuras son las que ese guion deja en `figuras/`. Las fórmulas van en LaTeX
(`$...$` o `$$...$$`).

## 1. La serie

La serie es la **precipitación mensual acumulada (mm)** de la estación
**CDEA El Topacio** (código 2629020601), en la cuenca del río Pance (Cali,
Valle del Cauca). Proviene de la red hidrometeorológica de la **Corporación
Autónoma Regional del Valle del Cauca (CVC)**, que suministró por correo
electrónico, para uso académico, los archivos `EXPORT_CPANCE_PRECIP_*.xls`;
se cita a la CVC como fuente.

La estación registra la lluvia de forma automática cada 10 minutos. Para
obtener la serie mensual se unieron los archivos, se eliminaron los registros
duplicados y se sumó toda la lluvia de cada mes. Un mes se habría dejado vacío
si tuviera datos en menos del 80 % de sus días. La serie resultante va de
**enero de 2015 a febrero de 2026** y tiene **134 observaciones** mensuales,
suficientes para ajustar los modelos y evaluarlos en los últimos 24 meses.

El grupo la eligió porque es insumo de un trabajo de tesis y porque tiene una
estacionalidad marcada. En la zona andina colombiana llueve en **dos
temporadas** al año, una en marzo–mayo y otra en octubre–noviembre, con una
temporada seca en julio–agosto. Por eso la serie se presta para trabajar la
diferencia estacional y el modelo SARIMA.

![La serie](../figuras/serie.png)

**Huecos.** Antes de modelar se revisó si faltaban meses. No faltó ninguno: el
mes con menos datos (mayo de 2017) tuvo registros en el 90 % de sus días.
Tampoco hay fechas repetidas, valores negativos ni meses en 0 mm (el mínimo es
5.7 mm, en agosto de 2019). Como no hubo huecos, no fue necesario rellenar
ningún dato.

Al revisar los registros crudos apareció un problema que la cobertura no
detecta: en algunos días la telemetría transmite **solo ceros** (143 registros
en 0 mm) y la lluvia del día aparece como un **total diario a las 07:00**, con
valores de 30 a 131 mm, imposibles en 10 minutos. Todo indica que el sensor
automático falló y la lluvia se registró por otra vía. Estos meses tienen la
mayor parte de su lluvia en totales diarios:

| Mes | Total (mm) | Parte en totales diarios |
|---|---|---|
| 2015-05 | 66.0 | 84 % |
| 2015-06 | 43.0 | 98 % |
| 2019-04 | 488.1 | 71 % |
| 2020-11 | 224.6 | 67 % |
| 2022-01 a 2022-03 | 185.0 / 464.1 / 340.0 | más del 90 % |
| 2022-06 | 440.0 | casi todo (69 registros en el mes) |
| 2023-05 | 291.0 | todo (un registro por día) |
| 2025-12 | 145.4 | 64 % |

La serie combina entonces dos formas de medir. En unos pocos días hay
lluvia en los dos tipos de registro (por ejemplo, octubre de 2019), lo que
sugiere un posible doble conteo pequeño.

**Atípicos.** Un criterio sobre la serie completa no sirve para una serie
estacional: 400 mm es normal en abril y extraordinario en agosto. Por eso los
atípicos se buscan en el residuo de la STL robusta,
$R_t = y_t - T_t - S_t$, que compara cada mes con lo esperado para ese mes. Se
marca como atípico el mes cuyo residuo cae fuera de
$[Q_1 - 1.5\,\mathrm{IQR},\ Q_3 + 1.5\,\mathrm{IQR}]$ de los residuos, es decir,
fuera de $[-174.5,\ 172.7]$ mm. Salen 7 meses:

| Mes | Observado (mm) | Esperado $T_t + S_t$ (mm) | Residuo (mm) | Peso STL |
|---|---|---|---|---|
| 2025-12 | 145.4 | 502.3 | −356.9 | 0.00 |
| 2022-06 | 440.0 | 139.2 | +300.8 | 0.00 |
| 2024-04 | 577.0 | 299.1 | +277.9 | 0.00 |
| 2023-03 | 474.6 | 232.2 | +242.4 | 0.01 |
| 2022-05 | 121.6 | 344.4 | −222.8 | 0.07 |
| 2023-10 | 371.8 | 157.4 | +214.4 | 0.10 |
| 2022-02 | 464.1 | 278.4 | +185.7 | 0.23 |

La STL robusta les da un peso casi nulo, de modo que no deforman la tendencia
ni la estacional y quedan en el residuo. Su lectura, contrastada con los
registros crudos:

- **Diciembre de 2025** (−356.9 mm) es en buena parte un **efecto de borde**:
  está al final de la serie, donde la tendencia LOESS solo tiene vecinos de un
  lado y sube a unos 340 mm/mes, así que el valor esperado (502 mm) está
  inflado. Además, el 64 % de su lluvia viene de totales diarios.
- **Junio de 2022** (+300.8 mm) y **febrero de 2022** (+185.7 mm) se midieron
  casi por completo con totales diarios. Junio cae en una temporada que
  debería ser seca y durante el episodio de La Niña 2020–2023, que aumenta la
  lluvia en la región andina; pero el cambio en la forma de medir también
  puede explicar el salto. Son **posibles atípicos de medición**.
- **Mayo de 2022** (−222.8 mm) es telemetría con el 97 % de los registros en
  cero, justo entre dos meses medidos con totales diarios: puede ser un mes
  seco o un sensor que falló sin respaldo diario.
- **Abril de 2024** (577 mm, el máximo), **marzo de 2023** y **octubre de
  2023** se midieron con telemetría y caen en temporadas húmedas: son meses
  lluviosos reales, más intensos que lo habitual.

**Decisión.** Los atípicos se **conservan**. Ninguno muestra un valor imposible
(negativo o código de faltante). Los medidos con telemetría son lluvia real, y
quitarlos haría que los modelos subestimaran los meses muy lluviosos, que son
justamente los que interesa pronosticar. Los medidos con totales diarios
quedan señalados como posibles artefactos de medición: corregirlos exigiría
reconstruir la serie desde los registros crudos con una regla por día (usar
el total diario cuando exista y, si no, la suma de la telemetría), lo que se
deja para el miniproyecto 2. La serie no se modifica, así que esta decisión no
introduce información del futuro en el *backtest*.

Decisión (columna `decision` de la tabla): *sin huecos (regla del 80 % no
activada); atípicos del residuo STL conservados; meses con totales diarios
señalados como posible artefacto*.

## 2. Componentes

![STL](../figuras/stl.png)

La STL separa la serie en tres partes, $y_t = T_t + S_t + R_t$: la tendencia,
la estacionalidad y el residuo. La versión robusta evita que los meses
atípicos distorsionen las dos primeras.

**Tendencia.** No sube ni baja de forma sostenida: oscila entre unos 155 y
231 mm/mes entre 2015 y 2024, con años más lluviosos (2018, 2021) y más secos
(2015, 2023) que coinciden con La Niña y El Niño. El salto final (289 mm/mes
en 2025 y 339 en 2026) se debe en parte a que 2025 fue muy lluvioso y en
parte a que la tendencia es menos confiable en el extremo de la serie.

**Estacionalidad.** El año tiene **dos temporadas de lluvia y dos secas**,
como es típico en la zona andina colombiana:

| Ene | Feb | Mar | Abr | May | Jun | Jul | Ago | Sep | Oct | Nov | Dic |
|---|---|---|---|---|---|---|---|---|---|---|---|
| −40.6 | +24.1 | +69.3 | **+118.6** | +109.4 | −59.0 | −102.7 | **−125.1** | −93.4 | +20.8 | +68.1 | +17.3 |

El mes más lluvioso es **abril (+118.6 mm** sobre la tendencia) y el más seco
es **agosto (−125.1 mm)**; octubre y noviembre forman la segunda temporada de
lluvias. Entre abril y agosto hay unos 244 mm de diferencia.

**Residuo.** Es grande: casi tan importante como la estacionalidad, lo que
indica que buena parte de la lluvia de cada mes no sigue un patrón regular.
Por eso cabe esperar errores de pronóstico altos con cualquier modelo. El
residuo más grande es **diciembre de 2025 (−356.9 mm)**, explicado en la
sección 1.

## 3. Líneas base y backtest

Los modelos se evalúan sobre los **últimos 24 meses** (marzo de 2024 a
febrero de 2026). Desde cada uno de **13 puntos de partida** (febrero de 2024
a febrero de 2025), el modelo aprende solo con los meses anteriores y
pronostica los **12 siguientes**, que se comparan con la lluvia real. Los
errores de los 13 intentos se promedian.

Como el modelo nunca ve los meses que debe pronosticar, no hay **fuga de
información**: el resultado se parece a lo que pasaría al pronosticar de
verdad.

Las dos líneas base son los pronósticos más simples posibles:

| Modelo | Qué hace | RMSE | MAE | MAPE (%) |
|---|---|---|---|---|
| Estacional ingenuo | Repite el mismo mes del año anterior | **154.93** | **112.39** | **43.90** |
| Ingenuo | Repite el último mes observado | 219.76 | 185.33 | 121.05 |

**Gana el estacional ingenuo**: en una serie con un ciclo anual tan marcado,
repetir el abril pasado funciona mucho mejor que repetir el último mes. Es la
marca que deben superar el SARIMA y el SARIMAX.

El MAPE se infla en los meses muy secos, donde un error pequeño en milímetros
es enorme en porcentaje. Por eso los modelos se comparan sobre todo con el
**RMSE y el MAE**, que están en milímetros.

## 4. Estacionariedad e identificación

Un SARIMA necesita una serie que oscile alrededor de un nivel fijo
(**estacionaria**). La prueba ADF lo verifica: si el valor p es menor que
0.05, la serie se considera estacionaria. Si no, se diferencia: restar el mes
anterior ($d = 1$) o el mismo mes del año anterior ($D = 1$).

| Versión | $d$ | $D$ | `regression` | Valor p |
|---|---|---|---|---|
| Original | 0 | 0 | `ct` | 0.2092 |
| `diff()` | 1 | 0 | `c` | $3.1 \times 10^{-11}$ |
| `diff(12)` | 0 | 1 | `c` | **0.0033** |
| `diff(12).diff()` | 1 | 1 | `c` | 0.0017 |

En la original se usa `'ct'` (con tendencia) y en las diferenciadas `'c'`. La
original no pasa. Con una sola diferencia pasan dos opciones, y se elige
**$d = 0$, $D = 1$**, porque la serie no tiene tendencia sino un ciclo anual
(sección 2). Con `diff()`, en cambio, el patrón anual sigue presente en el
rezago 12 de la ACF. Es la misma elección del taller 1.

![ACF y PACF](../figuras/acf_pacf.png)

Con la serie elegida, $w_t = y_t - y_{t-12}$, salen de la banda la **ACF** en
los rezagos 7 (+0.27) y 12 (−0.35), y la **PACF** en 7, 12, 20 y 24. La
barra aislada en 12 sugiere un modelo con un término estacional ($Q = 1$) y
nada más: **SARIMA$(0,0,0)(0,1,1)_{12}$**. La barra en 7 probablemente es
azar.

## 5. Modelos clásicos

Se probaron 36 combinaciones de órdenes y se compararon por AIC, que premia
el buen ajuste y castiga los parámetros de más:

| Modelo | AIC |
|---|---|
| **SARIMA$(0,0,0)(0,1,1)_{12}$** | **382.0** |
| SARIMA$(0,0,0)(1,1,1)_{12}$ | 383.2 |
| SARIMA$(2,0,2)(0,1,1)_{12}$ | 384.0 |

Gana el más simple, el mismo que sugería la ACF:

$$y_t - y_{t-12} = \varepsilon_t + \Theta\,\varepsilon_{t-12}, \qquad \Theta = -0.853.$$

En palabras: el modelo pronostica cada mes con un **patrón casi fijo**,
parecido al promedio de ese mes en los años anteriores. Tiene sentido, porque
las temporadas de lluvia llegan cada año en las mismas fechas.

![Residuos](../figuras/residuos.png)

**Residuos.** Lo que el modelo no explica se comporta como azar: no hay
patrones en la gráfica ni barras fuera de la banda, y la prueba de
**Ljung-Box** lo confirma (valor p 0.429 con 12 rezagos y 0.266 con 24, ambos
mayores que 0.05).

**SARIMAX.** Como variable externa se usó el **número de días del mes**: se
conoce de antemano por el calendario, así que no hay fuga. Mejora un poco el
pronóstico (RMSE de 117.05 a 113.79), pero el efecto sale de unos pocos
febreros bisiestos y tiene un signo sin sentido (−100.9 mm por día), así que
**probablemente es casualidad**.

## 6. Tabla de métricas

Decisión sobre los datos, común a todas las filas: *sin huecos (regla del
80 % no activada); atípicos del residuo STL conservados; meses con totales
diarios señalados como posible artefacto*.

| Modelo | RMSE | MAE | MAPE (%) |
|---|---|---|---|
| SARIMAX$(0,0,0)(0,1,1)_{12}$ + días del mes | **113.79** | **91.75** | 54.31 |
| SARIMA$(0,0,0)(0,1,1)_{12}$ | 117.05 | 93.35 | 54.68 |
| Estacional ingenuo | 154.93 | 112.39 | **43.90** |
| Ingenuo | 219.76 | 185.33 | 121.05 |

## 7. Conclusión

El mejor modelo clásico es el **SARIMAX$(0,0,0)(0,1,1)_{12}$ con los días
del mes**. Frente al estacional ingenuo, la mejor línea base, el error baja
un **26.6 % en RMSE** (de 154.93 a 113.79) y un **18.4 % en MAE** (de 112.39
a 91.75): unos 21 mm menos por mes. El MAPE sube un 23.7 % (de 43.90 a
54.31) porque en los meses muy secos unos pocos milímetros de error pesan
mucho en porcentaje.

Casi toda la mejora viene del SARIMA, no de la exógena. El modelo sigue
fallando en los meses extremos, como abril de 2024, porque pronostica un año
típico. Es el modelo que el miniproyecto 2 debe superar.
