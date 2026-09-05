from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image

from app.api.main import app
from app.detection.real_inference import ModeloNoDisponibleError


client = TestClient(app)


def _imagen_bytes() -> BytesIO:
    buffer = BytesIO()
    Image.new("RGB", (40, 40), (240, 240, 240)).save(buffer, "JPEG")
    buffer.seek(0)
    return buffer


def test_auditoria_inexistente_404():
    response = client.get("/auditorias/auditoria_9999")
    assert response.status_code == 404


def test_imagen_archivo_no_encontrado_404(monkeypatch):
    def _falla(zona_id, ruta_imagen, fuente):
        raise FileNotFoundError("Imagen inexistente")

    monkeypatch.setattr("app.api.routes_detection.procesar_imagen", _falla)
    response = client.post(
        "/auditorias/imagen",
        data={"zona_id": "estanteria_a"},
        files={"archivo": ("foto.jpg", _imagen_bytes(), "image/jpeg")},
    )
    assert response.status_code == 404


def test_imagen_modelo_no_disponible_503(monkeypatch):
    def _falla(zona_id, ruta_imagen, fuente):
        raise ModeloNoDisponibleError("Ultralytics no instalado")

    monkeypatch.setattr("app.api.routes_detection.procesar_imagen", _falla)
    response = client.post(
        "/auditorias/imagen",
        data={"zona_id": "estanteria_a"},
        files={"archivo": ("foto.jpg", _imagen_bytes(), "image/jpeg")},
    )
    assert response.status_code == 503


def test_simular_fixture_inexistente_404(monkeypatch):
    def _falla(zona_id, fixture, fuente="imagen"):
        raise FileNotFoundError(f"Fixture inexistente: {fixture}")

    monkeypatch.setattr("app.api.routes_detection.simular_auditoria", _falla)
    response = client.post(
        "/auditorias/simular",
        json={"zona_id": "estanteria_a", "fixture": "no_existe.json", "fuente": "imagen"},
    )
    assert response.status_code == 404


def test_simular_zona_invalida_400(monkeypatch):
    def _falla(zona_id, fixture, fuente="imagen"):
        raise ValueError(f"Zona desconocida: {zona_id}")

    monkeypatch.setattr("app.api.routes_detection.simular_auditoria", _falla)
    response = client.post(
        "/auditorias/simular",
        json={"zona_id": "zona_invalida", "fixture": "detecciones_estanteria_a.json", "fuente": "imagen"},
    )
    assert response.status_code == 400


def test_sdp_sobredimensionado_422():
    response = client.post(
        "/rtc/offer",
        json={"sdp": "x" * 300_000, "zona_id": "estanteria_a"},
    )
    assert response.status_code == 422