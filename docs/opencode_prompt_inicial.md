# Prompt Inicial para OpenCode

Usar este prompt para iniciar el trabajo en OpenCode.

```text
Estamos construyendo un POC para la IACKATON CDA, iniciativa 1: Computer vision para inventarios de productos.

El objetivo es una solucion de auditoria visual de inventario. No queremos solo detectar objetos; queremos comparar lo detectado contra un stock esperado y generar evidencia visual.

Empeza por el Punto 1: definicion del POC.

Lee estos archivos:

- project.md
- docs/opencode_punto_1_definicion_poc.md
- docs/criterios_estado.md
- docs/opencode_plan_accion_mejoras.md
- docs/opencode_pruebas_metricas_dashboard.md

Tu tarea inicial (Punto 1 + Preparacion de Testing y Metricas):

## Fase 1A - Definicion del POC (Datos Base)

1. Crear carpeta data si no existe.
2. Crear data/stock_esperado.csv con al menos 10 registros realistas.
3. Crear data/productos_objetivo.json con los productos objetivo, prompts de deteccion y umbrales iniciales.
4. Crear data/zonas.json con zonas del deposito.
5. Validar que los datos permitan implementar luego el flujo: imagen -> detecciones -> conteo -> comparacion.

## Fase 1B - Preparacion de Infraestructura de Testing (desde el inicio)

6. Crear carpeta tests/fixtures/ con datos de prueba reproducibles:
   - stock_esperado_test.csv (subset realista para pruebas)
   - detecciones_estanteria_a.json (detecciones simuladas)
   - detecciones_con_baja_confianza.json (para validar "revisar")
   - detecciones_vacias.json (para validar errores)

7. Documentar en tests/fixtures/README.md como usar los fixtures.

## Fase 1C - Preparacion de Estructura de Metricas y Dashboard

8. Crear archivo data/AUDITORIA_SCHEMA.json con la estructura esperada de una auditoria:
   - campos basicos: auditoria_id, fecha_hora, zona_id, fuente
   - detecciones: producto_id, label, confianza, bbox
   - conteos: resumen por producto
   - discrepancias: producto_id, diferencia, estado_operativo
   - metricas: total_esperado, total_detectado, porcentaje_coincidencia, confianza_promedio

9. Crear documento docs/METRICAS_DEFINIDAS.md con definicion de:
   - Total esperado
   - Total detectado
   - Cantidad de discrepancias
   - Porcentaje de coincidencia (formula)
   - Confianza promedio
   - Items a revisar

## Restricciones Importantes

- No implementes todavia WebRTC ni camara en vivo.
- No implementes el modelo de vision computacional (usar detecciones simuladas).
- Primero cierra el dominio del POC y asegura que los datos base sean consistentes.
- Mantene el alcance chico, demostrable y orientado a la presentacion ejecutiva.
- Las pruebas y metricas deben poder funcionar con datos simulados sin depender de inferencia real.
```
