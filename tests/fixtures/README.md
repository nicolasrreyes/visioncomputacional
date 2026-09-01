# Fixtures para Pruebas - OpenCode POC

Esta carpeta contiene datos de prueba reproducibles para validar la lógica del sistema sin depender del modelo de visión computacional.

## Uso General

Los fixtures están diseñados para:
- Tests unitarios de conteo y comparación
- Tests de integración con detecciones simuladas
- Validación de cálculo de métricas
- Validación de persistencia de auditorías

## Archivos Disponibles

### 1. `stock_esperado_test.csv`
Subset del stock principal optimizado para pruebas. Contiene:
- 5 productos en 2 zonas
- Datos simples y predecibles para validar lógica

**Uso**: Cargar en tests como base de comparación

### 2. `detecciones_estanteria_a.json`
Detecciones simuladas para la zona Estantería A.

Estructura:
```json
[
  {
    "producto_id": "string",
    "label": "string",
    "confianza": float (0-1),
    "bbox": [x, y, width, height]
  }
]
```

**Casos de prueba**:
- Coincidencia exacta (detectado == esperado)
- Faltante (detectado < esperado)
- Sobrante (detectado > esperado)

### 3. `detecciones_con_baja_confianza.json`
Detecciones donde la confianza está por debajo del umbral.

**Usa para validar**: Estado "revisar", filtrado por umbral

### 4. `detecciones_vacias.json`
Lista vacía o mínima.

**Usa para validar**: Manejo de error, ausencia de detecciones

## Estructura Base de Fixture

Cada fixture de detecciones sigue este patrón:

```json
{
  "auditoria_id": "test_001",
  "zona_id": "estanteria_a",
  "timestamp": "2026-09-01T12:00:00",
  "detecciones": [
    {
      "producto_id": "caja_carton_chica",
      "label": "caja carton chica",
      "confianza": 0.85,
      "bbox": [50, 40, 150, 120]
    }
  ]
}
```

## Cómo Usar en Tests

### Python - pytest
```python
import json

@pytest.fixture
def detecciones_test():
    with open('tests/fixtures/detecciones_estanteria_a.json') as f:
        return json.load(f)

def test_conteo_simple(detecciones_test):
    conteos = contar_detecciones(detecciones_test['detecciones'])
    assert conteos['caja_carton_chica'] == 2
```

### Cargar Stock Esperado
```python
import csv

def load_stock_test(zona_id):
    datos = {}
    with open('tests/fixtures/stock_esperado_test.csv') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['zona_id'] == zona_id:
                datos[row['producto_id']] = int(row['cantidad_esperada'])
    return datos
```

## Mantenimiento

- Actualizar fixtures si cambian los productos objetivo o zonas
- Mantener comentarios con casos de prueba que cada fixture cubre
- Versionar fixtures junto con cambios de esquema de auditoría

## Referencia Cruzada

Ver [docs/opencode_pruebas_metricas_dashboard.md](../../docs/opencode_pruebas_metricas_dashboard.md) para:
- Definición de tests unitarios esperados
- Definición de tests de integración
- Estructura de auditoría persistida
