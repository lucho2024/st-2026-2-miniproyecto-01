# datos

La serie del grupo va en esta carpeta, en CSV. Llene esta ficha y borre la
serie de ejemplo cuando ya no la use.

| Campo | Valor |
|---|---|
| Archivo | `pance_mensual.csv` |
| Qué mide | Precipitación mensual acumulada (mm) en la estación CDEA El Topacio (código 2629020601), cuenca del río Pance (Cali, Valle del Cauca) |
| Fuente | Corporación Autónoma Regional del Valle del Cauca (CVC), red de telemetría hidrometeorológica ([cvc.gov.co](https://www.cvc.gov.co)). Datos suministrados por la CVC por correo electrónico |
| Licencia | Uso académico autorizado por la CVC; se cita a la CVC como fuente. No es una licencia abierta |
| Frecuencia | mensual |
| Construcción | `preparar_serie.py` une los archivos `EXPORT_CPANCE_PRECIP_*.xls` (telemetría cada 10 minutos y, en días con falla del sensor, totales diarios a las 07:00), quita duplicados y suma por mes. Un mes con menos del 80 % de días con datos queda vacío; la regla no se activó |
| Periodo | 2015-01 a 2026-02 (134 observaciones) |
| Columna de fecha | `mes` (formato `AAAA-MM`) |
| Columna que se pronostica | `valor` (mm/mes) |

## Serie de ejemplo

`air_passengers.csv`: pasajeros mensuales de una aerolínea entre 1949 y 1960,
la serie clásica de Box y Jenkins, tomada de Kaggle
(`rakannimer/air-passengers`). Solo sirve para comprobar que el guion corre;
el miniproyecto se hace con la serie del grupo.
