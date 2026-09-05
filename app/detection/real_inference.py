from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

from app.inventory.schemas import Deteccion


DEFAULT_MODELO = "yolov8s-worldv2.pt"
DEFAULT_CONFIANZA = 0.25

_DETECCION_LOCK = threading.RLock()
_DETECTOR_COMPARTIDO: "RealDetector | None" = None


def obtener_detector_compartido(modelo: str = DEFAULT_MODELO) -> "RealDetector":
    """Devuelve una instancia unica del detector (la carga pesa ~340 MB).

    Las conexiones RTC concurrentes comparten un solo modelo; el lock global
    serializa set_classes + predict porque YOLO-World no es thread-safe.
    """
    global _DETECTOR_COMPARTIDO
    with _DETECCION_LOCK:
        if _DETECTOR_COMPARTIDO is None:
            _DETECTOR_COMPARTIDO = RealDetector(modelo=modelo)
        return _DETECTOR_COMPARTIDO


class ModeloNoDisponibleError(RuntimeError):
    pass


class RealDetector:
    """Detector zero-shot basado en YOLO-World (Ultralytics).

    El modelo se descarga automaticamente en el primer uso. La carga es
    lazy para no penalizar los tests ni los flujos que usan fixtures.
    """

    def __init__(
        self,
        modelo: str = DEFAULT_MODELO,
        device: str | None = None,
        verbose: bool = False,
    ) -> None:
        self.modelo = modelo
        self.device = device or self._detectar_device()
        self.verbose = verbose
        self._model: Any | None = None
        self._prompts_actuales: list[str] | None = None

    @staticmethod
    def _detectar_device() -> str:
        try:
            import torch
        except ImportError:
            return "cpu"
        return "cuda" if torch.cuda.is_available() else "cpu"

    def _cargar_modelo(self) -> Any:
        if self._model is None:
            try:
                from ultralytics import YOLO
            except ImportError as exc:
                raise ModeloNoDisponibleError(
                    "Ultralytics no esta instalado. Ejecuta: pip install ultralytics"
                ) from exc
            self._model = YOLO(self.modelo)
            self._model.to(self.device)
        return self._model

    def _activar_prompts(self, prompts: list[str]) -> None:
        if self._model is None:
            self._cargar_modelo()
        if self._prompts_actuales != prompts:
            self._model.set_classes(prompts)
            self._prompts_actuales = prompts

    def detectar(
        self,
        imagen: str | Path,
        prompts_por_producto: dict[str, list[str]],
        confianza: float = DEFAULT_CONFIANZA,
    ) -> list[Deteccion]:
        """Ejecuta deteccion zero-shot sobre una imagen en disco.

        prompts_por_producto: mapea producto_id -> lista de prompts en texto.
        Devuelve Deteccion con bbox en pixeles [x_min, y_min, x_max, y_max].
        """
        if not prompts_por_producto:
            return []

        ruta = Path(imagen)
        if not ruta.exists():
            raise FileNotFoundError(f"No existe la imagen: {imagen}")

        mapeo, prompts_planos = self._construir_mapeo(prompts_por_producto)
        with _DETECCION_LOCK:
            self._activar_prompts(prompts_planos)
            resultados = self._model.predict(
                source=str(ruta),
                conf=confianza,
                verbose=self.verbose,
            )

        alto, ancho = self._dimensiones(resultados, ruta)
        return self._procesar_resultados(resultados, ancho, alto, mapeo)

    def detectar_ndarray(
        self,
        imagen: Any,
        prompts_por_producto: dict[str, list[str]],
        confianza: float = DEFAULT_CONFIANZA,
    ) -> list[Deteccion]:
        """Ejecuta deteccion zero-shot sobre un frame en memoria (ndarray BGR).

        Usado por el pipeline de video en vivo (frames de la camara).
        """
        if not prompts_por_producto:
            return []

        mapeo, prompts_planos = self._construir_mapeo(prompts_por_producto)
        with _DETECCION_LOCK:
            self._activar_prompts(prompts_planos)
            resultados = self._model.predict(
                source=imagen,
                conf=confianza,
                verbose=self.verbose,
            )

        alto, ancho = self._dimensiones_ndarray(resultados, imagen)
        return self._procesar_resultados(resultados, ancho, alto, mapeo)

    @staticmethod
    def _construir_mapeo(
        prompts_por_producto: dict[str, list[str]],
    ) -> tuple[list[tuple[int, str, str]], list[str]]:
        mapeo: list[tuple[int, str, str]] = []
        for producto_id, prompts in prompts_por_producto.items():
            for prompt in prompts:
                mapeo.append((len(mapeo), producto_id, prompt))
        prompts_planos = [entry[2] for entry in mapeo]
        assert len(prompts_planos) == len(mapeo)
        return mapeo, prompts_planos

    def _procesar_resultados(
        self,
        resultados: list[Any],
        ancho: int,
        alto: int,
        mapeo_indice_producto: list[tuple[int, str, str]],
    ) -> list[Deteccion]:
        detecciones: list[Deteccion] = []
        for resultado in resultados:
            clases = RealDetector._a_lista(resultado.boxes.cls)
            confianzas = RealDetector._a_lista(resultado.boxes.conf)
            cajas = RealDetector._a_lista(resultado.boxes.xyxy)
            for pos, (clase, conf) in enumerate(zip(clases, confianzas)):
                _, producto_id, prompt = mapeo_indice_producto[int(clase)]
                bbox = self._a_pixeles(RealDetector._a_lista(cajas[pos]), ancho, alto)
                detecciones.append(
                    Deteccion(
                        producto_id=producto_id,
                        label=prompt,
                        confianza=float(conf),
                        bbox=bbox,
                        estado_visual="desconocido",
                    )
                )
        return detecciones

    @staticmethod
    def _a_lista(valor: Any) -> list[Any]:
        if hasattr(valor, "tolist"):
            return valor.tolist()
        return list(valor)

    @staticmethod
    def _dimensiones(resultados: list[Any], ruta: Path) -> tuple[int, int]:
        if resultados:
            shape = getattr(resultados[0].orig_shape, "__len__", None)
            if shape is not None and len(resultados[0].orig_shape) == 2:
                alto, ancho = resultados[0].orig_shape
                return int(alto), int(ancho)
        from PIL import Image

        with Image.open(ruta) as imagen:
            ancho, alto = imagen.size
        return alto, ancho

    @staticmethod
    def _dimensiones_ndarray(resultados: list[Any], imagen: Any) -> tuple[int, int]:
        if resultados:
            shape = getattr(resultados[0].orig_shape, "__len__", None)
            if shape is not None and len(resultados[0].orig_shape) == 2:
                alto, ancho = resultados[0].orig_shape
                return int(alto), int(ancho)
        alto, ancho = imagen.shape[0], imagen.shape[1]
        return int(alto), int(ancho)

    @staticmethod
    def _a_pixeles(caja: list[float], ancho: int, alto: int) -> list[float]:
        x1, y1, x2, y2 = caja
        if max(x1, y1, x2, y2) <= 1.0:
            x1, x2 = x1 * ancho, x2 * ancho
            y1, y2 = y1 * alto, y2 * alto
        return [round(x1, 2), round(y1, 2), round(x2, 2), round(y2, 2)]