from __future__ import annotations

import sys

import numpy as np
from fastapi.testclient import TestClient

from app.api.main import app
from app.audits.repository import AuditoriaRepository
from app.inventory.schemas import Deteccion
from app.audits.service import guardar_auditoria_viva


client = TestClient(app)


def test_vista_rtc_servida():
    response = client.get("/rtc")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "RTCPeerConnection" in response.text
    assert "getUserMedia" in response.text


def test_offer_zona_desconocida_devuelve_400():
    response = client.post("/rtc/offer", json={"sdp": "v=0", "zona_id": "zona_inexistente"})
    assert response.status_code == 400


def test_offer_sin_aiortc_devuelve_503(monkeypatch):
    monkeypatch.setitem(sys.modules, "aiortc", None)

    class FakeRequest:
        def __init__(self):
            self.sdp = "v=0"
            self.zona_id = "estanteria_a"

    response = client.post("/rtc/offer", json={"sdp": "v=0", "zona_id": "estanteria_a"})
    assert response.status_code == 503
    assert "aiortc" in response.json()["detail"]


def test_guardar_auditoria_viva(tmp_path):
    det = Deteccion(producto_id="botella_plastica", label="plastic bottle", confianza=0.8, bbox=[5, 5, 40, 60])

    class RepoEnTmp(AuditoriaRepository):
        def __init__(self):
            super().__init__(tmp_path / "auditorias")

    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    auditoria = guardar_auditoria_viva(
        zona_id="estanteria_a",
        detecciones=[det],
        duracion_proceso_segundos=1.5,
        frame_rgb=frame,
        repository=RepoEnTmp(),
        inputs_dir=tmp_path / "inputs",
        evidencia_dir=tmp_path / "evidencia",
    )

    assert auditoria.fuente.value == "camara_viva"
    assert auditoria.archivo_original == "inputs/auditoria_001_original.jpg"
    assert auditoria.evidencia_path == "outputs/evidencia/auditoria_001_anotada.jpg"
    assert (tmp_path / "inputs" / "auditoria_001_original.jpg").exists()
    assert (tmp_path / "evidencia" / "auditoria_001_anotada.jpg").exists()
    assert auditoria.conteos == {"botella_plastica": 1}