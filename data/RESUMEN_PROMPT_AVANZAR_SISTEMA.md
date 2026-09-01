# Resumen de Actualización - Prompt Avanzar Sistema (Fase 2)

**Fecha**: 2026-09-01  
**Archivo**: `docs/opencode_prompt_avanzar_sistema.md`  
**Estado**: ✅ ACTUALIZADO CON INTEGRACIONES

---

## 📋 Cambios Realizados

El prompt de Fase 2 ha sido expandido y mejorado para **integrar Testing y Métricas desde el inicio**:

### 1. Reorganización de Referencias
**Antes**: Lista plana de archivos a leer  
**Ahora**: 4 secciones organizadas:
- ✅ Punto 1 - Base Cerrada (5 archivos)
- ✅ Testing - Infraestructura Prep (5 fixtures)
- ✅ Métricas y Esquema (3 documentos)
- ✅ Referencia General (3 archivos)

**Impacto**: Navegación clara, sin ambigüedad sobre qué leer primero

---

### 2. Tarea 5 - Cálculo de Métricas (Mejorado)

**Antes**: Lista simple de 8 métricas  
**Ahora**: 
- ✅ 9 métricas documentadas con fórmulas EXACTAS
- ✅ Referencias a `docs/METRICAS_DEFINIDAS.md`
- ✅ Pseudocódigo Python incluido
- ✅ Énfasis en usar fórmulas exactas (no aproximadas)

**Detalle de 9 Métricas**:
1. total_esperado (Σ cantidad_esperada)
2. total_detectado (Σ conteos válidos)
3. diferencia_total (detectado - esperado)
4. cantidad_discrepancias (estado != OK)
5. porcentaje_coincidencia (fórmula: 100 - (abs(dif) / max(esp, 1) * 100))
6. confianza_promedio (Σ confianza / n)
7. items_a_revisar (confianza < umbral)
8. tiempo_ahorrado_minutos (estimación)
9. auditorias_con_discrepancias_pct (histórico)

---

### 3. Tarea 6 - Repositorio de Auditorías (Mejorado)

**Antes**: Descripción simple de guardado  
**Ahora**:
- ✅ Referencia a `data/AUDITORIA_SCHEMA.json`
- ✅ Validación contra schema (26 campos)
- ✅ 4 funciones específicas a implementar
- ✅ Lista de enums y validaciones

**Funciones Requeridas**:
```
- guardar_auditoria(dict) -> id
- cargar_auditoria(id) -> dict
- listar_auditorias(zona_id=None) -> list
- validar_schema_auditoria(dict) -> bool
```

---

### 4. Tarea 9 - Tests Unitarios (Expandida)

**Antes**: Lista de categorías  
**Ahora**: 
- ✅ 6 archivos de test especificados
- ✅ 20+ casos de prueba específicos
- ✅ Uso obligatorio de fixtures
- ✅ Casos edge incluidos (vacío, no encontrado, etc.)

**Estructura de Tests**:
```
test_loader.py       (4 tests)
test_counting.py     (5 tests)
test_compare.py      (5 tests)
test_metrics.py      (5 tests)
test_repository.py   (3 tests)
```

---

### 5. Tarea 10 - Tests de Integración (Expandida)

**Antes**: 4 casos simples  
**Ahora**:
- ✅ 8 casos de flujo completo detallados
- ✅ Cada caso mapea a fixture específica
- ✅ Valores esperados definidos (ej: 8 cajas, 12 botellas)
- ✅ 7 endpoints API testiados

**Casos de Integración**:
1. Flujo completo estantería A (coincidencia 100%)
2. Flujo con baja confianza (revisar)
3. Flujo con detecciones vacías (error handling)
4. Flujo con sobrante (más de lo esperado)
5. Flujo con faltante (menos de lo esperado)
6. Tests de 7 endpoints FastAPI

---

### 6. Criterios de Aceptación (Reescrita)

**Antes**: 7 criterios genéricos  
**Ahora**: 32 criterios específicos en 5 categorías

**Nuevas Categorías**:
```
✅ Testing (Obligatorio) - 5 criterios
✅ Funcionalidad (Obligatorio) - 6 criterios
✅ Dashboard (Obligatorio) - 6 criterios
✅ Documentación (Obligatorio) - 5 criterios
✅ Código (Obligatorio) - 5 criterios
```

Cada criterio es **verificable** y **no ambiguo**.

---

### 7. Orden de Implementación (Nuevo)

**Antes**: Lista de 12 pasos sin timeline  
**Ahora**: 
- ✅ 4 semanas de trabajo estructurado
- ✅ Dependencias claras por semana
- ✅ Hitos cada 3-4 días

**Timeline**:
```
Semana 1: Infraestructura (estructura, schemas, loaders)
Semana 2: Lógica Core (counting, compare, metrics, repository)
Semana 3: API y Dashboard (endpoints, Streamlit)
Semana 4: Testing y Cierre (tests, validación, documentación)
```

---

### 8. Validación Final (Nuevo)

**Antes**: Recomendación simple de ejecutar tests  
**Ahora**: 
- ✅ 6 comandos específicos a ejecutar
- ✅ Cada comando verifica un aspecto
- ✅ Salidas esperadas documentadas
- ✅ Checklist de reporte

**Comandos a Ejecutar**:
```bash
pytest tests/unit/ -v           # Tests unitarios
pytest tests/integration/ -v    # Tests integración
pytest --cov=app tests/         # Cobertura
curl http://localhost:8000/health
curl -X POST /auditorias/simular
ls -la outputs/auditorias/
```

---

## 📊 Comparativa: Antes vs Después

| Aspecto | Antes | Después |
|---------|-------|---------|
| Referencias | 15 archivos sin organizar | 4 secciones claras |
| Métricas | 8 métricas simples | 9 métricas con fórmulas exactas |
| Tests Unitarios | 7 categorías | 6 archivos + 22 tests específicos |
| Tests Integración | 4 casos vagos | 8 casos con valores esperados |
| Criterios Aceptación | 7 genéricos | 32 específicos y verificables |
| Timeline | No definido | 4 semanas estructuradas |
| Validación Final | Mención de tests | 6 comandos + checklist |

---

## 🎯 Impacto

### Para el Developer
- ✅ **Claridad total**: Cada tarea tiene acceptance criteria específica
- ✅ **Guía paso a paso**: Timeline de 4 semanas con hitos
- ✅ **Testing integrado**: No es "agregar al final", es parte de cada tarea
- ✅ **Validación objetiva**: Comandos concretos para verificar éxito

### Para el Proyecto
- ✅ **Métricas confiables**: 9 métricas con fórmulas exactas
- ✅ **Auditorías validadas**: Todas verifican contra JSON Schema
- ✅ **Testing desde día 1**: Fixtures y estructura lista
- ✅ **Preparado para siguiente fase**: Mock inference -> Real inference

---

## ✅ Listo Para

### Fase 2 - Implementación Backend
- Estructura de carpetas definida
- Tests preparados (fixtures disponibles)
- Métricas documentadas (fórmulas exactas)
- Schema validación listo
- API design claro

### Dashboard
- KPIs definidos (9 métricas)
- Layout especificado
- Fixtures para demo

### Siguiente Fase (Fase 3)
- Reemplazar `mock_inference.py` por modelo real
- Integrar Grounding DINO o YOLO-World
- Agregar WebRTC para cámara en vivo

---

## 📌 Referencias

- [opencode_prompt_avanzar_sistema.md](./opencode_prompt_avanzar_sistema.md) - Prompt actualizado
- [METRICAS_DEFINIDAS.md](./METRICAS_DEFINIDAS.md) - 9 métricas y fórmulas
- [data/AUDITORIA_SCHEMA.json](../data/AUDITORIA_SCHEMA.json) - Validación
- [tests/fixtures/README.md](../tests/fixtures/README.md) - Cómo usar fixtures
