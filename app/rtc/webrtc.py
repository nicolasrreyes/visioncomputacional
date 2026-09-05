from __future__ import annotations

import asyncio
import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any

from app.audits.service import build_prompts_con_background, guardar_auditoria_viva
from app.detection.real_inference import obtener_detector_compartido

logger = logging.getLogger(__name__)


@dataclass
class ConexionRtc:
    pc: Any
    procesador: Any
    ejecutor: ThreadPoolExecutor = field(default_factory=lambda: ThreadPoolExecutor(max_workers=1))
    canales: list[Any] = field(default_factory=list)
    inicio: float = field(default_factory=time.monotonic)
    snapshot_guardado: bool = False
    consumidor_task: Any = None

    def cerrar(self) -> None:
        """Cancela la tarea de consumo y libera el executor (no bloquea)."""
        if self.consumidor_task is not None and not self.consumidor_task.done():
            self.consumidor_task.cancel()
        self.ejecutor.shutdown(wait=False, cancel_futures=True)


CONEXIONES: dict[int, ConexionRtc] = {}


async def manejar_offer(sdp: str, zona_id: str) -> str:
    """Recibe la SDP offer del navegador y devuelve la SDP answer.

    Instala el pipeline: track de video -> ProcesadorVideo (throttling +
    deteccion en executor) -> DataChannel con el JSON de detecciones.
    """
    from aiortc import RTCPeerConnection, RTCSessionDescription

    from app.rtc.procesador import ProcesadorVideo

    prompts, prompts_negativos = build_prompts_con_background(zona_id)
    # Un solo modelo YOLO comparteado entre conexiones (~340 MB).
    procesador = ProcesadorVideo(
        zona_id=zona_id,
        prompts_por_producto=prompts,
        detector=obtener_detector_compartido(),
        prompts_negativos=prompts_negativos,
    )

    conexion = ConexionRtc(pc=RTCPeerConnection(), procesador=procesador)
    CONEXIONES[id(conexion.pc)] = conexion

    async def consumir_video(track: Any) -> None:
        while True:
            try:
                frame = await track.recv()
            except Exception:
                logger.exception("Error recibiendo frame del track; se corta el consumo")
                break
            rgb = frame.to_ndarray(format="rgb24")
            alto, ancho = rgb.shape[:2]
            loop = asyncio.get_running_loop()
            payload = await loop.run_in_executor(
                conexion.ejecutor, procesador.procesar_frame, rgb, ancho, alto
            )
            if payload:
                mensaje = json.dumps(payload)
                for canal in conexion.canales:
                    if canal.readyState == "open":
                        canal.send(mensaje)

    async def guardar_snapshot() -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(conexion.ejecutor, combinar_cuadros, conexion)
        mensaje = json.dumps({"tipo": "guardado"})
        for canal in conexion.canales:
            if canal.readyState == "open":
                canal.send(mensaje)

    @conexion.pc.on("track")
    async def on_track(track: Any) -> None:
        if track.kind == "video":
            conexion.consumidor_task = asyncio.ensure_future(consumir_video(track))

    @conexion.pc.on("datachannel")
    def on_datachannel(canal: Any) -> None:
        if canal.label != "detecciones":
            return
        conexion.canales.append(canal)

        @canal.on("message")
        def on_mensaje(mensaje: str) -> None:
            if mensaje == "detener":
                asyncio.ensure_future(guardar_snapshot())

        @canal.on("close")
        def on_cierre() -> None:
            if canal in conexion.canales:
                conexion.canales.remove(canal)

    @conexion.pc.on("connectionstatechange")
    async def on_estado() -> None:
        if conexion.pc.connectionState in ("failed", "closed"):
            await guardar_snapshot()
            try:
                await conexion.pc.close()
            except Exception:
                logger.warning("Error cerrando PeerConnection en limpieza (estado: %s)", conexion.pc.connectionState)
            conexion.cerrar()
            CONEXIONES.pop(id(conexion.pc), None)
            logger.info("Conexion RTC limpiada (id=%d)", id(conexion.pc))

    try:
        await conexion.pc.setRemoteDescription(RTCSessionDescription(sdp=sdp, type="offer"))
        respuesta = await conexion.pc.createAnswer()
        await conexion.pc.setLocalDescription(respuesta)
        return conexion.pc.localDescription.sdp
    except Exception:
        try:
            await conexion.pc.close()
        except Exception:
            logger.warning("Error cerrando PeerConnection tras fallo en el offer")
        conexion.cerrar()
        CONEXIONES.pop(id(conexion.pc), None)
        raise


def combinar_cuadros(conexion: ConexionRtc) -> None:
    """Guarda exactamente una vez la auditoria con el ultimo frame y sus detecciones."""
    if conexion.snapshot_guardado:
        return
    conexion.snapshot_guardado = True
    procesador = conexion.procesador
    frame = procesador.ultimo_frame_rgb
    detecciones = procesador.ultimas_detecciones
    if frame is None or not detecciones:
        return
    duracion = max(0.0, time.monotonic() - conexion.inicio)
    guardar_auditoria_viva(
        zona_id=procesador.zona_id,
        detecciones=detecciones,
        duracion_proceso_segundos=duracion,
        frame_rgb=frame,
    )