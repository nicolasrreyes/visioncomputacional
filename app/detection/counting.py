from __future__ import annotations

from collections import defaultdict

from app.inventory.schemas import Deteccion, Producto, ResultadoConteo


DEFAULT_CONFIDENCE_THRESHOLD = 0.65


def contar_detecciones(
    detecciones: list[Deteccion],
    productos: dict[str, Producto],
    default_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
) -> ResultadoConteo:
    conteos: dict[str, int] = defaultdict(int)
    validas: list[Deteccion] = []
    revisar: list[Deteccion] = []

    for deteccion in detecciones:
        producto = productos.get(deteccion.producto_id)
        threshold = producto.umbral_confianza if producto else default_threshold
        if deteccion.confianza >= threshold:
            conteos[deteccion.producto_id] += 1
            validas.append(deteccion)
        else:
            revisar.append(deteccion)

    return ResultadoConteo(
        conteos=dict(conteos),
        detecciones_validas=validas,
        detecciones_a_revisar=revisar,
    )


def confianza_promedio_por_producto(detecciones: list[Deteccion]) -> dict[str, float]:
    acumulado: dict[str, list[float]] = defaultdict(list)
    for deteccion in detecciones:
        acumulado[deteccion.producto_id].append(deteccion.confianza)
    return {
        producto_id: round(sum(valores) / len(valores), 4)
        for producto_id, valores in acumulado.items()
        if valores
    }

