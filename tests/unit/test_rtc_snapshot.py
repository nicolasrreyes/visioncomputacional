from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import numpy as np

from app.inventory.schemas import Deteccion
from app.rtc.webrtc import CONEXIONES, combinar_cuadros


def _procesador_fake(detecciones):
    return SimpleNamespace(
        zona_id="estanteria_a",
        ultimo_frame_rgb=np.zeros((60, 60, 3), dtype=np.uint8),
        ultimas_detecciones=detecciones,
    )


def test_combinar_cuadros_guarda_una_sola_vez(monkeypatch):
    det = Deteccion(producto_id="botella_plastica", label="bottle", confianza=0.8, bbox=[1, 1, 9, 9])
    guardados = {"n": 0, "zona": None}

    def fake_guardar(zona_id, detecciones, duracion_proceso_segundos, frame_rgb, **kwargs):
        guardados["n"] += 1
        guardados["zona"] = zona_id
        guardados["frame"] = frame_rgb

    monkeypatch.setattr("app.rtc.webrtc.guardar_auditoria_viva", fake_guardar)
    conexion = SimpleNamespace(
        pc=SimpleNamespace(),
        procesador=_procesador_fake([det]),
        inicio=0.0,
        snapshot_guardado=False,
    )

    combinar_cuadros(conexion)
    combinar_cuadros(conexion)

    assert guardados["n"] == 1
    assert guardados["zona"] == "estanteria_a"
    assert conexion.snapshot_guardado is True


def test_combinar_cuadros_sin_frame_no_guarda(monkeypatch):
    guardados = []
    monkeypatch.setattr("app.rtc.webrtc.guardar_auditoria_viva", lambda **kwargs: guardados.append(kwargs))
    conexion = SimpleNamespace(
        pc=SimpleNamespace(),
        procesador=_procesador_fake([]),
        inicio=0.0,
        snapshot_guardado=False,
    )
    combinar_cuadros(conexion)
    assert guardados == []
    # aunque no haya nada que guardar, queda marcado: el snapshot es exactly-once
    assert conexion.snapshot_guardado is True
    combinar_cuadros(conexion)
    assert guardados == []


def test_cerrar_cancela_task_y_apaga_ejecutor():
    import asyncio

    from app.rtc.webrtc import ConexionRtc

    async def escenario():
        tarea = asyncio.create_task(asyncio.Event().wait())
        conexion = ConexionRtc(pc=SimpleNamespace(), procesador=None)
        conexion.consumidor_task = tarea
        conexion.cerrar()
        conexion.cerrar()
        return tarea

    tarea = asyncio.run(escenario())
    assert tarea.cancelled()