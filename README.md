# Auditoria Visual de Inventario

POC para la IACKATON CDA, iniciativa 1: computer vision para inventarios de productos.

El sistema actual valida el flujo base con detecciones simuladas:

```text
fixture de detecciones -> conteo -> comparacion contra stock -> metricas -> auditoria guardada -> dashboard
```

Todavia no integra modelos reales de vision computacional ni WebRTC. Esa decision es intencional: primero se cierra el flujo operativo y testeable.

## Estructura

```text
app/
  api/
  audits/
  detection/
  inventory/
dashboard/
data/
docs/
tests/
```

## Instalacion

```bash
python -m pip install -r requirements.txt
```

## Ejecutar Tests

```bash
python -m pytest -q
```

## Levantar API

```bash
python -m uvicorn app.api.main:app --reload
```

Endpoints principales:

- `GET /health`
- `GET /zonas`
- `GET /productos`
- `GET /stock/{zona_id}`
- `POST /auditorias/simular`
- `GET /auditorias`
- `GET /auditorias/{auditoria_id}`

Ejemplo de simulacion:

```bash
curl -X POST http://127.0.0.1:8000/auditorias/simular ^
  -H "Content-Type: application/json" ^
  -d "{\"zona_id\":\"estanteria_a\",\"fixture\":\"detecciones_estanteria_a.json\",\"fuente\":\"imagen\"}"
```

## Levantar Dashboard

```bash
python -m streamlit run dashboard/streamlit_app.py
```

El dashboard permite:

- seleccionar zona;
- seleccionar fixture;
- simular auditoria;
- ver KPIs;
- ver discrepancias;
- listar auditorias guardadas;
- inspeccionar el JSON de una auditoria.

## Auditorias

Las auditorias simuladas se guardan en:

```text
outputs/auditorias/
```

Cada auditoria incluye:

- detecciones;
- conteos;
- discrepancias;
- metricas;
- zona;
- fecha/hora;
- fuente.

## Proximo Paso

La siguiente fase recomendada es agregar carga real de imagen y generar evidencia visual con bounding boxes, manteniendo `mock_inference.py` como fallback para tests y demo controlada.

