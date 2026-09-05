# Demo del POC

Guion paso a paso de la demo en localhost para la IACKATON CDA (iniciativa 1: computer
vision para inventarios).

## Requisitos

- Python 3.11 + dependencias (`scripts/run_demo.ps1` instala todo solo).
- Modelo `yolov8s-worldv2.pt` (~340 MB), se descarga al primer uso.
- CPU es suficiente (~1 fps de inferencia → el video de la camara procesa 1 frame/segundo).
- Navegador Chrome/Edge. `getUserMedia` exige contexto seguro: `localhost` califica.

## Levantar la demo

```powershell
scripts/run_demo.ps1
```

Levanta API (`http://127.0.0.1:8000`) + Dashboard (`http://127.0.0.1:8501`) y abre el
navegador.

**Antes de presentar:** cargar una imagen una vez (por ejemplo `botellas_en_estante.jpg`
con zona `estanteria_a`) para que el modelo quede caliente. Incluso con modelo caliente,
una inferencia toma varios segundos: es normal, avisarlo en la demo.

## Guion sugerido (~10 min)

### 1. Carga manual de imagen (el "core" de la demo)

| Imagen | Zona | Resultado esperado |
| --- | --- | --- |
| `data/demo_images/estante_gaseosas.jpg` | `estanteria_b` | ~41 botellas detectadas de 40 esperadas → **sobrante + baja confianza a revisar** (estado REVISAR). |
| `data/demo_images/caja_carton.jpg` | `palletera` | 1 pallet de 2 esperados → **faltante**. |
| `data/demo_images/botellas_en_estante.jpg` | `estanteria_a` | Caja + botellas vs stock (varios faltantes + a revisar) → **múltiples discrepancias**. |

Para cada una:

1. Sidebar **Detección real** → elegir zona → subir la imagen → "Procesar imagen".
2. Mostrar: KPI (total esperado/detectado, discrepancias, % coincidencia), la
   **evidencia anotada** con bounding boxes coloridos por producto, y las discrepancias
   del detalle de auditoría.

### 2. Cámara en vivo (WebRTC) - si el entorno lo permite

1. Sidebar → **Video en vivo** → elegir zona (`estanteria_b` da buen resultado con
   botellas que se tengan a mano) → activar "Mostrar vista de camara".
2. En el iframe: "Iniciar camara", aceptar el permiso. El video se superpone con
   bounding boxes en tiempo real (1 frame/segundo) y la tabla de conteos por producto.
3. "Detener y guardar": el backend **confirma el guardado** y la auditoría queda en el
   dashboard con `fuente: camara_viva`, el último frame como original y la versión
   anotada como evidencia.
4. Volver al dashboard y mostrarla seleccionándola en "Detalle de auditoría".

> Nota: una sola conexión RTC a la vez; cerrala antes de volver a iniciar.

## Cámara del celular (sin webcam en la PC)

El front RTC pide `getUserMedia`, que solo funciona en contexto seguro (`https` o
`localhost`). Abrir `http://192.168.x.x:8000/rtc` desde el celular **no** enciende la
cámara. Dos rutas funcionan:

### Opcion A: Android + `adb reverse` (recomendada, sin servicios externos)

1. En el celular activa **Depuracion USB** (Ajustes → Opciones de desarrollo) y conectalo
   por USB.
2. En la PC: `adb reverse tcp:8000 tcp:8000` (instala Platform Tools si no tenes `adb`).
3. En el celular abrí `http://localhost:8000/rtc?zona_id=estanteria_b`.
   Para el navegador eso es `localhost` = contexto seguro → la cámara se enciende. Los
   frames viajan por USB a la PC, que corre el modelo (~1 fps) y devuelve los bboxes.
4. Similar para el dashboard si lo querés del celu:
   `adb reverse tcp:8501 tcp:8501` y abrí `http://localhost:8501`.

> `run_demo.ps1` ya levanta la API en `0.0.0.0`, así que el reverse funciona. Si Windows
> pide permiso de Firewall, aceptalo.

### Opcion B: Túnel HTTPS (sin USB)

```bash
ngrok http 8000
```

Abri en el celular la URL `https://...ngrok.../rtc?zona_id=estanteria_b`. La cámara
sí se enciende (https), pero depende de internet y del túnel; útil como plan B.

### Plan C (respaldo garantido): foto del celular → carga manual

1. Sacale una foto a la estanteria con el celular.
2. Pasala a la PC (WhatsApp Web / cable / cualquier vía).
3. Dashboard → **Detección real** → zona + "Procesar imagen".
   Este flujo está validado y no depende de WebRTC.

> El guion de la sección anterior sirve para cualquiera de estos planes; la "cámara en
> vivo" es solo la opción con más impacto visual.

### 3. Cierre

- Mostrar la lista "Auditorías guardadas" y el JSON completo de una auditoría
  (detección, conteo NMS, discrepancias, métricas).
- Mencionar que el cómputo es local (sin nube), configurable vía
  `data/productos_objetivo.json` (umbrales, prompts) y que las imágenes demo están
  atribuidas en `data/demo_images/README.md`.

## Fallbacks / contingencias

- **Si la cámara no se enciende** (permisos, drivers): ir directo al flujo de carga
  manual de imagen y decirlo como "flujo de ingesta alternativo".
- **Si falla una inferencia** (out of memory, modelo ausente): bajar el tamaño de la
  imagen o reintentar; el validador `scripts/validar_deteccion.py` permite tabular
  detecciones sin pasar por el dashboard.
- **Numeros que no calzan**: los conteos pueden variar según iluminación/ángulo;
  los umbrales y prompts se retocan en `data/productos_objetivo.json` y se validan con
  `scripts/validar_deteccion.py --imagen X.jpg --zona Z`.

## Volver a empezar

```powershell
scripts/limpiar_demo.ps1
```

Borra las auditorías, evidencias e inputs generados (no toca código ni
`data/demo_images/`).