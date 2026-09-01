# OpenCode - Plan de Accion de Mejoras

## Objetivo General

Transformar el proyecto en una solucion demostrable de auditoria visual de inventario, alineada con la iniciativa 1 de la IACKATON CDA.

La prioridad es construir un POC serio y defendible, no una demo aislada de deteccion.

## Prioridades

1. Definicion del POC y datos base.
2. Flujo con imagen estatica.
3. Comparacion contra stock esperado.
4. Evidencia visual con bounding boxes.
5. Dashboard de discrepancias.
6. Carga de video corto.
7. Camara en vivo como mejora avanzada.
8. Revision humana y metricas ejecutivas.

## Fase 1 - Definicion del POC

Objetivo: dejar configurado el dominio inicial.

Tareas:

- crear `data/stock_esperado.csv`;
- crear `data/productos_objetivo.json`;
- crear `data/zonas.json`;
- completar `docs/criterios_estado.md`;
- documentar reglas de comparacion;
- dejar al menos 10 registros realistas de stock esperado.

Resultado esperado:

```text
El proyecto sabe que productos buscar, en que zonas, con que prompts y contra que stock comparar.
```

## Fase 2 - Deteccion por Imagen

Objetivo: implementar el flujo minimo funcional.

Tareas:

- crear endpoint backend para subir una imagen;
- ejecutar deteccion sobre la imagen;
- devolver clases, confianza y bounding boxes;
- contar detecciones por producto;
- dibujar bounding boxes sobre la imagen;
- guardar imagen procesada como evidencia.

Resultado esperado:

```text
Imagen -> detecciones -> conteo -> evidencia
```

## Fase 3 - Comparacion Contra Stock

Objetivo: convertir detecciones en informacion accionable.

Tareas:

- seleccionar zona antes de procesar;
- cargar stock esperado de esa zona;
- comparar cantidad esperada contra cantidad detectada;
- calcular diferencia;
- clasificar resultado como OK, faltante, sobrante o revisar;
- guardar auditoria.

Resultado esperado:

```text
Auditoria visual con discrepancias por producto y zona.
```

## Fase 4 - Dashboard

Objetivo: mostrar resultados de forma ejecutiva.

Tareas:

- listar auditorias realizadas;
- mostrar tabla de discrepancias;
- mostrar evidencia visual;
- mostrar metricas simples;
- permitir filtrar por zona, producto y estado operativo.

Metricas recomendadas:

- total de productos esperados;
- total de productos detectados;
- cantidad de discrepancias;
- porcentaje de coincidencia;
- confianza promedio;
- tiempo estimado de auditoria.

## Fase 5 - Video Corto

Objetivo: sumar evidencia dinamica sin depender de camara en vivo.

Tareas:

- permitir subir video corto;
- procesar 1 frame por segundo;
- detectar productos en cada frame;
- consolidar conteos;
- guardar snapshots relevantes;
- mostrar resumen final.

Resultado esperado:

```text
Video corto -> frames procesados -> conteo consolidado -> evidencia.
```

## Fase 6 - Camara en Vivo

Objetivo: sumar una demo avanzada.

Tareas:

- implementar captura desde navegador;
- procesar frames cada 500 ms o 1 segundo;
- enviar resultados al frontend;
- dibujar overlay en vivo;
- mantener carga de imagen/video como respaldo.

Nota:

Esta fase debe hacerse despues de que imagen y video corto funcionen. La camara en vivo tiene mas riesgo por permisos, HTTPS, latencia y disponibilidad de hardware.

## Criterio de Exito del Proyecto

La demo debe poder mostrar, en menos de 20 minutos:

- problema de negocio;
- carga o captura de evidencia;
- deteccion de productos;
- conteo por tipo;
- comparacion contra stock esperado;
- discrepancias;
- evidencia visual;
- metricas;
- camino de escalamiento.

