# Survey Population Bot

Rellena formularios web automáticamente a partir de un CSV de datos
demográficos. Si a una fila le falta un campo, **genera un valor sintético y lo
deja anotado** en vez de fallar en silencio.

## Cómo funciona

- **pandas** lee `population_data.csv`.
- **Playwright** (síncrono) navega y rellena el formulario.
- Cada dato inventado se escribe en `warning.log` por un logger aparte
  (`synthetic_warnings`), separado del log normal.

Ese segundo logger es la parte que importa: al terminar sabes exactamente qué
respuestas eran reales y cuáles se rellenaron solas.

## Empezar

```bash
pip install -r requirements.txt
python bot.py
```

## Estado y siguiente paso

Funciona con un CSV estático. La hoja de ruta está en
[`FUTURE_PLAN.md`](FUTURE_PLAN.md).

## Aviso

Está pensado para **poblar formularios propios** (pruebas de carga, QA de
formularios, datos de ejemplo). Enviar respuestas sintéticas a encuestas ajenas
contamina los datos de quien las hizo.
