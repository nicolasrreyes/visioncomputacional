# Arquitectura — Auditoria Visual de Inventario (POC)

Documento de referencia visual y de decisiones para presentar el sistema ante el
jurado. Complementa el [Manual Tecnico](MANUAL_TECNICO.md).

---

## 1. Vista de componentes

```mermaid
flowchart TB
    subgraph Cliente["Cliente"]
        NAV[("Navegador")]
        NAV -->|Foto / video / camara| RUIA[/"Dashboard Streamlit<br/>:8501"/]
        NAV -->|POST /auditorias/imagen<br/>POST /rtc/offer| APIH
    end

    subgraph Backend["Backend FastAPI :8000"]
        APIH[/"API HTTP + WebRTC"/]
        APIH --> SVC["Service Layer<br/>(orquestacion)"]
        SVC --> CNT["Conteo + NMS<br/>app/detection"]
        SVC --> CMP["Comparacion vs stock<br/>app/inventory"]
        SVC --> MET["Metricas<br/>app/audits"]
        CNT --> DET["Detector YOLO-World<br/>app/detection/real_inference"]
    end

    subgraph Datos["Datos"]
        C1[("productos_objetivo.json")]
        C2[("zonas.json")]
        C3[("stock_esperado.csv")]
        C4[("outputs/auditorias/*.json")]
        C5[("inputs/ + outputs/evidencia/")]
    end

    DET -->|bounding boxes| VIS["Visualizacion<br/>app/visualization"]
    SVC --> C1 & C2 & C3
    SVC -->|guarda auditoria| C4
    VIS --> C5
    C4 -->|lee| RUIA
    C5 -->|evidencia anotada| RUIA

    subgraph Vivo["Video en vivo (WebRTC)"]
        RTC["aiortc<br/>app/rtc/webrtc"]
        PRC["ProcesadorVideo<br/>throttling 1 fps<br/>app/rtc/procesador"]
        RTC --> PRC --> DET
    end
    APIH <--> Vivo
```

## 2. Flujo de una auditoria (cualquier fuente)

```mermaid
sequenceDiagram
    participant F as Frontend (Streamlit/HTML)
    participant A as API (FastAPI)
    participant S as Service
    participant D as Detector (YOLO-World)
    participant R as Repository (JSON)

    F->>A: evidencia (foto | camara | fixture)
    A->>S: procesar
    S->>D: detectar(productos de la zona, prompts)
    D-->>S: detecciones (bbox + confianza)
    S->>S: NMS + umbral por producto + conteo
    S->>S: comparar contra stock_esperado de la zona
    S->>S: calcular 9 metricas
    S->>R: guardar auditoria (JSON + evidencia anotada)
    R-->>A: auditoria_id
    A-->>F: resumen + evidencia + discrepancias + metricas
```

## 3. Decisiones clave

| Decision | Por que |
| --- | --- |
| **Zero-shot (YOLO-World)** | No requiere dataset propio; se configura por prompts de texto. Permite agregar productos sin reentrenar. |
| **Modelo compartido + locks** | Un solo YOLO en memoria (~340 MB) para todas las conexiones; YOLO no es thread-safe → RLock serializa. |
| **Single source of truth en `data/`** | Productos, zonas y stock viven en JSON/CSV editables. Agregar producto/zona = editar datos, sin tocar codigo. |
| **Auditorias en JSON por archivo** | Simple, trazable, auditado por un humano en Git. Suficiente para POC; migrable a DB si escala. |
| **Throttling 1 fps en camara** | La inferencia en CPU es ~1 fps. Procesar 1 frame/s mantiene la demo fluida y baja la carga. |
| **WebRTC con aiortc (signaling HTTP)** | Sin servidor de signaling aparte: un endpoint POST intercambia SDP. Aditivo, no reemplaza el flujo de fotos. |
| **Flujo de fotos como respaldo** | La demo en vivo puede fallar (wifi, permisos, HTTPS). La carga manual de imagen siempre queda disponible. |

## 4. Camino de escalamiento (narrativa)

1. Hoy: un deposito, 5 zonas, 7 productos, una estacion de trabajo.
2. Proximo paso: N estaciones corriendo la misma app (cada una apunta a su repo de datos).
3. Escala: reemplazar el repositorio JSON por una base (PostgreSQL) y el modelo por una
   version optimizada (TensorRT / GPU) si la tasa de fotos crece.
4. Vista de negocio: el dashboard ejecutivo ya consolida ahorro, ROI y discrepancias;
   se puede extender a reportes por turno/sucursal.