from fastapi.testclient import TestClient

from app.audits.repository import AuditoriaRepository
from app.api.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert isinstance(body["modelo_cargado"], bool)
    assert isinstance(body["zonas"], int)
    assert body["zonas"] >= 1
    assert isinstance(body["auditorias_guardadas"], int)
    assert isinstance(body["disco_libre_bytes"], int)


def test_lista_zonas_y_productos():
    assert client.get("/zonas").status_code == 200
    assert client.get("/productos").status_code == 200


def test_stock_por_zona():
    response = client.get("/stock/estanteria_a")
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_simular_auditoria(tmp_path, monkeypatch):
    repo = AuditoriaRepository(tmp_path / "auditorias")

    def _simular(zona_id, fixture, fuente="imagen"):
        from app.audits.service import simular_auditoria

        return simular_auditoria(zona_id=zona_id, fixture=fixture, fuente=fuente, repository=repo)

    monkeypatch.setattr("app.api.routes_detection.simular_auditoria", _simular)
    response = client.post(
        "/auditorias/simular",
        json={
            "zona_id": "estanteria_a",
            "fixture": "detecciones_estanteria_a.json",
            "fuente": "imagen",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["zona_id"] == "estanteria_a"
    assert "metricas" in body
    assert "discrepancias" in body


def test_zona_inexistente_devuelve_404():
    response = client.get("/stock/zona_inexistente")
    assert response.status_code == 404

