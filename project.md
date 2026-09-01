Protocolo RTC — Streaming de video en vivo para detección de inventario
Objetivo

Permitir que la demo en vivo del POC capture video de la cámara del navegador (celular o notebook) y lo envíe en tiempo real al backend de detección (Grounding DINO / YOLO-World), devolviendo las detecciones (tipo, estado, bounding box) superpuestas sobre el video, sin depender de subir fotos manualmente durante la demo.

Contexto del proyecto (resumen)
POC de conteo automatizado de inventario por visión computacional.
Backend: FastAPI + modelo de detección zero-shot (Grounding DINO o YOLO-World), sin dataset de entrenamiento propio.
Frontend: Streamlit (dashboard principal) — la parte de video en vivo puede vivir en un componente HTML/JS embebido o en una vista aparte, ya que Streamlit no maneja WebRTC nativamente sin librerías extra.
Uso: cámara → detección de productos → comparación contra stock declarado → evidencia visual.
Arquitectura RTC propuesta
[Navegador]                         [Backend FastAPI]
  getUserMedia()                      aiortc (Python WebRTC)
       │                                     │
       ▼                                     ▼
 RTCPeerConnection  ──── SDP offer ────►  RTCPeerConnection
       │              (signaling vía          │
       │               endpoint HTTP)         │
       ▼                                      ▼
  Video track enviado ─────────────►  VideoStreamTrack recibido
                                              │
                                              ▼
                                    Por cada frame (cada N ms):
                                    - correr detección
                                    - dibujar bounding boxes
                                    - clasificar tipo + estado
                                              │
                                              ▼
                              DataChannel ─── JSON con detecciones
                                              │
                                              ▼
       ◄──────────── resultados ─────────────┘
   Overlay en el <video> del navegador
Flujo paso a paso
El navegador pide permiso de cámara con getUserMedia({ video: true }).
Se crea un RTCPeerConnection en el navegador y se agrega el video track.
El navegador genera una SDP offer y la manda a un endpoint HTTP del backend (POST /rtc/offer) — este es el "signaling", no requiere servidor de signaling aparte para un POC simple (todo por HTTP directo).
El backend (usando aiortc) crea su propio RTCPeerConnection, recibe la offer, genera la answer y la devuelve en la respuesta HTTP.
Se establece la conexión peer-to-peer/servidor. El backend empieza a recibir frames de video.
Por cada frame (no hace falta procesar los 30fps — con 1 frame cada 500ms-1seg alcanza para la demo y baja mucho la carga de cómputo):
Se corre el modelo de detección zero-shot con los prompts de texto definidos (ej: "botella de plástico", "caja de cartón dañada").
Se arma un JSON con: clase detectada, confianza, bounding box (x, y, w, h), zona (si se seleccionó antes de iniciar la cámara).
El resultado se manda de vuelta al navegador por un DataChannel (canal de datos WebRTC, no necesita otra conexión).
El navegador dibuja los bounding boxes sobre el <video> en tiempo real (usando un <canvas> superpuesto) y actualiza el conteo en pantalla.
Al finalizar la captura (botón "Detener" o cierre de conexión), se guarda un resumen de detecciones + snapshot de evidencia en la base de datos (conteos_detectados), igual que en el flujo de carga de fotos/video ya existente.
Stack técnico específico para esta parte
Backend WebRTC: aiortc (librería Python para WebRTC, compatible con FastAPI/asyncio).
Frontend WebRTC: JavaScript nativo (RTCPeerConnection, getUserMedia) — no requiere frameworks adicionales.
Signaling: HTTP simple (un endpoint POST que intercambia SDP offer/answer), sin necesidad de servidor de signaling dedicado (ej. no hace falta Socket.IO) dado que es un POC de una sola sesión a la vez.
Overlay de resultados: <canvas> HTML sincronizado con el <video>, actualizado desde el DataChannel.
Tareas para OpenCode (checklist de implementación)
 Instalar y configurar aiortc en el backend FastAPI existente.
 Crear endpoint POST /rtc/offer que reciba la SDP offer del navegador y devuelva la SDP answer.
 Implementar una clase VideoTransformTrack (heredando de MediaStreamTrack de aiortc) que:
Reciba frames del track de video entrante.
Aplique throttling (procesar 1 de cada N frames, configurable).
Corra el modelo de detección zero-shot ya existente en el proyecto (reutilizar la función de inferencia actual, no reescribirla).
Devuelva el frame (con o sin overlay dibujado del lado del backend, a definir).
 Implementar el envío de resultados de detección por RTCDataChannel en formato JSON: { "detecciones": [{ "clase": str, "confianza": float, "bbox": [x,y,w,h] }], "timestamp": str }.
 Crear página HTML simple (puede estar embebida vía st.components.v1.html en Streamlit) con:
Botón "Iniciar cámara" / "Detener".
<video> mostrando el stream local.
<canvas> superpuesto dibujando los bounding boxes recibidos por el DataChannel.
Contador en pantalla de detecciones por clase.
 Al detener la captura, guardar en la base de datos (conteos_detectados) un resumen de las detecciones acumuladas junto con al menos un snapshot de evidencia (frame con overlay).
 Manejar el caso de error/desconexión: si la cámara falla o la conexión RTC se corta, mostrar mensaje claro y permitir volver al flujo de carga de foto/video como respaldo.
Criterios de aceptación
Al presionar "Iniciar cámara", el navegador pide permiso y muestra el video en menos de 3 segundos.
Las detecciones aparecen superpuestas sobre el video en un lapso razonable (no necesita ser 30fps; con 1-2 detecciones por segundo es suficiente para la demo).
Al detener la captura, queda un registro en la base de datos con evidencia (imagen) y las detecciones agregadas, visible luego en el dashboard de discrepancias.
Si falla la cámara o la conexión, el sistema no rompe — muestra error y permite usar el flujo de carga manual de fotos como alternativa.
Notas y riesgos a tener en cuenta
Latencia: procesar cada frame es costoso. Limitar a 1 frame por segundo (o menos) es clave para que la demo funcione fluido en una notebook sin GPU dedicada.
Red durante la demo: si el demo se hace en un lugar con wifi inestable, WebRTC puede fallar. Por eso el punto de "respaldo con flujo de carga manual" no es opcional — es el seguro de la demo en vivo.
HTTPS: getUserMedia requiere contexto seguro (HTTPS o localhost). Si se despliega en un servidor para la demo, verificar certificado válido o usar túnel tipo ngrok que da HTTPS automático.
Este componente es aditivo: el flujo de carga de fotos/video ya construido en las semanas anteriores no se reemplaza, sigue siendo el camino principal y el respaldo si RTC falla en vivo.