# Manual Técnico para Presentación — Auditoría Visual de Inventario

Documento de apoyo para la presentación ante el jurado (IACKATON CDA, iniciativa 1).
El objetivo es mostrar **qué se construyó, cómo está construido y por qué es
sólido** — en un formato que se pueda proyectar o repartir junto con la demo.

> Complementa: [ARQUITECTURA.md](ARQUITECTURA.md) (diagramas), [MANUAL_TECNICO.md](MANUAL_TECNICO.md)
> (referencia completa), [DEMO.md](DEMO.md) (guion de la demo).

---

## 1. Problema que resuelve

El inventario se cuenta **a mano**: una persona recorre el depósito, cuenta cajas
y botellas, carga el resultado en un planilla y recién ahí se comparan las cifras
contra el stock esperado.

**Consecuencias:** tiempo alto, errores humanos, stock desactualizado, diferencias
que aparecen después (nunca durante el recuento).

**Nuestra solución:** una foto (o la cámara en vivo) de una estantería → un modelo
de visión por computadora cuenta los productos → el sistema compara contra el stock
esperado de esa zona, marca **sobrantes, faltantes y discrepancias**, y deja una
**evidencia visual anotada** + **métricas ejecutivas**.

```text
Foto / cámara → YOLO-World (detección) → conteo + NMS → comparación vs stock → auditoría + evidencia
```

---

## 2. Qué se construyó (resumen ejecutivo)

| Capa | Qué hace | Cómo |
| --- | --- | --- |
| **Ingesta** | Foto subida, video en vivo (WebRTC), simulación | Dashboard + API |
| **Detección** | Encuentra los productos y los enmarca | YOLO-World zero-shot (~340 MB, local) |
| **Inteligencia** | Cuenta, deduplica (NMS), filtra por confianza | `app/detection/counting.py` |
| **Auditoría** | Compara contra stock, calcula KPIs, persiste | `app/audits/` + `outputs/auditorias/*.json` |
| **Evidencia** | Genera la imagen con bounding boxes por producto | `app/visualization/draw.py` |
| **Dashboard** | Ejecutivo: KPIs, evidencia, discrepancias, ROI | Streamlit |

**Tres fuentes de evidencia soportadas** (una sola lógica de auditoría para todas):

1. **Simulación** (fixtures) — para demostrar el flujo sin depender del modelo.
2. **Foto real** — el flujo principal de la demo.
3. **Cámara en vivo (WebRTC)** — 1 frame por segundo con bounding boxes en tiempo real.

---

## 3. Decisiones técnicas clave (y por qué)

### 3.1 Modelo zero-shot (YOLO-World)
- No requiere dataset propio ni entrenamiento: se configura con **prompts de texto**.
- Cada producto tiene 2-3 prompts (inglés + español) en `data/productos_objetivo.json`.
- **Agregar un producto = editar un JSON.** No hace falta reentrenar ni regresar a GPU.

### 3.2 Modelo compartido + locks
- Un único YOLO en memoria (~340 MB) para todas las conexiones.
- YOLO no es thread-safe → un `RLock` global serializa `set_classes` + `predict`.
- Esto es lo que permite que el flujo de foto y la cámara convivan sin duplicar memoria.

### 3.3 NMS (Supresión de No Máximos) antes del conteo
- Umbral `solapamiento_maximo = 0.7` (IoU) deduplica cajas del mismo producto sin
  fundir productos contiguos — estudiado empíricamente contra estantes densos.
- Umbrales de confianza **por producto** (`data/productos_objetivo.json`).
- Las detecciones bajo umbral no se cuentan: van a la lista **"a revisar"** (y el
  producto queda con estado `REVISAR`). **El sistema no "inventa": separa lo
  confiable de lo dudoso.**

### 3.4 Video en vivo con aiortc (WebRTC)
- `GET /rtc` sirve el reproductor; `POST /rtc/offer` intercambia el SDP (signaling HTTP, sin servidor extra).
- **Throttling 1 fps** (`VISINVENT_RTC_INTERVALO_SEG`): procesar 1 frame por segundo
  mantiene la demo fluida en CPU y baja la carga ~30× frente a procesar todos los frames.
- Las detecciones vuelven por **DataChannel** como JSON y se dibujan en un `<canvas>`
  superpuesto en el navegador.
- Al **detener**, el último frame se guarda como auditoría `camara_viva` con evidencia anotada.

### 3.5 Datos configurados, no hardcodeados
- `data/zonas.json` (5 zonas, con productos permitidos),
  `data/productos_objetivo.json` (7 productos, prompts, umbral, color),
  `data/stock_esperado.csv` (stock por zona).
- Puntos: agregar una zona o producto no requiere tocar código.

---

## 4. Números que importan

| Indicador | Valor |
| --- | --- |
| Productos detectables | 7 (configurables) |
| Zonas modeladas | 5 |
| Flujos de ingesta | 3 (simulación, foto, cámara en vivo) |
| Tests automatizados | **78** (unit + integración, sin GPU ni internet) |
| Velocidad de inferencia | ~1 fps en CPU (suficiente para la demo) |
| Modelo | YOLO-World `yolov8s-worldv2.pt`, zero-shot, ~340 MB |
| Peso de la app | ~0 dependencias externas de red en runtime (todo local) |
| Métricas ejecutivas | 9 KPIs por auditoría + ROI/ahorro globales en el dashboard |

---

## 5. Qué lo hace "empresarial" (no un POC de garaje)

Aplicado en esta iteración:

| Capacidad | Implementación |
| --- | --- |
| **Observabilidad** | Logging estructurado; ningún `except` silencioso (el pipeline RTC loguea cada fallo). |
| **Health check real** | `GET /health` reporta modelo cargado, zonas, auditorías y disco libre (no un 200 fijo). |
| **Configuración por entorno** | `app/config.py` con env vars `VISINVENT_*` (tamaño de upload, throttling, puerto, log level). |
| **Contratos de API** | `response_model=` Pydantic en todas las rutas → Swagger (`/docs`) documentado. |
| **CORS** | Configurable; el dashboard funciona desde cualquier máquina de la red. |
| **Manejo de errores HTTP** | 400/404/413/422/503 con mensajes claros en español (validados con tests). |
| **Tests como red de seguridad** | 78 pruebas que no dependen del modelo real (stubs) — refactorizable con confianza. |
| **Trazabilidad** | Cada auditoría = JSON (detecciones, conteos, discrepancias, métricas) + evidencia anotada nombrada por ID secuencial. |

---

## 6. Flujo de la demo técnica (qué mostrar y qué contar)

1. **`scripts/run_demo.ps1`** levanta API + dashboard (todo en uno).
2. Abrir **`http://127.0.0.1:8000/docs`** → mostrar que la API está documentada
   (Swagger) con contratos de entrada/salida.
3. Llamar **`GET /health`** → mostrar que reporta estado real (no un 200 fijo).
4. **Foto real** (`data/demo_images/estante_gaseosas.jpg` → `estanteria_b`):
   mostrar KPIs, evidencia anotada con bounding boxes coloridos, discrepancias y el JSON.
5. **Cámara en vivo** (`/rtc`): mostrar la superposición en tiempo real y el guardado
   como auditoría `camara_viva`.
6. **Métricas ejecutivas**: ahorro de tiempo, ROI estimado, distribuciones por zona.
7. Mencionar **configurabilidad**: umbrales/prompts/clases negativas en JSON, env vars,
   y que agregar un producto no toca código.
8. **Calidad medible** (opcional, si sobra tiempo): correr `scripts/evaluar.py --modo conteo`
   y mostrar P/R/F1 + que el umbral óptimo del sweep calza con el de config. Es la apertura
   a "cómo cambiamos de rubro sin romper calidad".

Guion paso a paso completo (con números esperados): [docs/DEMO.md](DEMO.md).

---

## 7. Camino de escalamiento (para el cierre)

- **Hoy:** 1 depósito, 5 zonas, 7 productos, una estación.
- **Mañana:** N estaciones corriendo la misma app; cada una con su `data/`.
- **Escala real:** repositorio JSON → base de datos (PostgreSQL); modelo CPU → GPU/TensorRT
  si la tasa de fotos crece; vistas ejecutivas por sucursal/turno.
- **Nuevos productos:** sin reentrenar (zero-shot), solo editar config; se suman clases
  negativas (`prompts_background`) para bajar falsos positivos.
- **Nuevos rubros:** el harness `scripts/evaluar.py` mide P/R/F1/mAP; si el cero-shot
  no alcanza para un catálogo de marca, se entrena un modelo por catálogo sin cambiar la app.

La arquitectura está preparada para ese camino: capas desacopladas, detección
intercambiable (mock ↔ real), datos 100% configurables y tests que permiten evolucionar sin romper.

---

## 8. Stack

| Componente | Tecnología |
| --- | --- |
| API | FastAPI + Uvicorn |
| Dashboard | Streamlit |
| Detección | Ultralytics YOLO-World (zero-shot) |
| Video en vivo | aiortc (WebRTC) + JS nativo |
| Validación | Pydantic v2 |
| Imágenes | Pillow + numpy |
| Tests | pytest (78) |
| Datos | JSON + CSV (configuración) y JSON (auditorías) |

---

## 9. Referencias

- [docs/ARQUITECTURA.md](ARQUITECTURA.md) — diagramas de componentes y flujo.
- [docs/MANUAL_TECNICO.md](MANUAL_TECNICO.md) — referencia técnica completa (18 secciones).
- [docs/MANUAL_DE_USO.md](MANUAL_DE_USO.md) — guía práctica de uso.
- [docs/DEMO.md](DEMO.md) — guion de la demo paso a paso.