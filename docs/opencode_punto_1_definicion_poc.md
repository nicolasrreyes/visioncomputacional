# OpenCode - Punto 1: Definicion del POC

## Contexto

Proyecto para la IACKATON CDA, iniciativa 1: **Computer vision para inventarios de productos**.

El objetivo del POC es construir una solucion de auditoria visual de inventario que permita:

- cargar o capturar evidencia visual de una zona de deposito;
- detectar productos mediante vision computacional;
- contar productos por tipo;
- comparar el conteo detectado contra un stock esperado;
- generar evidencia visual y una tabla de discrepancias.

Este primer punto no busca implementar todavia el modelo ni la interfaz completa. Busca dejar definido el alcance funcional, los datos base y las reglas del POC para que el desarrollo posterior sea concreto.

## Objetivo del Punto 1

Definir el dominio inicial del POC:

- rubro de inventario;
- productos objetivo;
- zonas fisicas;
- estados posibles;
- archivo de stock esperado;
- criterios de aceptacion para validar que la fase esta lista.

## Alcance elegido

Para la primera version se trabajara con un inventario simulado de deposito de insumos/productos empaquetados.

El POC debe evitar el objetivo demasiado amplio de detectar "cualquier producto". En su lugar, se debe trabajar con un conjunto chico y controlado de clases visuales.

## Productos objetivo iniciales

Trabajar con estas clases:

- caja carton chica;
- caja carton grande;
- botella plastica;
- lata metalica;
- paquete flexible;
- bidon plastico;
- pallet con cajas.

Estas clases fueron elegidas porque son visualmente distinguibles, faciles de conseguir para generar evidencia de demo y razonables para un escenario de deposito.

## Zonas iniciales

Trabajar con estas zonas:

- Estanteria A;
- Estanteria B;
- Mesa de recepcion;
- Zona de despacho;
- Palletera.

Cada auditoria visual debe estar asociada a una zona. La comparacion contra stock esperado se hace por producto y zona.

## Estados iniciales

Para evitar sobredimensionar el problema, separar el concepto de estado en dos grupos:

### Estado operativo

Este estado se calcula comparando deteccion contra stock esperado:

- OK;
- faltante;
- sobrante;
- revisar.

### Estado visual

Este estado describe la condicion observable del producto:

- sano;
- danado;
- parcialmente visible;
- desconocido.

En la primera version, el estado visual puede cargarse manualmente o inferirse con reglas simples. No es obligatorio que el modelo clasifique dano con alta precision desde el inicio.

## Datos base esperados

Crear archivos iniciales de configuracion o ejemplos equivalentes:

- `data/stock_esperado.csv`
- `data/productos_objetivo.json`
- `data/zonas.json`
- `docs/criterios_estado.md`

Si el proyecto todavia no tiene carpeta `data`, crearla.

## Reglas de comparacion

Para cada combinacion de zona y producto:

```text
diferencia = cantidad_detectada - cantidad_esperada
```

Reglas:

- si `diferencia == 0`, estado operativo `OK`;
- si `diferencia < 0`, estado operativo `faltante`;
- si `diferencia > 0`, estado operativo `sobrante`;
- si la confianza promedio de deteccion es baja, estado operativo `revisar`;
- si el producto no esta en el stock esperado de la zona pero aparece detectado, marcar como `sobrante` o `ubicacion incorrecta` en fases posteriores.

Para la primera version, `ubicacion incorrecta` puede quedar documentado como mejora futura.

## Escenarios de demo que deben quedar preparados

Preparar el sistema pensando en estos escenarios:

1. Inventario correcto: lo detectado coincide con lo esperado.
2. Faltante: el sistema esperado dice que hay mas unidades que las detectadas.
3. Sobrante: el sistema detecta unidades extra.
4. Baja confianza: deteccion dudosa que requiere revision humana.
5. Evidencia visual: imagen con bounding boxes asociada al resultado.

## Criterios de aceptacion del Punto 1

El punto 1 se considera terminado cuando:

- existen los archivos de datos base;
- los productos objetivo estan definidos con nombres, prompts y umbrales iniciales;
- las zonas estan definidas con identificador, nombre y descripcion;
- el stock esperado tiene al menos 10 filas realistas;
- los estados y reglas de comparacion estan documentados;
- queda claro que el siguiente paso es implementar el flujo: imagen -> detecciones -> conteo -> comparacion.

## Entregables para OpenCode

OpenCode debe crear o completar:

- `data/stock_esperado.csv`
- `data/productos_objetivo.json`
- `data/zonas.json`
- `docs/criterios_estado.md`

Tambien puede usar este documento como referencia principal para el alcance del POC.

