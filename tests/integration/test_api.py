from fastapi.testclient import TestClient

from app.api.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_lista_zonas_y_productos():
    assert client.get("/zonas").status_code == 200
    assert client.get("/productos").status_code == 200


def test_stock_por_zona():
    response = client.get("/stock/estanteria_a")
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_simular_auditoria():
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

