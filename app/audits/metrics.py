from __future__ import annotations

from app.inventory.schemas import Deteccion, Discrepancia, EstadoOperativo, MetricasAuditoria


def calcular_metricas(
    discrepancias: list[Discrepancia],
    detecciones_validas: list[Deteccion],
    detecciones_a_revisar: list[Deteccion],
    duracion_proceso_segundos: float,
) -> MetricasAuditoria:
    total_esperado = sum(item.cantidad_esperada for item in discrepancias)
    total_detectado = sum(item.cantidad_detectada for item in discrepancias)
    diferencia_total = total_detectado - total_esperado
    cantidad_discrepancias = sum(
        1 for item in discrepancias if item.estado_operativo != EstadoOperativo.OK
    )
    porcentaje_coincidencia = max(
        0,
        100 - (abs(diferencia_total) / max(total_esperado, 1) * 100),
    )
    confianza_promedio = (
        sum(d.confianza for d in detecciones_validas) / len(detecciones_validas)
        if detecciones_validas
        else 0
    )
    tiempo_manual_estimado_min = total_esperado * 0.25
    tiempo_ia_estimado_min = duracion_proceso_segundos / 60
    tiempo_ahorrado = max(0.0, tiempo_manual_estimado_min - tiempo_ia_estimado_min)

    return MetricasAuditoria(
        total_esperado=total_esperado,
        total_detectado=total_detectado,
        diferencia_total=diferencia_total,
        cantidad_discrepancias=cantidad_discrepancias,
        porcentaje_coincidencia=round(porcentaje_coincidencia, 2),
        confianza_promedio=round(confianza_promedio, 4),
        items_a_revisar=len({d.producto_id for d in detecciones_a_revisar}),
        tiempo_ahorrado_minutos=round(tiempo_ahorrado, 2),
    )


def porcentaje_auditorias_con_discrepancias(auditorias: list[dict]) -> float:
    if not auditorias:
        return 0
    con_discrepancias = sum(
        1
        for auditoria in auditorias
        if auditoria.get("metricas", {}).get("cantidad_discrepancias", 0) > 0
    )
    return round(con_discrepancias / len(auditorias) * 100, 2)

