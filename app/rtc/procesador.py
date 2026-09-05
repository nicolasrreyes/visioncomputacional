from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

from app.config import settings
from app.detection.real_inference import RealDetector, obtener_detector_compartido
from app.inventory.loader import cargar_productos
from app.inventory.schemas import Deteccion, Producto

DEFAULT_INTERVALO_SEG = settings.rtc_intervalo_seg
DEFAULT_MAX_DIMENSION = settings.rtc_max_dimension


def build_payload(
    detecciones: list[Deteccion],
    ancho: int,
    alto: int,
    productos: dict[str, Producto] | None = None,
) -> dict[str, Any]:
    """Arma el JSON que se envia por DataChannel al navegador."""
    productos = productos or cargar_productos()
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ancho": ancho,
        "alto": alto,
        "detecciones": [
            {
                "producto_id": d.producto_id,
                "label": d.label,
                "confianza": round(d.confianza, 3),
                "bbox": [round(v, 2) for v in d.bbox],
                "nombre": productos[d.producto_id].nombre if d.producto_id in productos else d.label,
                "color_bbox": productos[d.producto_id].color_bbox if d.producto_id in productos else "#FFFFFF",
                "umbral_confianza": productos[d.producto_id].umbral_confianza if d.producto_id in productos else None,
            }
            for d in detecciones
        ],
    }


class ProcesadorVideo:
    """Procesa frames del stream con throttling.

    El procesamiento es CPU-intensivo (YOLO-World); `procesar_frame` debe
    ejecutarse en un ThreadPoolExecutor para no bloquear el event loop.
    """

    def __init__(
        self,
        zona_id: str,
        prompts_por_producto: dict[str, list[str]],
        detector: RealDetector | None = None,
        intervalo_seg: float = DEFAULT_INTERVALO_SEG,
        max_dimension: int = DEFAULT_MAX_DIMENSION,
        productos: dict[str, Producto] | None = None,
    ) -> None:
        self.zona_id = zona_id
        self.prompts = prompts_por_producto
        self.detector = detector or obtener_detector_compartido()
        self.intervalo_seg = intervalo_seg
        self.max_dimension = max_dimension
        self.productos = productos or cargar_productos()
        self._ultimo_proceso = 0.0
        self.ultimas_detecciones: list[Deteccion] = []
        self.ultimo_frame_rgb: Any | None = None
        self._ancho = 0
        self._alto = 0

    @property
    def ultimas_dimensiones(self) -> tuple[int, int]:
        return self._ancho, self._alto

    def _dimensiones_inferencia(self, ancho: int, alto: int) -> tuple[int, int, float]:
        if self.max_dimension <= 0 or max(ancho, alto) <= self.max_dimension:
            return ancho, alto, 1.0
        factor = min(self.max_dimension / ancho, self.max_dimension / alto)
        return max(1, round(ancho * factor)), max(1, round(alto * factor)), factor

    def _redimensionar(self, frame_rgb: Any, ancho: int, alto: int) -> tuple[Any, int, int, float]:
        nuevo_ancho, nuevo_alto, factor = self._dimensiones_inferencia(ancho, alto)
        if factor == 1.0:
            return frame_rgb, nuevo_ancho, nuevo_alto, factor
        from PIL import Image

        redimensionado = Image.fromarray(frame_rgb).resize((nuevo_ancho, nuevo_alto), Image.BILINEAR)
        import numpy as np

        return np.asarray(redimensionado, dtype=np.uint8), nuevo_ancho, nuevo_alto, factor

    def procesar_frame(self, frame_rgb: Any, ancho: int, alto: int) -> dict[str, Any] | None:
        ahora = time.monotonic()
        if ahora - self._ultimo_proceso < self.intervalo_seg:
            return None
        self._ultimo_proceso = ahora

        self.ultimo_frame_rgb = frame_rgb
        self._ancho, self._alto = ancho, alto
        frame, _, _, factor = self._redimensionar(frame_rgb, ancho, alto)
        bgr = frame[:, :, ::-1].copy()
        detecciones = self.detector.detectar_ndarray(bgr, self.prompts)
        if factor != 1.0:
            detecciones = [
                d.model_copy(update={"bbox": [round(v / factor, 2) for v in d.bbox]})
                for d in detecciones
            ]
        self.ultimas_detecciones = detecciones
        return build_payload(detecciones, ancho, alto, self.productos)