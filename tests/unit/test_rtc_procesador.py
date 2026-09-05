from __future__ import annotations

import numpy as np

from app.inventory.schemas import Deteccion
from app.rtc.procesador import ProcesadorVideo, build_payload


class DetectorStub:
    def __init__(self, detecciones):
        self.llamados = 0
        self.detecciones = detecciones
        self.ultimo_shape = None

    def detectar_ndarray(self, bgr, prompts, prompts_negativos=None):
        self.llamados += 1
        self.ultimo_shape = bgr.shape
        return self.detecciones


def test_build_payload_contrato():
    deteccion = Deteccion(
        producto_id="botella_plastica",
        label="plastic bottle",
        confianza=0.7456,
        bbox=[10.123, 20.456, 30.789, 40.0],
    )
    payload = build_payload([deteccion], 640, 480)
    assert payload["ancho"] == 640
    assert payload["alto"] == 480
    assert "timestamp" in payload
    (d,) = payload["detecciones"]
    assert d["producto_id"] == "botella_plastica"
    assert d["confianza"] == 0.746
    assert len(d["bbox"]) == 4
    assert d["bbox"] == [10.12, 20.46, 30.79, 40.0]
    # enriquecido con el detalle del producto desde productos_objetivo.json
    assert d["nombre"] == "Botella Plástica"
    assert d["color_bbox"] == "#4ECDC4"
    assert d["umbral_confianza"] == 0.3


def test_build_payload_producto_desconocido_us_fallback():
    deteccion = Deteccion(
        producto_id="no_existe",
        label="unknown thing",
        confianza=0.5,
        bbox=[1, 1, 2, 2],
    )
    payload = build_payload([deteccion], 640, 480)
    (d,) = payload["detecciones"]
    assert d["nombre"] == "unknown thing"
    assert d["color_bbox"] == "#FFFFFF"
    assert d["umbral_confianza"] is None


def test_procesador_video_throttling():
    det = Deteccion(producto_id="caja", label="box", confianza=0.9, bbox=[0, 0, 10, 10])
    procesador = ProcesadorVideo(
        zona_id="estanteria_a",
        prompts_por_producto={"caja": ["box"]},
        detector=DetectorStub([det]),
        intervalo_seg=60.0,
    )
    frame = np.zeros((64, 64, 3), dtype=np.uint8)
    primero = procesador.procesar_frame(frame, 64, 64)
    assert primero is not None
    assert procesador.ultimas_detecciones == [det]
    assert procesador.ultimo_frame_rgb is frame
    assert procesador.ultimas_dimensiones == (64, 64)

    segundo = procesador.procesar_frame(frame, 64, 64)
    assert segundo is None
    assert len(procesador.ultimas_detecciones) == 1


def test_procesador_video_sin_detecciones_igualmente_envia_payload():
    procesador = ProcesadorVideo(
        zona_id="estanteria_a",
        prompts_por_producto={"caja": ["box"]},
        detector=DetectorStub([]),
        intervalo_seg=0.0,
    )
    frame = np.zeros((32, 32, 3), dtype=np.uint8)
    payload = procesador.procesar_frame(frame, 32, 32)
    assert payload is not None
    assert payload["detecciones"] == []


def test_procesador_video_redimensiona_y_escala_bbox():
    det = Deteccion(producto_id="botella", label="bottle", confianza=0.9, bbox=[80, 120, 240, 216])
    stub = DetectorStub([det])
    procesador = ProcesadorVideo(
        zona_id="estanteria_a",
        prompts_por_producto={"botella": ["bottle"]},
        detector=stub,
        intervalo_seg=0.0,
        max_dimension=320,
    )
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    payload = procesador.procesar_frame(frame, 640, 480)
    assert stub.ultimo_shape == (240, 320, 3)
    assert payload["ancho"] == 640
    assert payload["alto"] == 480
    (d,) = payload["detecciones"]
    # El detector trabaja sobre la imagen a 320px (factor 0.5): su bbox en
    # coords reducidas [80,120,240,216] se devuelve a coords originales (x2)
    assert d["bbox"] == [160.0, 240.0, 480.0, 432.0]
    assert procesador.ultimo_frame_rgb is frame


def test_procesador_video_sin_redimension_si_es_chico():
    det = Deteccion(producto_id="botella", label="bottle", confianza=0.9, bbox=[5, 5, 20, 20])
    stub = DetectorStub([det])
    procesador = ProcesadorVideo(
        zona_id="estanteria_a",
        prompts_por_producto={"botella": ["bottle"]},
        detector=stub,
        intervalo_seg=0.0,
        max_dimension=320,
    )
    frame = np.zeros((200, 200, 3), dtype=np.uint8)
    payload = procesador.procesar_frame(frame, 200, 200)
    assert stub.ultimo_shape == (200, 200, 3)
    (d,) = payload["detecciones"]
    assert d["bbox"] == [5.0, 5.0, 20.0, 20.0]