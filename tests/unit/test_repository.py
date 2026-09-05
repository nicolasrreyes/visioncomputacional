from __future__ import annotations

from app.audits.repository import AuditoriaRepository
from app.inventory.schemas import Auditoria, Discrepancia, FuenteAuditoria, MetricasAuditoria


def _auditoria(auditoria_id: str, zona_id: str = "estanteria_a") -> Auditoria:
    return Auditoria.nueva(
        auditoria_id=auditoria_id,
        zona_id=zona_id,
        fuente=FuenteAuditoria.IMAGEN,
        duracion_proceso_segundos=0.1,
        detecciones=[],
        conteos={},
        discrepancias=[],
        metricas=MetricasAuditoria(
            total_esperado=0,
            total_detectado=0,
            diferencia_total=0,
            cantidad_discrepancias=0,
            porcentaje_coincidencia=100.0,
            confianza_promedio=0.0,
            items_a_revisar=0,
            tiempo_ahorrado_minutos=0.0,
        ),
    )


def test_siguiente_id_consecutivo(tmp_path):
    repo = AuditoriaRepository(tmp_path)
    assert repo.siguiente_id() == "auditoria_001"
    repo.guardar(_auditoria(repo.siguiente_id()))
    repo.guardar(_auditoria(repo.siguiente_id()))
    assert repo.siguiente_id() == "auditoria_003"


def test_siguiente_id_no_se_resetea_al_borrar_archivos(tmp_path):
    repo = AuditoriaRepository(tmp_path)
    repo.guardar(_auditoria("auditoria_001"))
    repo.guardar(_auditoria("auditoria_002"))
    (tmp_path / "auditoria_001.json").unlink()
    # debe seguir en 3 (max+1) aunque falte la 001 (no se reutilizan ids altos)
    assert repo.siguiente_id() == "auditoria_003"


def test_guardar_colision_reasigna_id(tmp_path):
    repo = AuditoriaRepository(tmp_path)
    repo.guardar(_auditoria("auditoria_001"))
    devuelto = repo.guardar(_auditoria("auditoria_001"))
    assert devuelto == "auditoria_002"
    assert (tmp_path / "auditoria_001.json").exists()
    assert (tmp_path / "auditoria_002.json").exists()
    assert repo.cargar("auditoria_002").auditoria_id == "auditoria_002"


def test_guardar_y_cargar_roundtrip(tmp_path):
    repo = AuditoriaRepository(tmp_path)
    repo.guardar(_auditoria("auditoria_001", zona_id="palletera"))
    auditoria = repo.cargar("auditoria_001")
    assert auditoria.zona_id == "palletera"
    assert repo.listar(zona_id="palletera")[0].auditoria_id == "auditoria_001"