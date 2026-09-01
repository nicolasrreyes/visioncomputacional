# OpenCode - Pruebas, Integracion y Metricas de Dashboard

## Proposito

Este documento agrega el contexto necesario para que el proyecto se construya con pruebas desde el inicio y quede preparado para mostrar metricas utiles en un dashboard ejecutivo.

El foco no es solo que el sistema "funcione", sino que pueda demostrar:

- confiabilidad tecnica;
- trazabilidad de resultados;
- impacto de negocio;
- calidad de detecciones;
- estado de auditorias de inventario.

## Alcance

Este archivo complementa:

- `docs/opencode_punto_1_definicion_poc.md`
- `docs/criterios_estado.md`
- `docs/opencode_plan_accion_mejoras.md`

La implementacion debe contemplar desde el inicio:

- tests unitarios;
- tests de integracion;
- datos de prueba reproducibles;
- estructura de metricas;
- soporte para dashboard;
- evidencia visual asociada a auditorias.

## Principios de Testing

Las pruebas deben validar principalmente la logica de negocio y los contratos entre componentes.

No depender de que el modelo de vision computacional sea perfecto para que los tests pasen. Para pruebas automatizadas, usar detecciones simuladas o fixtures.

Separar:

- logica pura testeable;
- integracion backend/frontend;
- inferencia real del modelo;
- persistencia de auditorias;
- generacion de metricas.

## Tests Unitarios Recomendados

### 1. Comparacion contra stock esperado

Validar la funcion que compara cantidades esperadas contra cantidades detectadas.

Casos minimos:

- esperado igual a detectado -> `OK`;
- esperado mayor a detectado -> `faltante`;
- esperado menor a detectado -> `sobrante`;
- deteccion con confianza baja -> `revisar`;
- producto detectado sin stock esperado para esa zona -> `sobrante`;
- producto esperado no detectado -> `faltante`.

Ejemplo de entrada:

```json
{
  "zona_id": "estanteria_a",
  "esperado": {
    "caja_carton_chica": 8,
    "botella_plastica": 12
  },
  "detectado": {
    "caja_carton_chica": 7,
    "botella_plastica": 12
  }
}
```

Resultado esperado:

```json
[
  {
    "producto_id": "caja_carton_chica",
    "estado_operativo": "faltante",
    "diferencia": -1
  },
  {
    "producto_id": "botella_plastica",
    "estado_operativo": "OK",
    "diferencia": 0
  }
]
```

### 2. Conteo de detecciones

Validar que una lista de detecciones se convierta correctamente en conteos por producto.

Casos minimos:

- varias detecciones de la misma clase;
- detecciones de clases distintas;
- detecciones con confianza inferior al umbral;
- lista vacia;
- clase desconocida.

### 3. Validacion de umbrales

Validar que cada producto tenga un umbral inicial y que se respete al contar.

Casos minimos:

- confianza igual al umbral cuenta;
- confianza mayor al umbral cuenta;
- confianza menor al umbral no cuenta o queda en revision;
- producto sin umbral usa un valor por defecto.

### 4. Normalizacion de nombres

Validar que nombres de productos y zonas se manejen de forma consistente.

Casos minimos:

- espacios;
- mayusculas/minusculas;
- tildes si aparecen en inputs de usuario;
- ids esperados en snake_case.

### 5. Calculo de metricas

Validar funciones de metricas:

- total esperado;
- total detectado;
- cantidad de discrepancias;
- porcentaje de coincidencia;
- confianza promedio;
- cantidad de items a revisar.

### 6. Persistencia de auditorias

Si se usa SQLite, JSON o CSV, validar:

- creacion de auditoria;
- guardado de resultados;
- asociacion con zona;
- asociacion con evidencia;
- lectura posterior para dashboard.

## Tests de Integracion Recomendados

### 1. Flujo completo con imagen y detecciones simuladas

Validar el flujo:

```text
imagen de prueba -> endpoint backend -> detecciones simuladas -> conteo -> comparacion -> auditoria guardada
```

No depender del modelo real. Mockear la funcion de inferencia para devolver detecciones conocidas.

### 2. Endpoint de deteccion

Validar:

- recibe imagen valida;
- rechaza archivo invalido;
- responde JSON con estructura esperada;
- incluye bounding boxes;
- incluye confianza;
- incluye producto detectado;
- devuelve error claro si falta zona.

Contrato sugerido de respuesta:

```json
{
  "auditoria_id": "auditoria_001",
  "zona_id": "estanteria_a",
  "detecciones": [
    {
      "producto_id": "caja_carton_chica",
      "label": "caja carton chica",
      "confianza": 0.82,
      "bbox": [120, 80, 240, 180]
    }
  ],
  "conteos": {
    "caja_carton_chica": 1
  },
  "discrepancias": [
    {
      "producto_id": "caja_carton_chica",
      "cantidad_esperada": 8,
      "cantidad_detectada": 1,
      "diferencia": -7,
      "estado_operativo": "faltante"
    }
  ],
  "metricas": {
    "total_esperado": 8,
    "total_detectado": 1,
    "cantidad_discrepancias": 1,
    "porcentaje_coincidencia": 12.5,
    "confianza_promedio": 0.82,
    "items_a_revisar": 0
  },
  "evidencia_path": "outputs/auditoria_001.jpg"
}
```

### 3. Dashboard consume auditorias guardadas

Validar que el dashboard pueda leer auditorias existentes y construir:

- tabla de auditorias;
- tabla de discrepancias;
- indicadores principales;
- enlace o preview de evidencia.

### 4. Flujo de error

Validar:

- imagen corrupta;
- zona inexistente;
- producto desconocido;
- stock esperado vacio;
- ausencia de detecciones;
- error controlado de inferencia.

El sistema debe devolver mensajes claros y no romper el dashboard.

## Datos de Prueba

Crear una carpeta:

```text
tests/fixtures/
```

Contenido sugerido:

- `stock_esperado_test.csv`
- `productos_objetivo_test.json`
- `zonas_test.json`
- `detecciones_estanteria_a.json`
- `detecciones_con_baja_confianza.json`
- `detecciones_vacias.json`

Las detecciones de prueba deben ser JSON simples y reproducibles.

Ejemplo:

```json
[
  {
    "producto_id": "caja_carton_chica",
    "label": "caja carton chica",
    "confianza": 0.87,
    "bbox": [50, 40, 180, 160]
  },
  {
    "producto_id": "caja_carton_chica",
    "label": "caja carton chica",
    "confianza": 0.79,
    "bbox": [210, 45, 340, 170]
  },
  {
    "producto_id": "botella_plastica",
    "label": "botella plastica",
    "confianza": 0.68,
    "bbox": [380, 90, 430, 220]
  }
]
```

## Metricas para Dashboard

El dashboard debe estar preparado para mostrar metricas a nivel de:

- auditoria individual;
- zona;
- producto;
- historico general.

## Metricas Principales

### Total esperado

Suma de cantidades esperadas segun stock para la zona auditada.

### Total detectado

Suma de cantidades detectadas validas.

### Diferencia total

```text
diferencia_total = total_detectado - total_esperado
```

### Cantidad de discrepancias

Cantidad de productos cuyo estado operativo no es `OK`.

### Porcentaje de coincidencia

Formula sugerida:

```text
porcentaje_coincidencia = max(0, 100 - (abs(diferencia_total) / max(total_esperado, 1) * 100))
```

Nota: para una version posterior, calcular coincidencia por producto y promediar.

### Confianza promedio

Promedio de confianza de detecciones validas.

### Items a revisar

Cantidad de productos o detecciones marcadas como `revisar`.

### Auditorias con discrepancias

Porcentaje de auditorias historicas que tuvieron al menos una discrepancia.

### Tiempo estimado ahorrado

Metrica ejecutiva para presentacion.

Formula inicial sugerida:

```text
tiempo_manual_estimado_min = total_esperado * 0.25
tiempo_ia_estimado_min = duracion_proceso_segundos / 60
tiempo_ahorrado_min = tiempo_manual_estimado_min - tiempo_ia_estimado_min
```

Esta formula es aproximada y debe presentarse como estimacion de POC.

## Indicadores Visuales del Dashboard

El dashboard deberia incluir:

- card o metrica de total esperado;
- card o metrica de total detectado;
- card o metrica de discrepancias;
- card o metrica de coincidencia;
- card o metrica de confianza promedio;
- tabla de discrepancias;
- tabla de auditorias;
- visualizacion de evidencia;
- filtro por zona;
- filtro por estado operativo;
- filtro por producto.

## Estructura Sugerida de Auditoria

Cada auditoria guardada deberia tener:

```json
{
  "auditoria_id": "auditoria_001",
  "fecha_hora": "2026-09-01T14:30:00",
  "zona_id": "estanteria_a",
  "fuente": "imagen",
  "archivo_original": "inputs/estanteria_a_001.jpg",
  "evidencia_path": "outputs/auditoria_001_overlay.jpg",
  "duracion_proceso_segundos": 4.2,
  "detecciones": [],
  "conteos": {},
  "discrepancias": [],
  "metricas": {}
}
```

## Recomendacion de Organizacion de Codigo

Si el proyecto usa Python, separar modulos asi:

```text
app/
  detection/
    inference.py
    counting.py
  inventory/
    loader.py
    compare.py
    schemas.py
  audits/
    repository.py
    metrics.py
  api/
    routes_detection.py
tests/
  unit/
    test_counting.py
    test_compare.py
    test_metrics.py
    test_loader.py
  integration/
    test_detection_flow.py
    test_audit_repository.py
  fixtures/
```

Adaptar nombres a la estructura real del proyecto si ya existe.

## Definicion de Terminado

Esta mejora se considera lista cuando:

- existen fixtures de prueba;
- hay tests unitarios para conteo, comparacion y metricas;
- hay al menos un test de integracion del flujo con detecciones simuladas;
- las respuestas del backend incluyen metricas;
- las auditorias guardadas incluyen evidencia, discrepancias y metricas;
- el dashboard puede mostrar metricas aunque todavia no exista el modelo final;
- los tests no dependen de internet, GPU ni inferencia real.

