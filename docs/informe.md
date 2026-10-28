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

Los archivos traen dos tipos de registro: la **telemetría automática**, un
dato cada 10 minutos (144 por día), y, en algunos días, un **total diario**
anotado a las 07:00 (el día pluviométrico de 7 a. m. a 7 a. m.). La serie
mensual se construyó con el script `preparar_serie.py`: une las hojas de los
archivos, quita los registros duplicados y suma todos los registros de cada
mes calendario, $y_t = \sum_{i \in \text{mes } t} p_i$, con $p_i$ la lluvia de
cada registro. Un mes con menos del 80 % de días con algún dato se deja vacío.
La serie resultante es **mensual**, va de **enero de 2015 a febrero de 2026** y
tiene **134 observaciones**, más del doble del mínimo de 60 que necesita el
*backtest* (24 meses de prueba y al menos 36 para el primer ajuste).

El grupo la eligió porque es insumo de un trabajo de tesis y porque tiene una
estacionalidad marcada: el régimen de lluvias de la zona andina colombiana es
**bimodal**, con temporadas húmedas en marzo–mayo y octubre–noviembre y una
temporada seca en julio–agosto, lo que la hace adecuada para trabajar la
diferencia estacional y el SARIMA.

![La serie](../figuras/serie.png)

**Huecos.** Como en el curso (sesión 1, §7; sesión 2, §14), primero se
comprueba si faltan meses, porque con huecos la STL devuelve vacíos sin avisar
y las métricas se promedian sobre menos meses. La regla del 80 % nunca se
activó: el mes con menos cobertura (mayo de 2017) tuvo datos en el 90 % de
sus días. La función `preparar` reconstruye además el índice mensual
completo: los 134 meses están presentes, sin fechas repetidas, sin valores
negativos ni códigos de faltante (como $-999$) y sin meses en 0 mm (el mínimo
es 5.7 mm, en agosto de 2019). No hubo nada que imputar; si hubiera huecos,
la opción del curso sería la interpolación lineal.

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

La STL robusta con periodo 12 separa la serie en tendencia, estacional y
residuo, $y_t = T_t + S_t + R_t$, con suavizados LOESS. Con `robust=True` los
meses de residuo grande reciben un peso bajo (3 meses quedan con peso 0), de
modo que los atípicos no deforman la tendencia ni la estacional.

**Tendencia.** Promedio por año (mm/mes):

| 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 155 | 192 | 222 | 230 | 213 | 197 | 231 | 198 | 164 | 192 | 289 | 339 |

No tiene una dirección sostenida: sube hasta 2018, baja en 2020, sube en 2021,
cae en 2023 y vuelve a subir. Más que una tendencia es un **ciclo cuasi
periódico**, sin periodo fijo, que coincide con los episodios de El Niño y La
Niña: el nivel bajo de 2015 con El Niño de 2015–2016, el alto de 2021 con La
Niña y la caída de 2023 con El Niño de 2023. El salto final a 289 y 339 mm/mes
hay que leerlo con cuidado: en el extremo de la serie LOESS solo tiene vecinos
de un lado (**efecto de borde**), y 2025 fue además un año muy lluvioso.

**Estacional.** Promedio por mes (mm):

| Ene | Feb | Mar | Abr | May | Jun | Jul | Ago | Sep | Oct | Nov | Dic |
|---|---|---|---|---|---|---|---|---|---|---|---|
| −40.6 | +24.1 | +69.3 | **+118.6** | +109.4 | −59.0 | −102.7 | **−125.1** | −93.4 | +20.8 | +68.1 | +17.3 |

El régimen es **bimodal**, el típico de la zona andina colombiana: dos
temporadas de lluvia, de marzo a mayo (máximo en abril, +118.6 mm) y de
octubre a noviembre (noviembre, +68.1 mm), y dos temporadas secas, una larga
de junio a septiembre (mínimo en agosto, −125.1 mm) y una corta de diciembre
a febrero (enero, −40.6 mm). La amplitud entre abril y agosto es de
243.7 mm: en promedio, abril recibe unos 244 mm más de lluvia que agosto.

**Residuo.** Su varianza (7 138) es casi tan grande como la de la estacional
(8 381), mientras que la de la tendencia es mucho menor (1 643). Con la medida
de Hyndman y Athanasopoulos (*Forecasting: Principles and Practice*, §3.4),

$$F_S = \max\left(0,\ 1 - \frac{\mathrm{Var}(R_t)}{\mathrm{Var}(S_t + R_t)}\right) = 0.53,
\qquad
F_T = \max\left(0,\ 1 - \frac{\mathrm{Var}(R_t)}{\mathrm{Var}(T_t + R_t)}\right) = 0.10,$$

la estacionalidad es moderada y la tendencia casi nula. Cerca de la mitad de
la variación mes a mes es ruido, así que ningún modelo debería pronosticar
esta serie con mucha precisión; eso ya se ve en el MAPE de 43.9 % del
estacional ingenuo. El residuo más grande es **diciembre de 2025, −356.9 mm**,
en buena parte por el efecto de borde de la tendencia; este y los demás
atípicos se analizan en la sección 1.

## 3. Líneas base y backtest

{{Cómo es el backtest: cuántos orígenes, horizonte y qué meses quedan en la
prueba. Por qué ningún dato posterior al origen entra al modelo.}}

{{RMSE, MAE y MAPE del ingenuo y del estacional ingenuo, y cuál gana.}}

## 4. Estacionariedad e identificación

{{Valor p de la prueba ADF para la serie, su diferencia regular, la
estacional y las dos juntas. El d y el D elegidos.}}

![ACF y PACF](../figuras/acf_pacf.png)

{{Qué rezagos salen de las bandas y qué órdenes sugieren.}}

## 5. Modelos clásicos

{{La rejilla de órdenes y su AIC. El modelo elegido, escrito con su
ecuación.}}

![Residuos](../figuras/residuos.png)

{{Diagnóstico de los residuos: Ljung-Box y lo que muestran la gráfica y su
ACF.}}

{{La variable exógena: qué es, por qué se conoce de antemano y si mejora al
SARIMA.}}

## 6. Tabla de métricas

{{Copie aquí `resultados/metricas.csv` como tabla de Markdown, ordenada por
RMSE.}}

| Modelo | Decisión | RMSE | MAE | MAPE (%) |
|---|---|---|---|---|
| {{...}} | {{...}} | {{...}} | {{...}} | {{...}} |

## 7. Conclusión

{{El mejor modelo clásico, cuánto mejora a la mejor línea base en cada
métrica y en qué meses o tramos sigue fallando. Es el modelo que el
miniproyecto 2 debe superar.}}
