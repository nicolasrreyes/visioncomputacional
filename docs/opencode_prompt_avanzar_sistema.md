# Prompt para OpenCode - Avanzar con el Sistema Base

Usar este prompt para continuar despues del Punto 1.

```text
Estamos construyendo un POC para la IACKATON CDA, iniciativa 1: Computer vision para inventarios de productos.

El Punto 1 ya esta avanzado: existen datos base, fixtures, esquema de auditoria y metricas definidas.

Ahora quiero avanzar con el sistema base funcional, sin implementar todavia el modelo real de vision computacional ni WebRTC.

Objetivo de esta fase:

Construir una primera version ejecutable del sistema que use detecciones simuladas para validar el flujo completo:

imagen/fixture -> conteo -> comparacion contra stock -> metricas -> auditoria guardada -> dashboard basico

## Archivos Críticos para esta Fase

### Punto 1 - Base Cerrada
- [docs/opencode_punto_1_definicion_poc.md](./opencode_punto_1_definicion_poc.md) - Definición del POC
- [data/VALIDACION_PUNTO_1.md](../data/VALIDACION_PUNTO_1.md) - Validación de consistencia
- [data/productos_objetivo.json](../data/productos_objetivo.json) - 7 productos con prompts y umbrales
- [data/zonas.json](../data/zonas.json) - 5 zonas del depósito
- [data/stock_esperado.csv](../data/stock_esperado.csv) - 11 registros de stock base

### Testing - Infraestructura Prep
- [tests/fixtures/README.md](../tests/fixtures/README.md) - Guía de uso de fixtures
- [tests/fixtures/stock_esperado_test.csv](../tests/fixtures/stock_esperado_test.csv) - 4 registros para tests
- [tests/fixtures/detecciones_estanteria_a.json](../tests/fixtures/detecciones_estanteria_a.json) - Caso: coincidencia exacta
- [tests/fixtures/detecciones_con_baja_confianza.json](../tests/fixtures/detecciones_con_baja_confianza.json) - Caso: revisar
- [tests/fixtures/detecciones_vacias.json](../tests/fixtures/detecciones_vacias.json) - Caso: error

### Métricas y Esquema
- [docs/METRICAS_DEFINIDAS.md](./METRICAS_DEFINIDAS.md) - 9 métricas documentadas con fórmulas
- [data/AUDITORIA_SCHEMA.json](../data/AUDITORIA_SCHEMA.json) - JSON Schema completo (26 campos)
- [docs/criterios_estado.md](./criterios_estado.md) - Estados operativos y visuales

### Referencia General
- [project.md](../project.md) - Contexto general del proyecto
- [docs/opencode_pruebas_metricas_dashboard.md](./opencode_pruebas_metricas_dashboard.md) - Testing strategy completa
- [docs/opencode_plan_accion_mejoras.md](./opencode_plan_accion_mejoras.md) - Plan de 6 fases

Restricciones importantes:

- No implementes WebRTC todavia.
- No integres todavia Grounding DINO, YOLO-World ni modelos pesados.
- No dependas de internet, GPU ni inferencia real para que el sistema funcione.
- Usa detecciones simuladas desde fixtures para cerrar el flujo funcional.
- Priorizá codigo testeable y simple.
- Si hay que elegir entre demo vistosa y flujo confiable, priorizá flujo confiable.

Tareas principales:

1. Crear estructura base de proyecto Python si todavia no existe.

Estructura sugerida:

app/
  detection/
    counting.py
    mock_inference.py
  inventory/
    loader.py
    compare.py
    schemas.py
  audits/
    repository.py
    metrics.py
  api/
    main.py
    routes_detection.py
dashboard/
  streamlit_app.py
tests/
  unit/
  integration/

Adaptá la estructura si ya existe una mejor en el repo.

2. Implementar carga de configuracion y datos.

Implementar funciones para cargar:

- data/productos_objetivo.json
- data/zonas.json
- data/stock_esperado.csv

Validaciones minimas:

- producto_id existente;
- zona_id existente;
- cantidad_esperada numerica y no negativa;
- prompts y umbral por producto;
- stock filtrable por zona.

3. Implementar conteo de detecciones.

Crear una funcion que reciba detecciones en formato fixture:

[
  {
    "producto_id": "caja_carton_chica",
    "label": "caja carton chica",
    "confianza": 0.87,
    "bbox": [50, 40, 180, 160]
  }
]

La funcion debe:

- agrupar por producto_id;
- aplicar umbral de confianza por producto;
- separar detecciones validas de detecciones a revisar;
- devolver conteos por producto;
- no romper si la lista viene vacia.

4. Implementar comparacion contra stock esperado.

Crear una funcion que reciba:

- zona_id;
- conteos detectados;
- stock esperado filtrado por zona;
- detecciones a revisar.

Debe devolver discrepancias con:

- producto_id;
- cantidad_esperada;
- cantidad_detectada;
- diferencia = cantidad_detectada - cantidad_esperada;
- estado_operativo: OK, faltante, sobrante o revisar;
- confianza_promedio si aplica;
- requiere_revision.

Reglas:

- diferencia 0 -> OK;
- diferencia negativa -> faltante;
- diferencia positiva -> sobrante;
- confianza baja o deteccion dudosa -> revisar;
- producto no esperado pero detectado -> sobrante.

5. Implementar calculo de metricas.

Crear funciones para calcular las 9 metricas documentadas en docs/METRICAS_DEFINIDAS.md:

- total_esperado (Σ cantidad_esperada)
- total_detectado (Σ conteos validos)
- diferencia_total (total_detectado - total_esperado)
- cantidad_discrepancias (productos != OK)
- porcentaje_coincidencia (100 - (abs(diferencia) / max(esperado, 1) * 100))
- confianza_promedio (Σ confianza / n_detecciones)
- items_a_revisar (confianza < umbral)
- tiempo_ahorrado_minutos (total * 0.25 - duracion_segundos/60)
- auditorias_con_discrepancias_pct (historico)

IMPORTANTE: Usar las formulas EXACTAS documentadas en docs/METRICAS_DEFINIDAS.md.
Incluir pseudocódigo Python proporcionado en ese documento.

6. Implementar repositorio simple de auditorias.

Para esta fase puede ser JSON local.

Crear carpeta:

outputs/auditorias/

Cada auditoria debe guardarse como JSON con estructura compatible con data/AUDITORIA_SCHEMA.json.

IMPORTANTE: Validar contra el schema:
- Todos los campos requeridos presentes
- Tipos correctos (string, number, array, object)
- Enums válidos (zona_id, fuente, estado_operativo)
- Rango de confianza 0-1
- Coordenadas de bbox válidas

Debe incluir:

- auditoria_id (unico);
- fecha_hora (ISO 8601);
- zona_id (validado contra data/zonas.json);
- fuente ("imagen", "video" o "camara_viva");
- archivo_original (opcional);
- evidencia_path (opcional);
- duracion_proceso_segundos;
- detecciones (array con producto_id, label, confianza, bbox);
- conteos (dict producto_id -> cantidad);
- discrepancias (array con diferencia, estado_operativo);
- metricas (todas las 9 metricas calculadas).

Implementar funciones:
- guardar_auditoria(auditoria_dict) -> auditoria_id
- cargar_auditoria(auditoria_id) -> auditoria_dict
- listar_auditorias(zona_id=None) -> list[auditoria_id]
- validar_schema_auditoria(auditoria_dict) -> bool

7. Implementar API FastAPI basica.

Crear una API que permita ejecutar una auditoria con detecciones simuladas.

Endpoints sugeridos:

- GET /health
- GET /zonas
- GET /productos
- GET /stock/{zona_id}
- POST /auditorias/simular
- GET /auditorias
- GET /auditorias/{auditoria_id}

Contrato sugerido para POST /auditorias/simular:

Request:

{
  "zona_id": "estanteria_a",
  "fixture": "detecciones_estanteria_a.json",
  "fuente": "imagen"
}

Response:

{
  "auditoria_id": "auditoria_001",
  "zona_id": "estanteria_a",
  "detecciones": [],
  "conteos": {},
  "discrepancias": [],
  "metricas": {},
  "evidencia_path": null
}

8. Implementar dashboard Streamlit basico.

Crear dashboard/dashboard.py o dashboard/streamlit_app.py.

Debe mostrar:

- selector de zona;
- selector de fixture de detecciones;
- boton para simular auditoria;
- KPIs principales:
  - total esperado;
  - total detectado;
  - discrepancias;
  - porcentaje de coincidencia;
  - confianza promedio;
  - items a revisar;
- tabla de discrepancias;
- tabla de auditorias guardadas;
- detalle JSON de la auditoria seleccionada.

Por ahora no hace falta subir imagen real ni mostrar bounding boxes. Eso viene despues.

9. Implementar tests unitarios.

Usar pytest. Los fixtures ya existen en tests/fixtures/.

Tests minimos:

Unit Tests:

- test_loader.py:
  * test_load_stock_esperado() - cargar y validar CSV
  * test_load_productos_objetivo() - cargar JSON con 7 productos
  * test_load_zonas() - cargar JSON con 5 zonas
  * test_load_detecciones_from_fixture() - cargar JSON de detecciones

- test_counting.py:
  * test_count_single_product() - contar 1 producto
  * test_count_multiple_products() - contar 2+ productos
  * test_count_apply_threshold() - aplicar umbral, separar revisar
  * test_count_empty_detections() - detecciones vacías
  * test_count_unknown_product() - producto no en objetivos

- test_compare.py:
  * test_compare_exact_match() - esperado == detectado -> OK
  * test_compare_shortage() - detectado < esperado -> faltante
  * test_compare_surplus() - detectado > esperado -> sobrante
  * test_compare_with_low_confidence() - confianza baja -> revisar
  * test_compare_product_not_in_stock() - producto inesperado -> sobrante

- test_metrics.py:
  * test_metric_total_esperado()
  * test_metric_total_detectado()
  * test_metric_porcentaje_coincidencia()
  * test_metric_confianza_promedio()
  * test_metric_items_a_revisar()

- test_repository.py:
  * test_save_auditoria() - guardar y leer
  * test_auditoria_schema_validation() - validar contra AUDITORIA_SCHEMA.json
  * test_list_auditorias()

Todos los tests deben usar fixtures de tests/fixtures/.

10. Implementar tests de integracion.

Usar pytest + TestClient de FastAPI.

Tests minimos:

- test_integration_full_flow.py:
  * test_flujo_completo_estanteria_a()
    - Cargar detecciones_estanteria_a.json (8 cajas + 12 botellas)
    - Contar: esperamos 8 cajas, 12 botellas
    - Comparar: stock esperado == detectado -> todas OK
    - Calcular metricas: 100% coincidencia, 0.81 confianza promedio
    - Guardar auditoria
    - Verificar JSON guardado
  
  * test_flujo_con_baja_confianza()
    - Cargar detecciones_con_baja_confianza.json
    - Items bajo umbral -> estado "revisar"
    - Metricas incluyen items_a_revisar > 0
  
  * test_flujo_con_detecciones_vacias()
    - Cargar detecciones_vacias.json (array vacío)
    - No debe romper
    - total_detectado = 0
    - Todas las discrepancias -> "faltante"
  
  * test_flujo_con_sobrante()
    - Cargar fixture donde detectamos más de lo esperado
    - Estado: "sobrante"
  
  * test_flujo_con_faltante()
    - Usar stock_esperado_test.csv que tiene caso de faltante
    - Cargar fixture apropiada
    - Estado: "faltante"

- test_api.py:
  * test_get_health() - GET /health -> 200 OK
  * test_get_zonas() - GET /zonas -> lista 5 zonas
  * test_get_productos() - GET /productos -> lista 7 productos
  * test_get_stock_zona() - GET /stock/estanteria_a -> conteos
  * test_post_auditoria_simular() - POST /auditorias/simular -> auditoria completa
  * test_get_auditorias() - GET /auditorias -> lista
  * test_get_auditoria_by_id() - GET /auditorias/{id} -> detalle

Todos los tests deben:
- NO depender de internet ni GPU
- Ejecutar en < 10 segundos total
- Usar fixtures locales
- Reportar pass/fail sin ambigüedad

11. Documentar como correr.

Crear o actualizar README.md con:

- instalacion;
- como correr tests;
- como levantar API;
- como levantar dashboard;
- ejemplo de request para simular auditoria;
- limitaciones actuales;
- proximos pasos.

## Criterios de Aceptación (Fase 2)

Antes de declarar esta fase lista:

### Testing (Obligatorio)
- ✅ Todos los tests unitarios pasan (test_loader, test_counting, test_compare, test_metrics, test_repository)
- ✅ Todos los tests de integración pasan (full flow, edge cases, API)
- ✅ Cobertura > 80% de código principal
- ✅ Tests ejecutan en < 10 segundos sin GPU ni internet
- ✅ Reportar salida de pytest con summary

### Funcionalidad (Obligatorio)
- ✅ Se puede simular una auditoria completa sin modelo real
- ✅ Se guarda JSON de auditoria en outputs/auditorias/ que valida contra AUDITORIA_SCHEMA.json
- ✅ API responde GET /health con 200 OK
- ✅ API responde POST /auditorias/simular con estructura correcta
- ✅ Todas las 9 métricas se calculan correctamente con datos de test
- ✅ Comparación funciona en 3 casos: OK, faltante, sobrante

### Dashboard (Obligatorio)
- ✅ Dashboard se levanta sin errores
- ✅ Muestra selector de zona
- ✅ Muestra selector de fixture
- ✅ Muestra KPIs: esperado, detectado, discrepancias, coincidencia, confianza, revisar
- ✅ Tabla de discrepancias visible
- ✅ Tabla de auditorias guardadas visible

### Documentación (Obligatorio)
- ✅ README.md contiene:
  * Instalación (pip, requirements.txt)
  * Cómo correr tests (pytest command)
  * Cómo levantar API (uvicorn command)
  * Cómo levantar dashboard (streamlit command)
  * Ejemplo de request curl para simular auditoria
  * Limitaciones actuales listadas
  * Próximos pasos claros

### Código (Obligatorio)
- ✅ Estructura coincide con la propuesta (app/, tests/, dashboard/)
- ✅ No hay hardcoding de datos
- ✅ Funciones documentadas con docstrings
- ✅ No hay dependencias de internet, GPU ni modelo real
- ✅ Listo para reemplazar mock_inference.py en siguiente fase

## Orden Recomendado de Implementación (Fase 2)

Seguir estrictamente este orden para evitar bloqueos:

**Semana 1 - Infraestructura**
1. Crear estructura de carpetas (app/, tests/, outputs/auditorias/, etc.)
2. Crear requirements.txt con FastAPI, pytest, streamlit
3. Implementar schemas/modelos de datos simples
4. Implementar loaders (load_stock, load_productos, load_zonas)

**Semana 2 - Lógica Core**
5. Implementar counting.py (agrupar, aplicar umbral, separar revisar)
6. Implementar compare.py (calcular estado operativo, diferencias)
7. Implementar metrics.py (9 métricas con fórmulas exactas)
8. Implementar repository.py (guardar/leer auditorias con validación schema)

**Semana 3 - API y Dashboard**
9. Implementar flujo orquestador que integra todo
10. Agregar FastAPI con 7 endpoints sugeridos
11. Agregar dashboard Streamlit básico con KPIs y tablas
12. Actualizar README.md con instrucciones completas

**Semana 4 - Testing y Cierre**
13. Implementar tests unitarios (5 archivos de test)
14. Implementar tests de integración (5 casos de flujo)
15. Ejecutar y reportar resultados de pytest
16. Validar todos los criterios de aceptación

---

## Validación Final Requerida

Antes de reportar completado:

**Ejecutar estos comandos y reportar salida:**

```bash
# 1. Tests unitarios
pytest tests/unit/ -v --tb=short

# 2. Tests de integración
pytest tests/integration/ -v --tb=short

# 3. Cobertura
pytest --cov=app tests/ --cov-report=term-missing

# 4. Health check API
curl http://localhost:8000/health

# 5. Simular auditoria
curl -X POST http://localhost:8000/auditorias/simular \
  -H "Content-Type: application/json" \
  -d '{"zona_id": "estanteria_a", "fixture": "detecciones_estanteria_a.json", "fuente": "imagen"}'

# 6. Verificar auditoria guardada
ls -la outputs/auditorias/
```

**Reportar:**
- Salida de pytest (todos los tests deben pasar)
- Cobertura (target: > 80%)
- Screenshot o descripción del dashboard
- JSON de auditoria guardada (verificar estructura)

No cierres la tarea hasta ejecutar los tests y reportar el resultado.
```

