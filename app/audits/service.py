from __future__ import annotations

import time

from app.audits.metrics import calcular_metricas
from app.audits.repository import AuditoriaRepository
from app.detection.counting import contar_detecciones
from app.detection.mock_inference import cargar_detecciones_fixture
from app.inventory.compare import comparar_con_stock
from app.inventory.loader import cargar_productos, cargar_zonas, stock_por_zona
from app.inventory.schemas import Auditoria, FuenteAuditoria


def simular_auditoria(
    zona_id: str,
    fixture: str,
    fuente: FuenteAuditoria = FuenteAuditoria.IMAGEN,
    repository: AuditoriaRepository | None = None,
) -> Auditoria:
    inicio = time.perf_counter()
    zonas = cargar_zonas()
    if zona_id not in zonas:
        raise ValueError(f"Zona desconocida: {zona_id}")

    productos = cargar_productos()
    detecciones = cargar_detecciones_fixture(fixture)
    resultado_conteo = contar_detecciones(detecciones, productos)
    stock_zona = stock_por_zona(zona_id)
    discrepancias = comparar_con_stock(
        stock_zona=stock_zona,
        conteos=resultado_conteo.conteos,
        detecciones_validas=resultado_conteo.detecciones_validas,
        detecciones_a_revisar=resultado_conteo.detecciones_a_revisar,
    )
    duracion = time.perf_counter() - inicio
    metricas = calcular_metricas(
        discrepancias=discrepancias,
        detecciones_validas=resultado_conteo.detecciones_validas,
        detecciones_a_revisar=resultado_conteo.detecciones_a_revisar,
        duracion_proceso_segundos=duracion,
    )
    repo = repository or AuditoriaRepository()
    auditoria = Auditoria.nueva(
        auditoria_id=repo.siguiente_id(),
        zona_id=zona_id,
        fuente=fuente,
        duracion_proceso_segundos=round(duracion, 4),
        detecciones=detecciones,
        conteos=resultado_conteo.conteos,
        discrepancias=discrepancias,
        metricas=metricas,
    )
    repo.guardar(auditoria)
    return auditoria

