from app.audits.repository import AuditoriaRepository
from app.audits.service import simular_auditoria


def test_flujo_completo_con_fixture_estanteria_a(tmp_path):
    auditoria = simular_auditoria(
        "estanteria_a",
        "detecciones_estanteria_a.json",
        repository=AuditoriaRepository(tmp_path),
    )
    assert auditoria.zona_id == "estanteria_a"
    assert auditoria.conteos["caja_carton_chica"] == 8
    assert auditoria.metricas.total_esperado == 26
    assert auditoria.metricas.cantidad_discrepancias == 2


def test_flujo_con_baja_confianza(tmp_path):
    auditoria = simular_auditoria(
        "estanteria_a",
        "detecciones_con_baja_confianza.json",
        repository=AuditoriaRepository(tmp_path),
    )
    assert auditoria.metricas.items_a_revisar == 5
    assert any(item.requiere_revision for item in auditoria.discrepancias)


def test_flujo_con_detecciones_vacias(tmp_path):
    auditoria = simular_auditoria(
        "estanteria_a",
        "detecciones_vacias.json",
        repository=AuditoriaRepository(tmp_path),
    )
    assert auditoria.conteos == {}
    assert auditoria.metricas.total_detectado == 0

