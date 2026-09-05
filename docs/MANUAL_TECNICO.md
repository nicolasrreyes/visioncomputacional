# Manual Técnico — Auditoría Visual de Inventario (POC)

Documento de referencia técnica: arquitectura, módulos, flujos, API, datos,
decisiones de diseño y guía de extensión/afinado.

---

## 1. Stack

| Componente | Tecnología |
| --- | --- |
| Lenguaje | Python 3.11 |
| API | FastAPI + Uvicorn |
| Validación de datos | Pydantic v2 |
| Detección | Ultralytics YOLO-World (`yolov8s-worldv2.pt`, zero-shot, ~340 MB) |
| Video en vivo | aiortc (WebRTC, backend) + JS nativo (front) |
| Configuración | `app/config.py` (env vars `VISINVENT_*`) |
| Observabilidad | `logging` + `GET /health` con estado real |
| Dashboard | Streamlit |
| Imágenes | Pillow + numpy |
| Tests | pytest |

El modelo es **zero-shot**: no requiere entrenamiento; se le pasa una lista de
"prompts" de texto por producto y setea las clases en runtime (`set_classes`).

## 2. Arquitectura y flujos

```text
                 ┌────────────────────────────────────────────────┐
                 │                    Backend (FastAPI)          │
  Foto/stream ──►│                                                │
                 │  app/rtc (vivo) ─► ProcesadorVideo ─► RealDetector
  ┌───────────┐  │  app/api  ─► app/audits/service.py            │
  │ Dashboard │  │                   │                          │
  │ Streamlit ├──► app/audits  ◄─────┤ conteo → comparación →    │
  └───────────┘  │                    métricas → Auditoria JSON  │
                 │                    ↓                          │
                 │  outputs/auditorias · inputs/ · outputs/evidencia
                 └────────────────────────────────────────────────┘
```

### Pipeline de una auditoría (armado central)

`app/audits/service.py::_armar_y_guardar` ejecuta, para **cualquier** fuente:

1. `contar_detecciones(detecciones, productos)` — **NMS** por IoU + umbral por producto.
2. `stock_por_zona(zona_id)` — lee `data/stock_esperado.csv`.
3. `comparar_con_stock(...)` — construye las discrepancias por producto.
4. `calcular_metricas(...)` — KPIs.
5. `Auditoria.nueva(...)` + `repository.guardar(...)` — persiste JSON.

### Tres fuentes de detecciones

| Fuente | Función | Origen del bbox |
| --- | --- | --- |
| Simulado | `simular_auditoria` | fixture JSON (`tests/fixtures/detecciones_*.json`) |
| Imagen | `procesar_imagen` | imagen en disco → `RealDetector.detectar` |
| Cámara viva | `guardar_auditoria_viva` | último frame → `RealDetector.detectar_ndarray` |

## 3. Estructura de directorios

```text
app/
  api/            # FastAPI routes: routes_detection.py, routes_rtc.py, main.py
  audits/         # service.py (orquestacion) · repository.py (persistencia)
                  # metrics.py (KPIs)
  detection/      # counting.py (NMS+umbrales) · real_inference.py (YOLO-World)
                  # mock_inference.py (fixtures)
  inventory/      # schemas.py (pydantic) · loader.py (JSON/CSV) · compare.py
  rtc/            # procesador.py (throttling/payload) · webrtc.py (aiortc)
  visualization/  # draw.py (bounding boxes sobre imagen/array)
dashboard/        # streamlit_app.py · rtc_player.html (front RTC)
data/             # zonas.json · productos_objetivo.json · stock_esperado.csv
                  # AUDITORIA_SCHEMA.json · demo_images/
docs/ scripts/ tests/ inputs/ outputs/
```

## 4. Configuración/data (datos de entrada)

### `data/productos_objetivo.json`
```json
{
  "productos_objetivo": [{
    "id": "botella_plastica",
    "nombre": "Botella Plástica",
    "prompts_deteccion": ["plastic bottle", "transparent plastic container", "botella plástica transparente"],
    "umbral_confianza": 0.3,
    "color_bbox": "#4ECDC4",
    "peso_aproximado_kg": 0.2,
    "altura_tipica_cm": 25
  }],
  "reglas_conteo": {
    "solapamiento_maximo": 0.7,     // NMS IoU
    "frames_para_consolidar": 5,
    "minimo_detecciones_confirmadas": 2
  }
}
```
- **Prompts** = lenguaje natural (priorizar inglés + variantes en español). Cuanto más
  discriminativos, mejor separan clases.
- **Color** = hex usado para la evidencia anotada y el overlay del video.

### `data/zonas.json`
Zonas físicas con `productos_permitidos` (solo esos se detectan en esa zona) y
`flujo_logistico` (entrada → almacenamiento → despacho).

### `data/stock_esperado.csv`
`zona_id, producto_id, cantidad_esperada, ubicacion_exacta, fecha_ultimo_recuento, notas`.

### `data/AUDITORIA_SCHEMA.json`
Documenta el contrato del JSON de auditoría (referencia para el equipo de datos).

## 5. Detección (`app/detection/real_inference.py`)

- `RealDetector` carga el modelo de forma **lazy** (`_cargar_modelo`), auto-detecta
  device (`cpu`/`cuda`) y deja prompts cacheados en `_prompts_actuales`.
- `_construir_mapeo(prompts_por_producto)` aplana los prompts en índices; el clasificador
  de YOLO-World devuelve índices que se remapean a `producto_id` + prompt original.
- `_a_pixeles` normaliza a coordenadas originales si el modelo devuelve bboxes
  relativos (0–1).
- **Singleton + locks**: `obtener_detector_compartido()` devuelve **una única instancia**
  (YOLO no es thread-safe) y `_DETECCION_LOCK` (RLock) serializa `set_classes`+`predict`
  en disco y en ndarray. Todas las conexiones RTC comparten el mismo modelo (~340 MB).

## 6. Conteo y NMS (`app/detection/counting.py`)

`supresion_no_maxima` (greedy):

1. Ordena por confianza descendente.
2. Conserva una caja si su IoU máximo contra las ya conservadas **≤**
   `solapamiento_maximo` (default **0.7**).

Razón del valor 0.7 (decisión empírica): valores bajos (ej. 0.15) colapsan estantes
densos en cadena; 0.7 deduplica sin fundir productos contiguos. En estantes densos el
colapso observado era por umbrales de confianza altos, no por NMS.

`contar_detecciones`: NMS → para cada detección usa el umbral **por producto** (o el
default 0.65 si no existe): `confianza >= umbral` → cuenta como válida; si no, pasa a
`detecciones_a_revisar` (baja confianza).

## 7. Comparación (`app/inventory/compare.py`)

Por producto (unión de stock esperado ∪ detecciones ∪ a_revisar):
`diferencia = detectado − esperado` y estado:

- `REVISAR` si hay detecciones de baja confianza (prioriza sobre la diferencia);
- `OK / FALTANTE / SOBRANTE` según el signo de la diferencia.

## 8. Métricas (`app/audits/metrics.py`)

| Métrica | Fórmula |
| --- | --- |
| `total_esperado` | `Σ cantidad_esperada` |
| `total_detectado` | `Σ cantidad_detectada` |
| `diferencia_total` | `total_detectado − total_esperado` |
| `cantidad_discrepancias` | productos con estado ≠ OK |
| `porcentaje_coincidencia` | `max(0, 100 − |diferencia_total|/total_esperado·100)` |
| `confianza_promedio` | media de confianza de válidas (0 si sin válidas) |
| `items_a_revisar` | **productos únicos** con detecciones de baja confianza |
| `tiempo_ahorrado_minutos` | `max(0, total_esperado·0.25 − duración_seg/60)` (clamp ≥ 0) |

Especificación de negocio completa en `docs/METRICAS_DEFINIDAS.md`.

## 9. Persistencia (`app/audits/repository.py`)

- Un JSON por auditoría: `outputs/auditorias/auditoria_NNN.json` (`NNN` = secuencial 3
  dígitos, precio del max+1 con lock global `_ID_LOCK`).
- `siguiente_id()` es **atómico** (lock). `guardar()` detecta colisiones (ej. seeds
  trackeadas en git) y re-asigna id con `model_copy`.
- `_path` sanitiza el id (`Path(id).stem`) para evitar path-traversal.

## 10. API (FastAPI)

### Endpoints públicos
| Método y ruta | Función | Errores |
| --- | --- | --- |
| `GET /health` | healthcheck | — |
| `GET /zonas` · `GET /productos` | catálogos | — |
| `GET /stock/{zona_id}` | stock de una zona | 404 zona |
| `POST /auditorias/simular` | auditoría desde fixture | 404 fixture · 400 zona |
| `POST /auditorias/imagen` | **foto + modelo real** | 400 imagen/zona · 413 > 10 MB · 404 · 503 modelo |
| `GET /auditorias` · `GET /auditorias/{id}` | listar / detalle | 404 |
| `GET /rtc` | página del reproductor (HTML) | — |
| `POST /rtc/offer` | signaling: SDP offer → answer | 400 · 503 sin aiortc · 422 SDP > 200 KB |

### Detalle endurecido de `/auditorias/imagen`
- Valida la **zona antes** de leer el archivo → `400` temprano.
- Solo `image/*` → `400`.
- Tope de **10 MB** leído por chunks (512 KB) → `413` (evita doom en memoria).
- Form-param: `zona_id` (obligatorio), `fuente` (enum `imagen|video|camara_viva`,
  default `imagen`), `archivo`.

### Windows/head
- `GET /rtc` responde con
  `Permissions-Policy: camera=(self), microphone=()` (aisla permisos de la página).
- `RtcOfferRequest.sdp` con `Field(max_length=200_000)` → `422`.
- **CORS**: `CORSMiddleware` con `allow_origins=settings.cors_origins` (default `*`
  para POC; el dashboard "oficina" puede abrirse desde otra máquina de la LAN).
- **Response models**: todas las rutas declaran `response_model=` (tipos Pydantic),
  por lo que `/docs` (Swagger) expone los contratos de entrada y salida.

## 11. Observabilidad y configuracion

### Configuracion centralizada (`app/config.py`)
Constantes de runtime en un `Settings` (dataclass) que se leen de env vars:

| Variable | Default | Uso |
| --- | --- | --- |
| `VISINVENT_MAX_UPLOAD_MB` | `10` | tope del archivo subido |
| `VISINVENT_RTC_INTERVALO_SEG` | `1.0` | throttling del video en vivo |
| `VISINVENT_RTC_MAX_DIMENSION` | `640` | tamaño maximo de frame para inferencia |
| `VISINVENT_API_HOST` / `VISINVENT_API_PORT` | `127.0.0.1` / `8000` | binding de la API |
| `VISINVENT_LOG_LEVEL` | `INFO` | nivel de logging |

### Logging
`app/logging_config.py::configurar_logging()` se llama al iniciar `app.api.main`.
Ningún `except` queda silencioso: los caminos del RTC que antes hacían `pass`
ahora loguean (`logger.exception` / `logger.warning`). Utili en la demo: un fallo
de inferencia queda visible en la consola de uvicorn.

### Health check real
`GET /health` ya **no** devuelve un 200 fijo: reporta `modelo_cargado`,
`zonas`, `auditorias_guardadas` y `disco_libre_bytes`. Permite distinguir "el
proceso esta arriba" de "el sistema esta operativo".

## 12. Video en vivo (WebRTC, `app/rtc/`)

### Signaling
1. El front `GET /rtc` carga `rtc_player.html` (same-origin → contexto seguro para
   `getUserMedia`).
2. `RTCPeerConnection` local → `createOffer` → `POST /rtc/offer` → el backend crea su
   `RTCPeerConnection` + `ProcesadorVideo`, responde el SDP answer.
3. DataChannel `detecciones` para el streaming.

### ProcesadorVideo (`procesador.py`)
- **Throttling** por `intervalo_seg` (default 1 s): 1 detección por segundo.
- **Resize** a `max_dimension=640` (misma escala si es más chica): los bboxes del
  detector se devuelven a **coordenadas originales** (factor = redimensionado).
- `build_payload` entrega:
  ```json
  {"timestamp","ancho","alto","detecciones":[{"producto_id","label",
   "confianza","bbox":[x1,y1,x2,y2],"nombre","color_bbox","umbral_confianza"}]}
  ```
  (`nombre`, `color_bbox`, `umbral_confianza` se enriquecen desde `productos_objetivo.json`.)
- Detección en **ThreadPoolExecutor(max_workers=1)** para no bloquear el event loop.

### Guardado de la cámara viva
- Mensaje `"detener"` (DataChannel) o cierre de conexión → `guardar_snapshot()`.
- `combinar_cuadros` guarda **exactamente una vez** (`snapshot_guardado` flag): si no
  hubo frame o detecciones, no persiste pero igual se marca (semántica exactly-once).
- ACK `{"tipo":"guardado"}` al front, que cierra el stream tras la confirmación
  (timeout 4 s de respaldo en el JS).
- La auditoría queda con `fuente=camara_viva`, último frame en `inputs/` y evidencia
  anotada en `outputs/evidencia/`.
- `ConexionRtc.cerrar()` cancela la tarea consumidora y apaga el executor
  (`wait=False, cancel_futures=True`); cleanup de `CONEXIONES` en failed/closed y en
  fallo del offer.

## 13. Dashboard (Streamlit)

- Datos cacheados con `@st.cache_data` (TTL 10 s para auditorías) + botón
  "Recargar auditorías" (`st.cache_data.clear()`).
- Toggle de cámara y selección de auditoría **persistidos** en `st.session_state`.
- `st.spinner` alrededor de las inferencias (avisar que tarda).
- Área principal: KPIs de la última + **Detalle de auditoría** (evidencia anotada,
  discrepancias, JSON completo).

## 14. Tests

```powershell
python -m pytest -q          # suite completa (78 tests verdes)
python -m pytest -q tests/unit/test_counting_nms.py   # uno solo
```

Estructura:
- `tests/unit/` — lógica pura: NMS/IoU, conteo, comparación, métricas, loader,
  repository, detector (con modelo *stub*), payload RTC, snapshot, draw.
- `tests/integration/` — API con TestClient (errores 400/404/413/422/503, flujo de
  imagen con detector stub, audit_flow, RTC).

Patrón de stubs: se inyecta un `RealDetector` con `_model` falso (`FakeModel` +
`FakeResult`/`FakeBoxes`) para no descargar el modelo real.

## 15. Afinado del modelo (sin tocar código)

```powershell
python scripts/validar_deteccion.py --imagen data/demo_images/estante_gaseosas.jpg --zona estanteria_b
```

Reporta por producto: detecciones crudas, válidas por umbral y **tras NMS a varios
umbrales** (`--nms 0.5 0.6 0.7 0.8`), confianzas ordenadas y comparación contra stock.
Opciones: `--imagen`, `--zona`, `--conf`, `--max-confs`, `--nms`.

Regla práctica: elegir `umbral_confianza` tal que las válidas igualen el stock real y
que las falsas positivas queden bajo el umbral (→ a revisar, no a conteo).

## 16. Decisiones de diseño registradas

- **NMS 0.7** por defecto (trade-off estantes densos vs deduplicación).
- **Prompts filtrados por zona**: detectan *más* objetos que todas las clases juntas
  (compiten menos clases). Ej. `estante_gaseosas`→`estanteria_b`: 41 botellas con
  prompts de zona vs 31 con vocabulario completo.
- **Clases negativas (`prompts_background`)**: entran al softmax para mejorar precisión
  y se filtran del output. Se miden con `evaluar.py --no-background` (comparación).
- **Momento: no hay que asumir.** Cambios de prompts/umbrales se deciden con el harness de
  evaluación. Ej: enriquecer el prompt de pallet degradó precision (1→2 detecciones) y se
  revirtió; los umbrales óptimos del sweep calzan con los de config.
- **Modelo compartido + locks**: un solo YOLO en memoria para todas las conexiones.
- **IDs atómicos y re-asignación bajo colisión**: tolera seeds commiteadas con el repo.
- **`fuente`**: enum; se renombró `fuentes`→`fuente` en la API (match con la internals).
- **Resiliencia demo**: flujo de foto→carga manual como respaldo siempre disponible y
  ACK de guardado en el front RTC para no perder el snapshot.

## 17. Extender la aplicación

### Agregar un producto
1. Añadirlo a `productos_objetivo.json` (id, nombre, prompts, umbral, color).
2. Añadir su stock esperado a `stock_esperado.csv` en las zonas correspondientes.
3. Validar y calibrar con el harness `scripts/evaluar.py` (formato GT en
   `data/evaluacion/README.md`): mide P/R/F1/mAP y recomienda el umbral óptimo
   por producto (`--sweep "0.2 0.3 0.4 0.5"`).
4. Ajustar el umbral con el resultado y re-correr `evaluar.py`.

### Agregar una zona
1. Añadirla a `zonas.json` (con `productos_permitidos`).
2. Añadir stock en `stock_esperado.csv`.
3. `GET /zonas` y `GET /stock/{zona}` deberían reflejarla de inmediato.

### Cambiar el modelo
Reemplazar `DEFAULT_MODELO` en `real_inference.py` (manteniendo `detectar`/
`detectar_ndarray` y el mapeo por prompts: requiere API Ultralytics compatible).

## 18. Limitaciones conocidas

- CPU: ~1 fps de inferencia → el video procesa 1 frame/s.
- Vocabulario cerrado a los productos definidos; cero-shot depende de la calidad de los
  prompts (mitigado con `prompts_background` y medible con `scripts/evaluar.py`).
- Comparación contra stock es por **cantidad**, no por posición exacta.
- WebRTC: un cliente a la vez; `getUserMedia` exige `localhost`/HTTPS.
- El primer arranque descarga el modelo (~340 MB).
- El modo bbox del harness requiere anotar cajas GT; sin anotación se usa el modo conteo.