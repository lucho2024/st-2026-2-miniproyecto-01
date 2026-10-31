# Guía Maestra de Sustentación y Conceptos · Miniproyecto 1
**Pronóstico de Series Temporales con IA · UAO 2026-II**  
**Profesor:** Carlos Andrés Delgado Saavedra  
**Integrantes:** Gustavo Adolfo Morales Ortiz & Luis Hernando Montoya Muñoz  

---

## ⏱️ Reglas del Juego (15 Minutos en Total)
* **7 minutos:** Presentación del grupo (mostrar serie, decisiones de datos, modelo y tabla de métricas).
* **8 minutos:** Preguntas del profesor sobre las decisiones tomadas.
* **Demostración en vivo:** Un integrante al azar correrá `python miniproyecto.py` en la terminal.

---

## 📖 DICCIONARIO Y GLOSARIO DE SÍMBOLOS MATEMÁTICOS

Para entender las ecuaciones del código y responder con solvencia cuando el profesor señale una fórmula:

| Símbolo | Nombre técnico | Significado en palabras sencillas | ¿Cuánto vale en tu proyecto? |
| :--- | :--- | :--- | :--- |
| $y_t$ | Serie temporal observada | La lluvia real registrada en el mes $t$ (en mm). | Valores entre 5.7 y 577.0 mm |
| $T_t$ | Tendencia (*Trend*) | El nivel medio suave de fondo a largo plazo. | Oscila entre 155 y 230 mm/mes |
| $S_t$ | Estacionalidad (*Seasonal*) | El patrón climático que se repite religiosamente cada 12 meses. | Pico: Abril (+118.6 mm), Valle: Agosto (-125.1 mm) |
| $R_t$ | Residuo (*Residual*) | **La sorpresa**. Lo que sobró: $R_t = y_t - (T_t + S_t)$. | Mide la anomalía climática real de ese mes |
| $Q_1, Q_3$ | Cuartiles (25% y 75%) | Puntos que encierran el 50% central de los meses normales. | Calculados sobre los residuos $R_t$ |
| $\text{IQR}$ | Rango Intercuartílico | $Q_3 - Q_1$: la dispersión o ancho del clima habitual. | Franja de Tukey: $[-174.5, 172.7]$ mm |
| $w_t$ | Serie diferenciada | La serie ya estacionaria tras aplicar las diferencias: $y_t - y_{t-12}$. | 122 meses (media centrada en 0) |
| $d$ | Orden de diferencia regular | Cuántas veces se resta el mes anterior ($y_t - y_{t-1}$) para matar tendencias. | **$d = 0$** (no hay tendencia secular) |
| $D$ | Orden de diferencia estacional | Cuántas veces se resta el año anterior ($y_t - y_{t-12}$) para matar el ciclo anual. | **$D = 1$** (periodo $m=12$) |
| $p$ | Orden AutoRegresivo regular | Cuántos meses pasados recientes ($t-1, t-2$) influyen directamente en hoy. | **$p = 0$** (el mes previo no aporta memoria) |
| $q$ | Orden Media Móvil regular | Cuántas sorpresas recientes influyen en el mes actual. | **$q = 0$** |
| $P$ | Orden AutoRegresivo estacional | Si el valor de hace 12 meses predice directamente el de hoy. | **$P = 0$** (el MA estacional es más eficiente) |
| $Q$ | Orden Media Móvil estacional | Si la sorpresa climática de hace 12 meses corrige el pronóstico de hoy. | **$Q = 1$** |
| $\Theta$ (Theta) | Coeficiente MA estacional | El peso que se le da al error de hace 12 meses en el modelo. | **$\Theta = -0.853$** (en `ma.S.L12`) |
| $\varepsilon_t$ | Ruido blanco / Innovación | El choque aleatorio impredecible del mes actual. | Media 0, varianza $\sigma^2$ |
| $\sigma^2$ | Varianza residual | La dispersión del error aleatorio que el modelo no puede predecir. | $\approx 1.145$ (en escala reducida) |
| $m$ | Periodicidad estacional | Número de periodos que componen un ciclo completo. | **$m = 12$** (12 meses por año) |
| $\text{AIC}$ | Criterio de Akaike | Métrica que premia el buen ajuste y castiga agregar parámetros ($2k - 2\ln L$). | **382.0** (el más bajo de la rejilla) |
| $Q_{\text{LB}}$ | Estadístico de Ljung-Box | Mide si las autocorrelaciones de los residuos son conjuntamente cero. | $p = 0.429$ a 12 meses, $p = 0.266$ a 24 meses |
| $x_t$ | Variable exógena | Variable externa conocida con certeza de antemano. | Días del mes (28 a 31) |
| $\beta$ | Coeficiente de la exógena | Cuántos mm de lluvia suma/resta cada unidad de la variable exógena. | $-100.9$ mm/unidad ($p = 0.095$) |
| $h$ | Horizonte de pronóstico | Cuántos meses hacia el futuro proyecta el modelo en cada origen. | **$h = 1$ a 12 meses** |

---

## 🧠 FUNDAMENTOS TEÓRICOS: EL "POR QUÉ" DE CADA PASO Y SUS TÉRMINOS

Esta sección está diseñada para que entiendas la **física y la matemática detrás de cada decisión**. Si el profesor te pregunta por cualquier concepto, aquí tienes la definición técnica rigurosa, la analogía intuitiva y la forma exacta de responderle.

---

### 1. ¿Por qué esto NO es Machine Learning tradicional?
* **Términos clave:**
  * **Datos I.I.D. (Independientes e Idénticamente Distribuidos):** Supuesto del Machine Learning tabular (precios de casas, clientes) donde cada fila es un evento aislado. Si barajas (*shuffle*) los datos, el modelo aprende exactamente igual.
  * **Autocorrelación:** Es la correlación de una variable consigo misma a través del tiempo. El valor de hoy ($y_t$) contiene memoria de ayer ($y_{t-1}$) y de hace un año ($y_{t-12}$).
  * **Data Leakage (Fuga de Información):** Usar información del futuro para predecir el pasado. En ML tradicional se hace *K-Fold Cross-Validation* aleatorio; en series de tiempo eso está terminantemente prohibido porque causaría fuga de datos temporal.
* **El Porqué:**
  El orden cronológico es sagrado. Si barajas una serie temporal, destruyes el **Proceso Generador de Datos (DGP)**. Por eso la validación en series temporales se hace mediante **orígenes móviles (*Rolling Origin*)**, donde el modelo siempre entrena con el pasado y evalúa estrictamente en el futuro ($h=1\dots12$).
* **Cómo responder al profesor:**
  > *"Profesor, una serie temporal viola el supuesto de independencia de las muestras. La estructura de autocorrelación exige respetar la flecha del tiempo. Por eso no usamos K-Fold aleatorio, sino un backtest con origen rodante para garantizar cero fuga de datos".*

---

### 2. Descomposición STL Robusta: Separando la Señal del Ruido
* **Términos clave:**
  * **STL:** *Seasonal and Trend decomposition using LOESS* (Suavizamiento de Regresión Local Ponderada). Modelo aditivo: $Y_t = T_t + S_t + R_t$.
  * **Tendencia ($T_t$):** La dirección suave de fondo a largo plazo. En Pance es casi horizontal (oscila entre 155 y 230 mm/mes, fuerza baja de 0.10).
  * **Estacionalidad ($S_t$):** Patrón periódico que se repite idénticamente cada año ($m=12$, fuerza moderada de 0.53).
  * **Régimen Bimodal:** Dos temporadas de lluvias al año (abril-mayo y octubre-noviembre) y dos temporadas secas (enero-febrero y julio-agosto). Ocurre porque la **Zona de Confluencia Intertropical (ZCIT)** cruza Colombia dos veces al año.
  * **Residuo ($R_t$):** Es la diferencia matemática: $R_t = Y_t - (T_t + S_t)$. En palabras humanas: **es la sorpresa o anomalía climática**.
* **El Porqué de los Atípicos en el Residuo (y NO en la serie original):**
  * *La analogía del abrigo:* Salir con abrigo de invierno en Bogotá en julio es normal; salir con abrigo al mediodía en Barranquilla es una anomalía.
  * En Pance, que caigan **350 mm en abril es normal** (mes lluvioso); pero que caigan **350 mm en agosto (mes seco) es una catástrofe**. Si buscas atípicos en la lluvia cruda, castigarías los meses lluviosos normales y no verías las verdaderas anomalías de los meses secos. El residuo compara cada mes contra su propio estándar estacional.
* **El Porqué de Tukey ($1.5 \times \text{IQR}$) frente a la Desviación Estándar ($\mu \pm 3\sigma$):**
  * La precipitación tiene eventos extremos asimétricos (como abril de 2024 con 577 mm). La media ($\mu$) y la desviación estándar ($\sigma$) son hipersensibles: un solo diluvio infla la media y la desviación de toda la serie, ocultando a los demás atípicos.
  * La mediana y el **Rango Intercuartílico ($\text{IQR} = Q_3 - Q_1$)** son medidas no paramétricas robustas que no se dejan distorsionar por extremos.
* **Cómo responder al profesor:**
  > *"Profesor, descompusimos con STL robusta porque el residuo $R_t$ aísla la verdadera sorpresa climática libre de estacionalidad. Usamos el criterio de Tukey sobre el residuo porque la media y la desviación estándar se inflan ante diluvios extremos, mientras que el IQR es inmune a ese sesgo".*

---

### 3. La Estacionariedad: El Requisito Obligatorio de ARIMA
* **Términos clave:**
  * **Estacionariedad en sentido débil:** Exige tres condiciones matemáticas invariables en el tiempo:
    1. **Media constante:** $\mathbb{E}[y_t] = \mu$ (la serie no tiene rampa ascendente ni descendente).
    2. **Varianza constante:** $\text{Var}(y_t) = \sigma^2$ (las oscilaciones no crecen con los años).
    3. **Autocovarianza invariable:** $\text{Cov}(y_t, y_{t-k}) = \gamma_k$ (la relación entre dos meses depende de cuántos meses de distancia hay entre ellos, no del año en que ocurran).
  * *La analogía:* Un péndulo en una habitación oscilando alrededor de un centro fijo es estacionario. Un cohete acelerando hacia el espacio no es estacionario.
* **El Porqué:**
  Los modelos ARIMA estiman coeficientes fijos ($\phi_1, \dots, \phi_p, \theta_1, \dots, \theta_q$). Si la serie cambia de nivel medio o de varianza con el tiempo, un sistema de ecuaciones con coeficientes constantes no puede modelar el proceso y los pronósticos matemáticamente divergen o pierden validez.
* **Cómo responder al profesor:**
  > *"Profesor, ARIMA exige estacionariedad porque sus parámetros autorregresivos y de medias móviles asumen propiedades probabilísticas estables en el tiempo. Si la media no es constante, el modelo cometería errores crecientes hacia el infinito".*

---

### 4. La Prueba ADF y sus Regresiones (`'ct'` vs `'c'`)
* **Términos clave:**
  * **ADF (Augmented Dickey-Fuller):** Prueba formal para detectar si una serie tiene **raíz unitaria**.
  * **Raíz Unitaria:** Significa que el sistema tiene **memoria infinita** (como una caminata aleatoria): un shock aleatorio hoy altera la media de la serie para siempre. Si NO hay raíz unitaria, el sistema tiene memoria finita y regresa a su nivel de equilibrio.
  * **Hipótesis Nula ($H_0$):** La serie tiene raíz unitaria (es **NO estacionaria**).
  * **Hipótesis Alternativa ($H_1$):** La serie no tiene raíz unitaria (es **estacionaria**).
  * **Regla de decisión:** Rechazamos $H_0$ si el $p\text{-valor} < 0.05$.
* **El Porqué de las opciones `'ct'` y `'c'`:**
  * En la serie original usamos `regression='ct'` (*constant + trend*) porque antes de diferenciar debemos comprobar si la serie tiene raíz unitaria en presencia de una posible tendencia lineal determinista. Dio $p = 0.2092$ (no se rechaza $H_0$; la serie original es no estacionaria).
  * En las series ya diferenciadas usamos `regression='c'` (*constant*) porque la diferenciación ya eliminó cualquier rampa y solo se evalúa si oscila sobre un promedio fijo.
* **Cómo responder al profesor:**
  > *"Profesor, la prueba ADF evalúa la hipótesis nula de raíz unitaria. Usamos 'ct' en la serie original para no confundir una tendencia determinista con una raíz unitaria, y usamos 'c' en las diferenciadas porque la operación de resta ya remueve la tendencia".*

---

### 5. ¿Por qué elegir $d=0, D=1$ y NO $d=1, D=0$? (La Pregunta Reina)
Ambas transformaciones dieron $p\text{-valor} < 0.05$ en el ADF. Sin embargo, elegir $d=1, D=0$ es un grave error técnico por tres razones:
1. **Física del Fenómeno:** La precipitación en Pance **no tiene tendencia secular acumulativa** (no sube año tras año indefinidamente). En cambio, tiene un ciclo estacional rígido de 12 meses. La operación matemáticamente coherente con la física de la cuenca es la diferencia estacional $D=1$ ($y_t - y_{t-12}$).
2. **Sobrediferenciación (*Overdifferencing*):** Si aplicas diferencia regular $d=1$ a una serie sin tendencia, induces autocorrelación negativa artificial en el rezago 1 ($-0.29$) y dejas intacto el ciclo en el rezago 12. Creas ruido espurio y destruyes la estructura real.
3. **Limitación Matemática del ADF:** La prueba ADF estándar **solo detecta raíces unitarias regulares en frecuencia cero**, no raíces unitarias estacionales en frecuencias armónicas ($2\pi / 12$). Que `diff()` dé $p < 0.05$ es un falso amigo: el ADF cree que la serie es estacionaria simplemente porque ya no hay tendencia regular, ignorando que la estacionalidad sigue viva.
* **Cómo responder al profesor:**
  > *"Profesor, aunque el ADF dé $p < 0.05$ en ambos casos, $d=1$ sobrediferencia la serie porque la lluvia no tiene tendencia secular; además, el ADF estándar no evalúa raíces estacionales. Físicamente, la transformación correcta es la diferencia estacional $D=1$, que neutraliza el ciclo anual sin inyectar ruido espurio en rezagos cortos".*

---

### 6. Las Firmas de ACF y PACF: Leyendo los "Rayos X"
* **Términos clave:**
  * **ACF (Función de Autocorrelación):** Mide la correlación entre $y_t$ y sus rezagos $y_{t-k}$, acumulando todos los efectos directos e indirectos.
  * **PACF (Función de Autocorrelación Parcial):** Mide la correlación **directa y pura** entre $y_t$ y $y_{t-k}$, descontando el efecto de todos los rezagos intermedios ($y_{t-1}, \dots, y_{t-k+1}$).
  * **Bandas de Bartlett ($\pm 1.96 / \sqrt{N}$):** Franja de confianza del $95\%$. Cualquier rezago dentro de las bandas se considera estadísticamente ruido blanco (cero).
* **Las Firmas de Libro (Metodología Box-Jenkins):**
  * **Proceso $\mathbf{AR(p)}$:** La PACF se corta bruscamente en el rezago $p$ y la ACF decae exponencialmente o con ondas amortiguadas.
  * **Proceso $\mathbf{MA(q)}$:** La ACF se corta bruscamente en el rezago $q$ y la PACF decae suavemente.
* **El Diagnóstico en Pance sobre la serie con $D=1$ ($w_t = y_t - y_{t-12}$):**
  * En la **ACF**, los rezagos cortos están dentro de las bandas, pero en el rezago estacional 12 aparece un pico negativo aislado ($-0.35$) que luego desaparece.
  * En la **PACF**, la correlación decae gradualmente en múltiplos estacionales (12, 24).
  * **Conclusión teórica:** Es la firma clásica de libro de un **término de media móvil estacional: $Q=1$ con periodo $m=12$**, con $p=0, q=0, P=0$.
* **Cómo responder al profesor:**
  > *"Profesor, la ACF de la serie con $D=1$ mostró un corte abrupto en el rezago 12 mientras la PACF decaía suavemente. Siguiendo la regla de Box-Jenkins, un corte neto en la ACF a la distancia del ciclo estacional identifica directamente un componente de medias móviles estacional $Q=1$".*

---

### 7. ¿Qué hace exactamente la ecuación del modelo $\text{SARIMA}(0,0,0)(0,1,1)_{12}$?
* **La Ecuación Teórica:**
  $$y_t - y_{t-12} = \varepsilon_t + \Theta \varepsilon_{t-12}$$
* **Nuestros Parámetros Calibrados:**
  * $\Theta = -0.853$ (coeficiente `ma.S.L12`, altamente significativo con $p < 0.001$).
  * Despejando el pronóstico esperado ($\hat{y}_t$, asumiendo choque futuro esperado $\varepsilon_t = 0$):
    $$\hat{y}_t = y_{t-12} - 0.853 \cdot \varepsilon_{t-12}$$
* **Significado en Español Humano (La física del modelo):**
  * Para estimar la lluvia de abril de este año, el modelo toma como referencia la lluvia de abril del año anterior ($y_{t-12}$).
  * Si el año anterior ocurrió un choque climático atípico (por ejemplo, llovió 150 mm más de lo normal por una tormenta imprevista, $\varepsilon_{t-12} = +150$), el modelo **no comete el error de proyectar que esa tormenta se repetirá**.
  * Al multiplicar por $\Theta = -0.853$, el modelo le **descuenta el $85.3\%$ de esa anomalía** ($ -0.853 \times 150 \approx -128\text{ mm}$), regresando la predicción hacia la normalidad climatológica de la estación.
  * **Es un mecanismo automático de memoria y amortiguamiento:** confía en el ciclo anual, pero no se deja engañar por los excesos del año pasado.
* **Cómo responder al profesor:**
  > *"Profesor, $\Theta = -0.853$ actúa como un amortiguador estacional: descuenta el 85% de las anomalías climáticas ocurridas en el mismo mes del año anterior, evitando que eventos atípicos contaminen el pronóstico futuro y retornando la serie a su régimen medio".*

---

### 8. Por qué el AIC castiga parámetros y por qué NO compara diferentes $d$ y $D$
* **Términos clave:**
  * **Criterio de Información de Akaike:** $\text{AIC} = 2k - 2\ln L$.
  * **$\ln L$ (Log-verosimilitud):** Mide qué tan bien se ajusta la distribución probabilística del modelo a los datos reales observados. A mayor verosimilitud, mejor ajuste.
  * **$2k$ (Penalización por parsimonia):** $k$ es el número de parámetros del modelo. Cada parámetro adicional te suma $+2$ al AIC.
  * **Principio de Parsimonia (Navaja de Ockham):** Entre dos modelos que explican lo mismo, el más simple es el preferido porque no sobreajusta (*overfitting*).
* **El Porqué NO se pueden comparar modelos con distinto $d$ o $D$ mediante AIC:**
  * Al aplicar una diferencia estacional ($D=1$ con $m=12$), la serie pierde 12 observaciones (pasa de 134 a 122 datos).
  * La verosimilitud $L$ se calcula sobre una muestra distinta y con una variable transformada. Comparar los AIC de dos modelos con diferente número de datos es matemáticamente inválido (es como comparar el consumo de gasolina de un carro con 5 pasajeros contra el mismo carro vacío y sin puertas).
  * Por eso, el orden de diferenciación ($d$ y $D$) se decide primero con la física del proceso y las pruebas de raíz unitaria; el AIC solo se utiliza para comparar modelos que compiten sobre la **misma serie exactamente diferenciada**.
* **Cómo responder al profesor:**
  > *"Profesor, el AIC premia la verosimilitud penalizando con $2k$ cada parámetro adicional para evitar sobreajuste. Sin embargo, no es válido comparar modelos con diferente $d$ o $D$ por AIC porque la diferenciación altera el tamaño muestral y la escala de la densidad de probabilidad".*

---

### 9. Diagnóstico de Residuos, Ruido Blanco y Ljung-Box
* **Términos clave:**
  * **Residuo del Modelo:** $e_t = y_t - \hat{y}_t$ (la diferencia entre lo observado y lo predicho).
  * **Ruido Blanco (White Noise):** Proceso puramente aleatorio con media cero, varianza constante y correlación cero en todos los rezagos.
  * **Prueba de Ljung-Box:** Evalúa conjuntamente si las primeras $h$ autocorrelaciones de los residuos son distintas de cero.
    * $H_0$: Los residuos están incorrelacionados (son ruido blanco, ¡lo deseado!).
    * $H_1$: Queda correlación serial remanente en los errores.
    * Criterio: $p\text{-valor} > 0.05 \implies$ No se rechaza $H_0$ (el modelo pasa la prueba).
* **El Porqué de descartar los primeros 12 meses en el diagnóstico:**
  * El modelo utiliza un retardo estacional de orden 12 ($y_{t-12}$ y $\varepsilon_{t-12}$).
  * Para los primeros 12 meses de la serie no existe un año previo disponible dentro de la ventana muestral; por tanto, esos primeros 12 meses corresponden a un periodo de inicialización o calentamiento (*burn-in*). Incluirlos generaría residuos espurios que distorsionarían las pruebas de hipótesis.
* **Nuestros Resultados:** A 12 meses dio $p = 0.429$ y a 24 meses dio $p = 0.266$. Ambos son holgadamente superiores a 0.05, certificando que los residuos son ruido blanco puro.
* **Cómo responder al profesor:**
  > *"Profesor, un modelo es válido solo si sus residuos son ruido blanco, lo que demuestra que ya extrajo toda la información predecible. Descartamos los primeros 12 meses del test de Ljung-Box porque corresponden a la fase de inicialización estacional del filtro".*

---

### 10. El Backtest Rodante (Rolling Origin) y la Trampa del MAPE
* **Términos clave:**
  * **Rolling Origin (Origen Rodante):** Esquema de validación secuencial en el que el modelo se recalibra o proyecta en múltiples ventanas temporales ($t_0, t_1, \dots$). En nuestro caso evaluamos 13 orígenes proyectando a $h=1\dots12$ meses cada vez.
  * **RMSE (Raíz del Error Cuadrático Medio):** Mide el error promedio ponderando más fuertemente los errores grandes (por elevar al cuadrado).
  * **MAE (Error Absoluto Medio):** Mide el error promedio directo en las unidades físicas de la variable (milímetros de lluvia).
  * **MAPE (Error Porcentual Absoluto Medio):** $\text{MAPE} = \frac{1}{n}\sum |\frac{y_t - \hat{y}_t}{y_t}| \times 100\%$.
* **El Porqué la Validación Rodante supera al split fijo 80/20:**
  * Un corte fijo es vulnerable al clima: si el periodo de prueba cae en un año con Fenómeno de El Niño severo (sequía extraordinaria), el modelo parecerá malo por pura mala suerte climática. La validación con 13 orígenes garantiza que el modelo fue probado en épocas secas, húmedas y de transición.
* **La Trampa del MAPE con Datos de Lluvia:**
  * En meses secos (enero o agosto en Cali), la lluvia real puede ser de apenas **$5\text{ mm}$** ($y_t = 5$).
  * Si el modelo pronostica **$25\text{ mm}$**, el error físico es mínimo: solo $20\text{ mm}$ (un charco menor).
  * Sin embargo, el cálculo porcentual arroja: $\frac{|5 - 25|}{5} \times 100\% = \mathbf{400\%}$.
  * Al promediar, esos porcentajes astronómicos distorsionan el MAPE global (54.31%). Por esa razón, en hidrología y meteorología el MAPE se reporta con salvedades y las decisiones operativas se toman siempre con base en el **MAE ($91.75\text{ mm}$)** y el **RMSE ($113.79\text{ mm}$)**.
* **Cómo responder al profesor:**
  > *"Profesor, evaluamos con 13 orígenes rodantes para medir estabilidad climática real sin sesgo de un solo año. El MAPE se eleva al 54% debido a la división por valores cercanos a cero en estiaje; por eso la superioridad de nuestro modelo se fundamenta en la reducción del 18.4% en MAE y 26.6% en RMSE en milímetros reales".*

---

### 11. ¿Por qué reescalamos los datos con `ESCALA = 100`?
* **Términos clave:**
  * **MLE (Maximum Likelihood Estimation):** Algoritmo numérico que optimiza los parámetros encontrando el máximo de una función hiperdimensional mediante derivadas (gradientes y matriz Hessiana).
  * **Inestabilidad Numérica:** Error de precisión en punto flotante cuando los datos tienen órdenes de magnitud muy dispares.
* **El Porqué:**
  La lluvia en Pance alcanza valores de hasta 577 mm, con varianzas muestrales superiores a $10\,000$. Cuando el algoritmo BFGS intenta optimizar simultáneamente parámetros decimales pequeños ($\Theta \approx -0.85$) junto a varianzas del orden de $10\,000$, las matrices numéricas se malcondicionan y el algoritmo puede fallar en converger.
  Al dividir la serie por 100, la precipitación queda acotada en el rango $[0.05, 5.77]$, logrando una convergencia matemática inmediata, robusta y exacta. Al finalizar, las predicciones y errores se re-multiplican por 100 para entregar métricas en milímetros reales.
* **Cómo responder al profesor:**
  > *"Profesor, la división por 100 es una buena práctica de ingeniería computacional para evitar el mal condicionamiento de la matriz Hessiana en la optimización por máxima verosimilitud. Permite una convergencia rápida y precisa sin alterar en absoluto las propiedades estadísticas del proceso".*

---

## 🎯 RESUMEN EJECUTIVO DE CIFRAS CLAVE
* **Serie:** Precipitación mensual acumulada (mm) en estación CDEA El Topacio (Pance, Cali).
* **Fuente y periodo:** Red hidrometeorológica CVC, **134 meses** (Ene-2015 a Feb-2026).
* **Huecos:** **0 huecos** (cobertura mensual siempre > 90%; regla del 80% no activada).
* **Atípicos:** **7 meses** detectados con $1.5 \times \text{IQR}$ sobre residuo STL robusta ($[-174.5, 172.7]$ mm). **Se conservaron**.
* **Estacionalidad:** Bimodal andina (Abril $+118.6$ mm, Agosto $-125.1$ mm; amplitud $243.7$ mm; fuerza $0.53$).
* **Diferenciación elegida:** **$d=0, D=1$** con periodo $m=12$ (ADF $p=0.0033$).
* **Modelo ganador:** **$\text{SARIMA}(0,0,0)(0,1,1)_{12}$** con AIC **382.0** ($\Theta = -0.853$).
* **Diagnóstico de residuos:** Ljung-Box sin los primeros 12 meses ($h=12: p=0.429$; $h=24: p=0.266$). Ruido blanco.
* **Variable exógena:** Días del mes (28 a 31 días), calendario sin fuga de información.
* **Backtest (13 orígenes móviles, $h=1$ a 12):**
  * **RMSE:** $154.93 \rightarrow 113.79$ mm (**$-26.6\%$** de mejora frente a estacional ingenuo).
  * **MAE:** $112.39 \rightarrow 91.75$ mm (**$-18.4\%$** de mejora, $\approx 21$ mm menos de error por mes).
  * **MAPE:** $43.90\% \rightarrow 54.31\%$ (se infla en meses secos por valores cercanos a 0 mm).

---

## 🗣️ GUION CRONOMETRADO DE LOS 7 MINUTOS

### Minuto 1–2: La Serie y Calidad de Datos (Sección 1)
> *"Buenos días, profesor y compañeros. Nuestro miniproyecto analiza la precipitación mensual de la cuenca del río Pance, medida en la estación CDEA El Topacio y suministrada por la CVC para uso académico.*
> 
> *La serie va de enero de 2015 a febrero de 2026, con **134 meses consecutivos**, superando con creces el mínimo de 60 que exige el curso.*
> 
> *En la verificación de calidad comprobamos que **no hay huecos ni meses faltantes**; la regla del 80% no fue necesaria porque el mes con menor registro tuvo más del 90% de días con datos.*
> 
> *Para los atípicos, aplicamos el criterio de Tukey ($1.5 \times \text{IQR}$) pero **sobre el residuo de la STL robusta**, no sobre la lluvia cruda. Encontramos 7 meses con anomalías climáticas (como abril de 2024 con 577 mm) y **decidimos conservarlos** porque son fenómenos reales de La Niña que el modelo debe aprender a pronosticar. Dejamos advertido en el informe que algunos meses tuvieron fallas de telemetría y se midieron con totales diarios a las 7 a. m."*

---

### Minuto 3: Descomposición STL Robusta (Sección 2)
> *(Mostrar figura `figuras/stl.png`)*
> 
> *"Descompusimos la serie con STL robusta ($m=12$):*
> * *La **estacionalidad (fuerza 0.53)** es bimodal, típica de la región andina: el pico más lluvioso es **abril (+118.6 mm)** y el más seco es **agosto (−125.1 mm)**, con una amplitud de casi 244 mm entre estaciones.*
> * *La **tendencia (fuerza 0.10)** es débil y no tiene una dirección sostenida; oscila entre 155 y 230 mm/mes reflejando los ciclos de El Niño y La Niña. El repunte al final de la serie se debe en parte a un 2025 lluvioso y al efecto de borde del suavizador LOESS.*
> * *El **residuo** tiene varianza alta (7,138), lo que confirma que el clima en Pance tiene una fuerte componente aleatoria que ningún modelo estacional podrá predecir al 100%."*

---

### Minuto 4: Estacionariedad e Identificación (Sección 3)
> *(Mostrar tabla ADF y figura `figuras/acf_pacf.png`)*
> 
> *"Para garantizar estacionariedad aplicamos la prueba ADF:*
> * *La serie original no es estacionaria ($p = 0.2092$ con `'ct'`).*
> * *Al diferenciar, tanto la regular `diff()` ($p \approx 0$) como la estacional `diff(12)` ($p = 0.0033$) pasaron la prueba.*
> 
> *Elegimos **$d=0, D=1$** porque la serie no tiene tendencia secular sino ciclo anual. Diferenciar regular de más (`diff()`) introduce sobrediferenciación, genera una autocorrelación negativa espuria en el rezago 1 y conserva la barra en el rezago 12.*
> 
> *Al graficar ACF y PACF de la serie elegida ($w_t = y_t - y_{t-12}$), observamos una barra negativa aislada en el rezago 12 de la ACF ($-0.35$). Esta es la firma teórica clásica de un **MA estacional ($Q=1$)**."*

---

### Minuto 5: Modelos Clásicos y Diagnóstico (Sección 4)
> *(Mostrar figura `figuras/residuos.png`)*
> 
> *"Para ajustar los modelos dividimos la serie por 100 (`ESCALA = 100`), evitando que la varianza gigante desestabilice el optimizador numérico.*
> 
> *Evaluamos una rejilla de 36 combinaciones por AIC y ganó el modelo más parsimonioso: **$\text{SARIMA}(0,0,0)(0,1,1)_{12}$ con AIC de 382.0** ($\Theta = -0.853$).*
> 
> *Al aplicar la prueba de **Ljung-Box** sobre sus residuos (descartando los primeros 12 meses de inicialización), obtuvimos valores p de **0.429** a 12 rezagos y **0.266** a 24 rezagos. Al ser mayores a 0.05, confirmamos que los residuos son ruido blanco y que el modelo extrajo toda la memoria predecible.*
> 
> *Adicionalmente probamos un **SARIMAX** usando como exógena los **días de cada mes** (28 a 31), variable que se conoce legítimamente por calendario sin fuga de información."*

---

### Minuto 6–7: Backtest y Resultados Finales (Sección 5 y Conclusión)
> *(Mostrar tabla de métricas)*
> 
> *"Evaluamos los modelos con el backtest común del curso: 13 orígenes móviles sobre los últimos 24 meses, pronosticando a 12 pasos:*
> 
> *1. El **estacional ingenuo** superó ampliamente al ingenuo simple, demostrando el peso del ciclo anual.*
> *2. El **SARIMA puro** superó al estacional ingenuo, bajando el RMSE de 154.93 a 117.05 mm.*
> *3. El **SARIMAX con días del mes** obtuvo el mejor desempeño global, con **RMSE de 113.79 mm** y **MAE de 91.75 mm**.*
> 
> *Frente a la mejor línea base, logramos una reducción del **26.6% en RMSE** y del **18.4% en MAE** (más de 20 mm menos de error mensual). El MAPE subió a 54.31% debido a la conocida distorsión de dividir por valores cercanos a cero en meses secos.*
> 
> *En conclusión: la estructura estacional del SARIMA aportó casi toda la ganancia predictiva. Este SARIMA/SARIMAX es la marca de referencia sólida que el Miniproyecto 2 tendrá que superar."*

---

## 🛡️ LAS 7 PREGUNTAS "FIJAS" DEL PROFESOR DELGADO

### 1. ¿Por qué eligieron $d=0, D=1$ y no $d=1, D=0$ si ambos pasaron el ADF?
> *"Profesor, por 3 motivos:*  
> *1. **Física del proceso:** La descomposición STL demostró que no hay tendencia de largo plazo, sino un ciclo anual marcado. La diferencia que corresponde es la estacional.*  
> *2. **Sobrediferenciación:** Al aplicar `diff()`, la serie se sobrediferencia: la ACF muestra una caída artificial negativa en el rezago 1 y la PACF decae negativamente en los primeros 5 rezagos, mientras que la estacionalidad en el rezago 12 sigue viva.*  
> *3. **Diseño del ADF:** La prueba Dickey-Fuller aumentada evalúa raíces unitarias regulares en frecuencia cero, no raíces estacionales. Un p-valor bajo en `diff()` no garantiza que eliminó el ciclo estacional."*

### 2. ¿Por qué buscaron atípicos en el residuo STL y no en la serie original?
> *"Porque en series con fuerte estacionalidad no se puede evaluar un dato sin considerar su época climática. En Pance, 400 mm en abril es normal para la temporada húmeda, pero 400 mm en agosto sería un diluvio insólito. El residuo STL ($y_t - T_t - S_t$) ya descuenta la tendencia y la estacionalidad, permitiendo juzgar si un mes fue verdaderamente anómalo frente a su propio histórico."*

### 3. ¿Por qué usaron cuartiles ($1.5 \times \text{IQR}$) en vez de $\mu \pm 2\sigma$?
> *"Porque la media y la desviación estándar no son métricas robustas. Un aguacero extremo (como los 577 mm de abril de 2024) infla la media de toda la serie y agranda la desviación estándar, haciendo que otros atípicos pasen desapercibidos. Los cuartiles ($Q_1$ y $Q_3$) se basan en rangos de posición y no se dejan distorsionar por valores extremos."*

### 4. ¿Qué significa el parámetro $\Theta = -0.853$ en su modelo?
> *"Es el coeficiente de media móvil estacional ($Q=1$, `ma.S.L12`). Indica que el modelo ajusta el pronóstico del mes actual descontando cerca del 85% del error o sorpresa estacional observada hace 12 meses. Matemáticamente esto hace que el pronóstico converja hacia un patrón anual estable, muy similar a la climatología histórica de cada mes."*

### 5. ¿Por qué en la prueba de Ljung-Box descartaron los primeros 12 meses?
> *"Porque el modelo aplica una diferencia estacional $D=1$ ($m=12$). Para los primeros 12 meses no existe un año previo con el cual contrastar; son observaciones consumidas en inicializar las diferencias y sus residuos no son errores legítimos de pronóstico. Incluirlos contaminaría la evaluación de ruido blanco."*

### 6. ¿Cómo evitaron la fuga de información (data leakage) en el backtest y la exógena?
> *"En el backtest, la función `modelo(entrenamiento, h)` solo usa datos estrictamente anteriores a la fecha de corte. Para la exógena usamos los **días del mes**, que provienen del calendario civil fijo y se conocen con años de antelación. Si hubiésemos usado variables que solo se miden a mes vencido (como la temperatura o el caudal del río), habríamos incurrido en fuga de información."*

### 7. ¿Por qué el MAPE del SARIMA (54.68%) es más alto que el del Estacional Ingenuo (43.90%) si en RMSE y MAE gana el SARIMA?
> *"Es una trampa conocida del MAPE: al dividir el error por el valor real ($|y - \hat{y}| / y$), en meses secos con lluvias de apenas 5 a 10 mm, cualquier error pequeño de unos pocos milímetros se infla a porcentajes del 50% o más. Por esa razón, en meteorología y en el curso, las decisiones se basan en el **RMSE y el MAE**, que miden el error en milímetros reales de lluvia."*

---

## 💻 Comandos Rápidos para Correr en Vivo

Si el profesor pide correr el script en la sustentación:
```bash
# 1. Asegúrate de estar en la carpeta del repositorio
cd "c:\Users\luish\Documents\maestria\segundo semestre\series temporales\miniproyecto 1\st-2026-2-miniproyecto-01"

# 2. Ejecuta el guion
python miniproyecto.py
```
*(El guion tardará ~15 segundos en ejecutar los 13 cortes del backtest y desplegará en consola todas las tablas y métricas que respaldan el informe).*
