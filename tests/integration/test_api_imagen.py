from io import BytesIO

from PIL import Image

from app.audits.repository import AuditoriaRepository
from app.inventory.schemas import Deteccion


class DetectorEndpointStub:
    def __init__(self, modelo="", device=None, verbose=False):
        self.modelo = modelo

    def detectar(self, imagen, prompts_por_producto, confianza=0.25, prompts_negativos=None):
        return [
            Deteccion(producto_id="caja_carton_chica", label="small cardboard box", confianza=0.84, bbox=[10, 10, 60, 80]),
            Deteccion(producto_id="botella_plastica", label="plastic bottle", confianza=0.79, bbox=[100, 10, 160, 90]),
        ]


def _imagen_bytes() -> BytesIO:
    buffer = BytesIO()
    Image.new("RGB", (200, 200), (240, 240, 240)).save(buffer, "JPEG")
    buffer.seek(0)
    return buffer


def test_endpoint_imagen_genera_auditoria(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "app.audits.service.obtener_detector_compartido", lambda: DetectorEndpointStub()
    )
    monkeypatch.setattr("app.audits.service.INPUTS_DIR", tmp_path / "inputs")
    monkeypatch.setattr("app.audits.service.EVIDENCIA_DIR", tmp_path / "evidencia")

    class RepoEnTmp(AuditoriaRepository):
        def __init__(self):
            super().__init__(tmp_path / "auditorias")

    monkeypatch.setattr("app.audits.service.AuditoriaRepository", RepoEnTmp)

    from fastapi.testclient import TestClient

    from app.api.main import app

    client = TestClient(app)
    response = client.post(
        "/auditorias/imagen",
        data={"zona_id": "estanteria_a"},
        files={"archivo": ("estante.jpg", _imagen_bytes(), "image/jpeg")},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["conteos"]["caja_carton_chica"] == 1
    assert body["conteos"]["botella_plastica"] == 1
    assert body["archivo_original"] == "inputs/auditoria_001_original.jpg"
    assert body["evidencia_path"] == "outputs/evidencia/auditoria_001_anotada.jpg"
    assert (tmp_path / "evidencia" / "auditoria_001_anotada.jpg").exists()
    assert (tmp_path / "inputs" / "auditoria_001_original.jpg").exists()


def test_endpoint_imagen_rechaza_no_imagen(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from app.api.main import app

    client = TestClient(app)
    response = client.post(
        "/auditorias/imagen",
        data={"zona_id": "estanteria_a"},
        files={"archivo": ("documento.txt", b"no soy imagen", "text/plain")},
    )
    assert response.status_code == 400


def test_endpoint_imagen_zona_desconocida_400(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from app.api.main import app

    client = TestClient(app)
    response = client.post(
        "/auditorias/imagen",
        data={"zona_id": "zona_inexistente"},
        files={"archivo": ("foto.jpg", _imagen_bytes(), "image/jpeg")},
    )
    assert response.status_code == 400


def test_endpoint_imagen_rechaza_archivo_gigante_413(tmp_path, monkeypatch):
    import app.api.routes_detection as routes

    monkeypatch.setattr(routes, "MAX_UPLOAD_BYTES", 100)

    from fastapi.testclient import TestClient

    from app.api.main import app

    client = TestClient(app)
    response = client.post(
        "/auditorias/imagen",
        data={"zona_id": "estanteria_a"},
        files={"archivo": ("gran.jpg", _imagen_bytes(), "image/jpeg")},
    )
    assert response.status_code == 413


def test_endpoint_imagen_acepta_fuente_form(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "app.audits.service.obtener_detector_compartido", lambda: DetectorEndpointStub()
    )

    class RepoEnTmp(AuditoriaRepository):
        def __init__(self):
            super().__init__(tmp_path / "auditorias")

    monkeypatch.setattr("app.audits.service.AuditoriaRepository", RepoEnTmp)
    monkeypatch.setattr("app.audits.service.INPUTS_DIR", tmp_path / "inputs")
    monkeypatch.setattr("app.audits.service.EVIDENCIA_DIR", tmp_path / "evidencia")

    from fastapi.testclient import TestClient

    from app.api.main import app

    client = TestClient(app)
    response = client.post(
        "/auditorias/imagen",
        data={"zona_id": "estanteria_a", "fuente": "video"},
        files={"archivo": ("estante.jpg", _imagen_bytes(), "image/jpeg")},
    )
    assert response.status_code == 200, response.text
    assert response.json()["fuente"] == "video"
    assert "fuentes" not in response.json()