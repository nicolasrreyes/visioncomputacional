# Métricas Definidas para OpenCode POC

Este documento define todas las métricas que el dashboard debe poder mostrar.

## Contexto

Las métricas están diseñadas para:
- Demostrar confiabilidad técnica
- Mostrar impacto de negocio
- Validar calidad de detecciones
- Comunicar estado de auditorías ejecutivamente

Todas las métricas deben calcularse desde la estructura de auditoría.

---

## Métricas Principales

### 1. Total Esperado

**Descripción**: Suma de cantidades esperadas según stock para la zona auditada.

**Fórmula**:
```
total_esperado = Σ cantidad_esperada[producto] para todos los productos en la zona
```

**Ejemplo**:
- Estantería A: caja_carton_chica=8, botella_plastica=12
- Total: 20

**Tipo**: Métrica base (no calculada)

---

### 2. Total Detectado

**Descripción**: Suma de cantidades detectadas válidas (confianza >= umbral).

**Fórmula**:
```
total_detectado = Σ conteos[producto] donde confianza >= umbral[producto]
```

**Notas**:
- Solo cuenta detecciones por encima del umbral definido en productos_objetivo.json
- Las detecciones bajo umbral van a "items_a_revisar"

**Ejemplo**:
- Detectadas: caja_carton_chica=7, botella_plastica=12
- Total: 19

---

### 3. Diferencia Total

**Descripción**: Desviación bruta entre detectado y esperado.

**Fórmula**:
```
diferencia_total = total_detectado - total_esperado
```

**Interpretación**:
- 0: Coincidencia perfecta
- Negativo: Faltan productos
- Positivo: Hay productos extras

**Ejemplo**: 19 - 20 = -1 (falta 1 producto)

---

### 4. Cantidad de Discrepancias

**Descripción**: Cantidad de productos cuyo estado operativo NO es "OK".

**Fórmula**:
```
cantidad_discrepancias = CONTAR(discrepancias donde estado_operativo != "OK")
```

**Estados considerados discrepancia**:
- faltante
- sobrante
- revisar

**Ejemplo**: 1 producto con faltante = 1 discrepancia

---

### 5. Porcentaje de Coincidencia

**Descripción**: Qué porcentaje del inventario esperado se verificó correctamente.

**Fórmula**:
```
porcentaje_coincidencia = MAX(0, 100 - (ABS(diferencia_total) / MAX(total_esperado, 1) * 100))
```

**Rango**: 0% a 100%

**Interpretación**:
- 100%: Coincidencia perfecta
- 95-99%: Muy bueno (pequeñas desviaciones)
- 80-94%: Aceptable (requiere revisión)
- <80%: Crítico (revisar zona completa)

**Ejemplo**: 
- total_esperado=20, diferencia=-1
- porcentaje = 100 - (1 / 20 * 100) = 95%

---

### 6. Confianza Promedio

**Descripción**: Promedio de confianza de todas las detecciones válidas.

**Fórmula**:
```
confianza_promedio = Σ confianza[deteccion] / CONTAR(detecciones_validas)
```

**Rango**: 0 a 1

**Interpretación**:
- ≥ 0.75: Excelente confianza
- 0.65-0.74: Buena confianza
- < 0.65: Revisar (posible error en detecciones)

**Ejemplo**: (0.85 + 0.78 + 0.82 + 0.76) / 4 = 0.80

---

### 7. Items a Revisar

**Descripción**: Cantidad de productos detectados con confianza bajo umbral o estado ambiguo.

**Causas**:
- Confianza < umbral del producto
- Producto parcialmente oculto
- Imagen borrosa
- Detecciones superpuestas no resueltas

**Fórmula**:
```
items_a_revisar = CONTAR(detecciones donde estado_operativo="revisar")
```

**Ejemplo**: 2 productos requieren revisión humana

---

### 8. Auditorías con Discrepancias (Histórico)

**Descripción**: Porcentaje de auditorías que tuvieron al menos una discrepancia.

**Fórmula**:
```
pct_auditorias_con_disc = CONTAR(auditorias donde cantidad_discrepancias > 0) / CONTAR(auditorias_totales) * 100
```

**Uso**: Indicador de tendencia y confiabilidad del proceso

**Ejemplo**: 7 de 10 auditorías tuvieron discrepancias = 70%

---

### 9. Tiempo Ahorrado (Métrica Ejecutiva)

**Descripción**: Estimación de tiempo ahorrado vs. conteo manual (POC).

**Fórmula**:
```
tiempo_manual_estimado_min = total_esperado * 0.25  (15 segundos por producto)
tiempo_ia_estimado_min = duracion_proceso_segundos / 60
tiempo_ahorrado_min = tiempo_manual_estimado_min - tiempo_ia_estimado_min
```

**Notas**:
- La fórmula es aproximada para POC
- Ajustar factor multiplicador (0.25) según datos reales
- Presentar como "estimación" no como valor exacto

**Ejemplo**:
- Stock: 20 productos → 5 minutos manual
- Proceso IA: 4 segundos
- Ahorro: ~4.9 minutos

---

## Indicadores Visuales del Dashboard

El dashboard debería mostrar estas métricas en:

### Cards/KPIs (Nivel Zona)
- **Total Esperado**: número grande, color gris
- **Total Detectado**: número grande, color azul
- **Discrepancias**: número grande, color naranja si >0
- **Coincidencia**: porcentaje con barra de progreso (verde si >90%)
- **Confianza Promedio**: porcentaje o decimal (verde si >0.75)

### Tablas
- **Tabla de Discrepancias**: producto, esperado, detectado, diferencia, estado
- **Tabla de Auditorías**: zona, fecha, coincidencia, discrepancias, acción

### Gráficos (si aplica en fase posterior)
- Histórico de coincidencia por zona
- Distribución de estados operativos
- Tendencia de discrepancias

---

## Cálculo de Métricas en Código

### Pseudocódigo Python

```python
def calcular_metricas(detectados, esperados, detecciones):
    """
    detectados: dict {producto_id: cantidad}
    esperados: dict {producto_id: cantidad}
    detecciones: list of detection objects
    """
    
    total_esperado = sum(esperados.values())
    total_detectado = sum(detectados.values())
    diferencia_total = total_detectado - total_esperado
    
    cantidad_discrepancias = len([
        p for p in esperados 
        if estado_operativo(detectados.get(p, 0), esperados[p]) != "OK"
    ])
    
    porcentaje_coincidencia = max(0, 100 - (abs(diferencia_total) / max(total_esperado, 1) * 100))
    
    confianza_promedio = (
        sum(d['confianza'] for d in detecciones) / len(detecciones) 
        if detecciones else 0
    )
    
    items_a_revisar = len([d for d in detecciones if d['confianza'] < umbral])
    
    tiempo_ahorrado = (total_esperado * 0.25) - (tiempo_proceso / 60)
    
    return {
        'total_esperado': total_esperado,
        'total_detectado': total_detectado,
        'diferencia_total': diferencia_total,
        'cantidad_discrepancias': cantidad_discrepancias,
        'porcentaje_coincidencia': round(porcentaje_coincidencia, 2),
        'confianza_promedio': round(confianza_promedio, 3),
        'items_a_revisar': items_a_revisar,
        'tiempo_ahorrado_minutos': round(tiempo_ahorrado, 2)
    }
```

---

## Referencias

- [Criterios de Estado](./criterios_estado.md)
- [Estructura de Auditoría](../data/AUDITORIA_SCHEMA.json)
- [Pruebas, Integración y Métricas de Dashboard](./opencode_pruebas_metricas_dashboard.md)
