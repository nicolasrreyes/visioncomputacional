# Auditoria Visual de Inventario

POC para la IACKATON CDA, iniciativa 1: computer vision para inventarios de productos.

El sistema soporta dos flujos de deteccion:

```text
Flujo simulado (mock):   fixture de detecciones -> conteo -> comparacion -> metricas -> auditoria
Flujo real (imagen):     imagen (foto real) -> YOLO-World -> conteo -> comparacion -> metricas -> auditoria + evidencia visual
```

La deteccion real usa [YOLO-World](https://github.com/AILab-CVC/YOLO-World) (`yolov8s-worldv2.pt`)
con prompts por producto, auto-detectando CUDA/CPU en runtime. El modelo pesa ~340MB y se
descarga automaticamente al primer uso (se cachea en la raiz, ignorado por git).

Ademas soporta **video en vivo por WebRTC** (`aiortc`): el navegador envia la camara al
backend, que detecta 1 frame por segundo (throttling) y devuelve por DataChannel un JSON
con las detecciones para superponerlas en un `<canvas>`. Al detener, se guarda una
auditoria con `fuente=camara_viva` y evidencia anotada.

`mock_inference.py` se mantiene como fallback para tests y demo controlada.

## Estructura

```text
app/
  api/
  audits/
  detection/       # mock_inference.py + real_inference.py (YOLO-World)
  inventory/
  rtc/             # procesador.py (throttling/payload) + webrtc.py (aiortc)
  visualization/   # draw.py (bounding boxes sobre la imagen)
dashboard/
data/
docs/
scripts/
tests/
```

## Instalacion

```bash
python -m pip install -r requirements.txt
```

## Ejecutar Tests

```bash
python -m pytest -q
```

## Levantar API

```bash
python -m uvicorn app.api.main:app --reload
```

Endpoints principales:

- `GET /health`
- `GET /zonas`
- `GET /productos`
- `GET /stock/{zona_id}`
- `POST /auditorias/simular`
- `POST /auditorias/imagen` (deteccion real con carga de imagen)
- `GET /rtc` (pagina del reproductor de video en vivo)
- `POST /rtc/offer` (signaling WebRTC: recibe SDP offer, devuelve SDP answer)
- `GET /auditorias`
- `GET /auditorias/{auditoria_id}`

Ejemplo de simulacion:

```bash
curl -X POST http://127.0.0.1:8000/auditorias/simular ^
  -H "Content-Type: application/json" ^
  -d "{\"zona_id\":\"estanteria_a\",\"fixture\":\"detecciones_estanteria_a.json\",\"fuente\":\"imagen\"}"
```

Ejemplo de deteccion real (carga multipart):

```bash
curl -X POST http://127.0.0.1:8000/auditorias/imagen ^
  -F "zona_id=estanteria_a" ^
  -F "fuente=imagen" ^
  -F "archivo=@data/demo_images/botellas_en_estante.jpg"
```

La carga valida tempranamente que la zona exista (400) y limita el archivo a 10 MB (413).

## Levantar Dashboard

```bash
python -m streamlit run dashboard/streamlit_app.py
```

O con un solo comando (levanta API + dashboard y abre el navegador):

```powershell
scripts/run_demo.ps1
```

Para volver a empezar de cero (borra auditorias/evidencias/inputs generados):

```powershell
scripts/limpiar_demo.ps1
```

Guion de la demo paso a paso: [docs/DEMO.md](docs/DEMO.md).

## Documentacion

- [Manual de uso](docs/MANUAL_DE_USO.md): guia practica de instalacion, uso del
  dashboard, conteo con fotos propias, camara (PC/celular) y resolucion de problemas.
- [Manual tecnico](docs/MANUAL_TECNICO.md): arquitectura, modulos, API, NMS/metricas,
  WebRTC, tests y guia de extension/afinado.
- [Guion de demo](docs/DEMO.md): paso a paso de presentacion con numeros esperados.

El dashboard permite:

- seleccionar zona;
- seleccionar fixture;
- simular auditoria;
- **subir una imagen y procesarla con deteccion real** (sidebar);
- **abrir la vista de camara en vivo (WebRTC)** (toggle persistente) y detener para
  guardar la auditoria;
- ver KPIs de la ultima auditoria;
- **elegir cualquier auditoria guardada** y ver su evidencia anotada, discrepancias y
  JSON completo; el toggle de camara y la seleccion se mantienen entre recargas;
- listar auditorias guardadas;
- recargar manualmente (limpia la cache) desde la sidebar.

## Video en vivo (WebRTC)

Para la demo en vivo:

1. Levantar la API: `python -m uvicorn app.api.main:app --reload`.
2. En el dashboard, activar "Mostrar vista de camara" en la sidebar (o abrir
   directamente `http://127.0.0.1:8000/rtc?zona_id=estanteria_a`).
3. El navegador pide permiso de camara (`getUserMedia` requiere contexto seguro:
   `localhost` sirve; para otro host usar HTTPS/ngrok).
4. El backend procesa ~1 frame por segundo (throttling configurable en
   `app/rtc/procesador.py`, `DEFAULT_INTERVALO_SEG`) y manda el JSON por DataChannel.
5. "Detener y guardar" cierra la conexion y persiste una auditoria
   (`fuente: camara_viva`) con el ultimo frame como original y la version anotada
   como evidencia.

Si la camara no se enciende o la conexion RTC falla, el flujo de carga manual de
imagen queda disponible como respaldo (no es opcional: es el seguro de la demo).

Para usar el **celular como camara**: `scripts/run_demo.ps1` ya levanta la API en
`0.0.0.0`. Android + USB con `adb reverse tcp:8000 tcp:8000` (y abrir
`http://localhost:8000/rtc` en el celular) o un tunele HTTPS (ngrok). `getUserMedia`
solo funciona en `https`/`localhost`; detalle y guion en [docs/DEMO.md](docs/DEMO.md).

## Auditorias

Las auditorias se guardan en:

```text
outputs/auditorias/
```

Cada auditoria incluye:

- detecciones;
- conteos;
- discrepancias;
- metricas;
- zona;
- fecha/hora;
- fuente.

En el flujo real, ademas:

- `archivo_original`: copia de la imagen cargada en `inputs/`;
- `evidencia_path`: imagen anotada con bounding boxes en `outputs/evidencia/`.

## Imagenes de Demostracion

Mientras no haya fotos propias del deposito, se usan imagenes libres descargadas de
Wikimedia Commons (ver atribucion en `data/demo_images/README.md`):

```bash
python scripts/descargar_imagenes_demo.py
```

Los prompts por producto, umbrales de confianza y la regla `solapamiento_maximo`
(NMS por IoU para deduplicar cajas) se ajustan en `data/productos_objetivo.json`.
Para afinar de forma objetiva existe un validador que corre el modelo real sobre
las imagenes demo y tabula detecciones crudas, validas por umbral y tras NMS,
comparando contra el stock por zona:

```bash
python scripts/validar_deteccion.py --imagen data/demo_images/estante_gaseosas.jpg --zona estanteria_b
```

Narrativa demo (emparejamiento imagen -> zona):

- `estante_gaseosas.jpg` -> `estanteria_b`: ~41 botellas detectadas de 40 esperadas
  (sobrante + detecciones de baja confianza a revisar).
- `caja_carton.jpg` -> `palletera`: 1 pallet detectado de 2 esperados (faltante).
- `botellas_en_estante.jpg` -> `estanteria_a`: caja/botellas detectadas vs stock
  (varias faltantes) - ideal para mostrar multiples discrepancias.
- `estante_supermercado.jpg` => sin detecciones utiles para el vocabulario actual;
  se conserva para pruebas y atribucion, no se usa en la demo principal.

