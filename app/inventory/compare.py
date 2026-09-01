from __future__ import annotations

from app.detection.counting import confianza_promedio_por_producto
from app.inventory.schemas import Deteccion, Discrepancia, EstadoOperativo, StockEsperado


def comparar_con_stock(
    stock_zona: list[StockEsperado],
    conteos: dict[str, int],
    detecciones_validas: list[Deteccion] | None = None,
    detecciones_a_revisar: list[Deteccion] | None = None,
) -> list[Discrepancia]:
    detecciones_validas = detecciones_validas or []
    detecciones_a_revisar = detecciones_a_revisar or []
    esperado = {item.producto_id: item.cantidad_esperada for item in stock_zona}
    productos = sorted(set(esperado) | set(conteos) | {d.producto_id for d in detecciones_a_revisar})
    confianza_por_producto = confianza_promedio_por_producto(detecciones_validas)
    productos_a_revisar = {d.producto_id for d in detecciones_a_revisar}

    discrepancias: list[Discrepancia] = []
    for producto_id in productos:
        cantidad_esperada = esperado.get(producto_id, 0)
        cantidad_detectada = conteos.get(producto_id, 0)
        diferencia = cantidad_detectada - cantidad_esperada
        requiere_revision = producto_id in productos_a_revisar

        if requiere_revision:
            estado = EstadoOperativo.REVISAR
        elif diferencia == 0:
            estado = EstadoOperativo.OK
        elif diferencia < 0:
            estado = EstadoOperativo.FALTANTE
        else:
            estado = EstadoOperativo.SOBRANTE

        discrepancias.append(
            Discrepancia(
                producto_id=producto_id,
                cantidad_esperada=cantidad_esperada,
                cantidad_detectada=cantidad_detectada,
                diferencia=diferencia,
                estado_operativo=estado,
                confianza_promedio=confianza_por_producto.get(producto_id, 0),
                requiere_revision=requiere_revision,
            )
        )
    return discrepancias

