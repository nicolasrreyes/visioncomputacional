from app.audits.repository import AuditoriaRepository
from app.audits.service import simular_auditoria


def test_guarda_y_carga_auditoria(tmp_path):
    repo = AuditoriaRepository(tmp_path)
    auditoria = simular_auditoria("estanteria_a", "detecciones_estanteria_a.json", repository=repo)
    cargada = repo.cargar(auditoria.auditoria_id)
    assert cargada.auditoria_id == auditoria.auditoria_id
    assert cargada.zona_id == "estanteria_a"


def test_lista_auditorias_por_zona(tmp_path):
    repo = AuditoriaRepository(tmp_path)
    simular_auditoria("estanteria_a", "detecciones_estanteria_a.json", repository=repo)
    simular_auditoria("estanteria_b", "detecciones_vacias.json", repository=repo)
    assert len(repo.listar()) == 2
    assert len(repo.listar(zona_id="estanteria_a")) == 1

