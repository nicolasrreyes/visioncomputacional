# Manual de Uso — Auditoría Visual de Inventario (POC)

Guía práctica para usar la aplicación sin tocar código: instalar, levantar, cargar
fotos, usar la cámara y entender los resultados.

---

## 1. Qué hace la aplicación

Toma una **foto de una estantería o zona de depósito**, la procesa con un modelo de
visión por computadora (YOLO-World) y devuelve:

- cuántas unidades detectó de cada **producto configurado**;
- una **comparación contra el stock esperado** de la zona (sobrante / faltante / ok /
  a revisar);
- **métricas** (total esperado, total detectado, % de coincidencia, discrepancias,
  confianza promedio, tiempo ahorrado);
- una **evidencia visual** = la foto con los productos marcados con recuadros.

También permite operar con **cámara en vivo** (WebRTC) o simular flujos sin cámara.

## 2. Requisitos

| Requisito | Detalle |
| --- | --- |
| Windows / Linux / macOS | desarrollado y probado en Windows |
| Python 3.11+ | recomendado |
| Conexión a internet | solo la primera vez, para descargar el modelo (~340 MB) |
| Navegador moderno | Chrome/Edge recomendado. La cámara en vivo necesita `localhost` o HTTPS |
| Cámara | webcam de la PC **o** el celular (Android vía USB) **o** simplemente fotos |

> El procesamiento es local: las fotos no se suben a ninguna nube.

## 3. Instalación

```powershell
# en la carpeta del proyecto
python -m pip install -r requirements.txt
```

`run_demo.ps1` también instala las dependencias automáticamente (ver sección 4).

## 4. Puesta en marcha (todo en uno)

```powershell
scripts/run_demo.ps1
```

Esto:

1. instala dependencias si faltan;
2. levanta la **API** en `http://127.0.0.1:8000` (accesible también en tu IP de red);
3. levanta el **Dashboard** en `http://127.0.0.1:8501`;
4. abre el navegador en el dashboard.

Si Windows pregunta por el Firewall (al exponer la API en la red), aceptalo **solo si
vas a usar el celular** por red; para uso 100% local podés decir que no.

Para detener todo:

```powershell
Stop-Process -Id <PID_api>,<PID_dashboard> -Force
```

Los PIDs se muestran al final del script.

## 5. Primer contacto con el Dashboard

La barra lateral tiene tres bloques:

1. **Simulación** — genera una auditoría a partir de un fixture (no usa el modelo).
   Útil para ver la app y validar el flujo sin esperas.
2. **Detección real** — el flujo principal: se sube una foto y corre el modelo.
3. **Video en vivo (RTC)** — cámara de la PC o del celular en tiempo real.

El área central muestra:
- **KPIs** de la última auditoría;
- **Detalle de auditoría**: al elegir una auditoría se ve su **evidencia anotada**
  (foto con recuadros), las **discrepancias** y el **JSON completo**. Las auditorías
  simuladas (sin foto) muestran un aviso en vez de imagen;
- botón **Recargar auditorías** (limpieza de caché) en la sidebar.

## 6. Contar stock con una foto propia (paso a paso)

> Solo cuenta los **7 productos configurados** (ver tabla en sección 8). Si tu foto
> tiene otros productos, primero agregalos en la configuración o elegí una foto que
> contenga los productos existentes.

1. Elegí la **zona** correcta en "Detección real". La zona debe coincidir con el stock
   esperado que querés auditar (ver sección 7).
2. **Subí la foto** (JPG/PNG). Buenas prácticas:
   - luz uniforme, sin reflejos;
   - foto de frente, completa del estante;
   - que los productos queden visibles, sin taparse entre sí.
3. Tocá **"Procesar imagen"**. La primera inferencia tarda más (el modelo se carga en
   memoria); después queda caliente.
4. Revisá los KPIs, la **evidencia anotada** y las **discrepancias**.

Alternativa por terminal (sin dashboard):

```powershell
python -m uvicorn app.api.main:app --port 8000
# en otra consola:
curl -X POST http://127.0.0.1:8000/auditorias/imagen `
  -F "zona_id=estanteria_b" `
  -F "fuente=imagen" `
  -F "archivo=@C:\ruta\a\mi_foto.jpg"
```

## 7. Zonas y stock esperado

Las auditorías se hacen **por zona**. Cada zona tiene:

- una lista de **productos permitidos** (solo esos se detectan en esa zona);
- un **stock esperado** contra el que se compara el conteo.

| Zona | Productos permitidos | Stock esperado |
| --- | --- | --- |
| `estanteria_a` | caja chica, caja grande, botella, lata | caja chica 8 · botella 12 · lata 6 |
| `estanteria_b` | caja grande, paquete flexible, bidón, botella | botella 40 |
| `mesa_recepcion` | caja chica, caja grande, botella | caja chica 4 · botella 10 |
| `zona_despacho` | caja chica, caja grande, paquete flexible, pallet | caja grande 7 · paquete flexible 20 |
| `palletera` | pallet con cajas | pallet 2 |

Configurables en `data/zonas.json` y `data/stock_esperado.csv`.

## 8. Productos y umbrales de confianza

| id | Nombre | Umbral de confianza |
| --- | --- | --- |
| `caja_carton_chica` | Caja de Cartón Pequeña | 0.60 |
| `caja_carton_grande` | Caja de Cartón Grande | 0.28 |
| `botella_plastica` | Botella Plástica | 0.30 |
| `lata_metalica` | Lata Metálica | 0.38 |
| `paquete_flexible` | Paquete Flexible | 0.40 |
| `bidon_plastico` | Bidón Plástico | 0.40 |
| `pallet_con_cajas` | Pallet con Cajas | 0.30 |

Una detección con confianza **menor** a su umbral no se cuenta como stock: pasa a la
lista **"a revisar"** y el producto figura con estado `REVISAR`.

## 9. Entender los resultados

### Estados por producto

| Estado | Significado |
| --- | --- |
| `OK` | lo detectado == lo esperado |
| `FALTANTE` | se detectó menos de lo esperado |
| `SOBRANTE` | se detectó más de lo esperado |
| `REVISAR` | hay detecciones de baja confianza para ese producto (prioridad: revisar) |

### Métricas

| Métrica | Qué es |
| --- | --- |
| Total esperado | suma del stock esperado de la zona |
| Total detectado | suma de unidades detectadas válidas |
| Diferencia | detectado − esperado (negativo = faltante) |
| Discrepancias | productos cuyo estado no es OK |
| Coincidencia % | qué tanto coincide el total detectado con el esperado |
| Confianza promedio | confianza media de las detecciones válidas |
| A revisar | cantidad de **productos** con detecciones de baja confianza |
| Tiempo ahorrado | tiempo manual estimado (0.25 min/unidad) − tiempo de la IA (nunca negativo) |

### Evidencia y archivos

- **Evidencia anotada**: la foto con recuadros de colores por producto, en
  `outputs/evidencia/auditoria_NNN_anotada.jpg`.
- **Original**: copia de la foto subida en `inputs/auditoria_NNN_original.jpg`.
- **Auditorias**: un JSON por auditoría en `outputs/auditorias/auditoria_NNN.json`.

## 10. Cámara en vivo

### Webcam de la PC

1. En la sidebar: **Video en vivo** → elegir zona → activar **"Mostrar vista de
   camara"**.
2. En el iframe: **"Iniciar camara"** → aceptar el permiso del navegador.
3. Verás el video con recuadros en vivo (**1 frame por segundo**) y la tabla de
   conteos.
4. **"Detener y guardar"**: el backend confirma el guardado y la auditoría queda en el
   dashboard con fuente `camara_viva`.

> Una sola conexión a la vez; cerrá la vista antes de volver a iniciar.

### Celular como cámara

`getUserMedia` solo funciona en contexto seguro (`https` o `localhost`).

- **Android + USB (recomendado, sin servicios)**: activá "Depuración USB", conectá el
  celu y en la PC:
  ```powershell
  adb reverse tcp:8000 tcp:8000
  ```
  En el celular abrí `http://localhost:8000/rtc?zona_id=estanteria_b`.
  El modelo corre en la PC; el celular solo envía video.
- **Túnel HTTPS**: `ngrok http 8000` y abrir la URL `https://...` en el celular.
- **Respaldo**: sacá la foto con el celular, pasala a la PC y subila en "Detección
  real" (sección 6).

Detalle completo en `docs/DEMO.md`.

## 11. Volver a empezar (limpiar datos generados)

```powershell
scripts/limpiar_demo.ps1
```

Borra las auditorías, evidencias e inputs generados. **No** toca el código ni las
imágenes demo de `data/demo_images/`.

## 12. Imágenes y guion de demo

Imágenes de ejemplo en `data/demo_images/` (libres, atribuidas en
`data/demo_images/README.md`):

- `estante_gaseosas.jpg` → `estanteria_b` (botellas)
- `caja_carton.jpg` → `palletera` (pallets)
- `botellas_en_estante.jpg` → `estanteria_a` (varias discrepancias)
- `estante_supermercado.jpg` → sin detecciones útiles (solo pruebas)

Guion paso a paso de presentación: `docs/DEMO.md`.

## 13. Problemas frecuentes

| Síntoma | Causa / solución |
| --- | --- |
| La cámara no se enciende en el celular | No es un contexto seguro. Usá `adb reverse` (localhost) o un túnel HTTPS. |
| Primer procesamiento tarda mucho | El modelo se está cargando (~340 MB) o descargando. Planificá una "pre-carga" antes de la demo: procesá una foto una vez. |
| No detecta productos | La foto no contiene los 7 productos configurados, o la imagen está muy lejos/deseenfocada. Probá con otra zona o ajustá umbrales/prompts (manual técnico, sección 11); calibrá con `scripts/evaluar.py` (sweep de umbral). |
| "Archivo demasiado grande" (413) | Límite de subida: 10 MB. Reducí la foto. |
| "Zona desconocida" (400) | Verificá el id de zona en `data/zonas.json` (`GET /zonas`). |
| Firewall bloquea el celular | Aceptá el permiso de Windows Firewall al levantar la API (`run_demo.ps1` expone `0.0.0.0`). |
| La conexión RTC se corta | Probá cerrar y volver a iniciar; un solo cliente a la vez. |
| Resultados cambian con la luz | Es esperable; los conteos por foto pueden variar. Usá condiciones de luz parecidas. |