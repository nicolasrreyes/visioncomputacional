# Criterios de Estado

## Proposito

Este documento define como interpretar el resultado de una auditoria visual de inventario.

El sistema debe distinguir entre:

- estado operativo: surge de comparar cantidades detectadas contra cantidades esperadas;
- estado visual: describe la condicion observable del producto en la evidencia.

## Estado Operativo

### OK

Se usa cuando la cantidad detectada coincide con la cantidad esperada.

Ejemplo:

```text
Producto: caja carton chica
Zona: Estanteria A
Esperado: 8
Detectado: 8
Estado operativo: OK
```

### Faltante

Se usa cuando la cantidad detectada es menor que la cantidad esperada.

Ejemplo:

```text
Producto: botella plastica
Zona: Mesa de recepcion
Esperado: 12
Detectado: 9
Estado operativo: faltante
```

### Sobrante

Se usa cuando la cantidad detectada es mayor que la cantidad esperada.

Ejemplo:

```text
Producto: lata metalica
Zona: Zona de despacho
Esperado: 6
Detectado: 8
Estado operativo: sobrante
```

### Revisar

Se usa cuando la evidencia o la confianza del modelo no alcanza para tomar una decision automatica.

Casos tipicos:

- confianza promedio debajo del umbral definido para el producto;
- producto parcialmente oculto;
- imagen borrosa;
- detecciones superpuestas;
- diferencia pequena pero dudosa;
- objeto detectado que no coincide claramente con ningun producto objetivo.

## Estado Visual

### Sano

Producto visible sin dano aparente.

### Danado

Producto con evidencia visible de deterioro.

Ejemplos:

- caja aplastada;
- envase roto;
- etiqueta desprendida;
- paquete deformado;
- producto abierto.

### Parcialmente Visible

Producto detectado, pero no completamente visible.

Ejemplos:

- tapado por otro objeto;
- cortado por el borde de la imagen;
- visible solo en una parte;
- baja iluminacion.

### Desconocido

No se puede determinar el estado visual.

## Reglas Iniciales

La primera version del POC no necesita resolver estado visual con precision perfecta. Priorizar conteo y comparacion contra stock.

Reglas sugeridas:

- si el modelo detecta con confianza igual o superior al umbral del producto, contar la deteccion;
- si la confianza esta por debajo del umbral, marcar como `revisar`;
- si hay varias detecciones muy superpuestas del mismo producto, aplicar supresion o consolidacion para evitar doble conteo;
- si el producto aparece en una zona donde no se esperaba, marcar inicialmente como `sobrante`;
- si la imagen es insuficiente, permitir revision humana.

## Campos Recomendados en Resultados

```json
{
  "producto_id": "caja_carton_chica",
  "zona_id": "estanteria_a",
  "cantidad_esperada": 8,
  "cantidad_detectada": 7,
  "diferencia": -1,
  "estado_operativo": "faltante",
  "estado_visual": "desconocido",
  "confianza_promedio": 0.74,
  "requiere_revision": false,
  "evidencia_path": "outputs/auditoria_001_estanteria_a.jpg"
}
```

