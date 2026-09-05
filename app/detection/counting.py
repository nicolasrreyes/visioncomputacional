from __future__ import annotations

from collections import defaultdict

from app.inventory.schemas import Deteccion, Producto, ResultadoConteo


DEFAULT_CONFIDENCE_THRESHOLD = 0.65
DEFAULT_SOLAPAMIENTO_MAXIMO = 0.7


def iou(caja_a: list[float], caja_b: list[float]) -> float:
    """Interseccion sobre union de dos bboxes [x1, y1, x2, y2]."""
    x1a, y1a, x2a, y2a = caja_a
    x1b, y1b, x2b, y2b = caja_b
    inter_x = max(0.0, min(x2a, x2b) - max(x1a, x1b))
    inter_y = max(0.0, min(y2a, y2b) - max(y1a, y1b))
    inter = inter_x * inter_y
    area_a = max(0.0, (x2a - x1a) * (y2a - y1a))
    area_b = max(0.0, (x2b - x1b) * (y2b - y1b))
    union = area_a + area_b - inter
    if union <= 0:
        return 0.0
    return inter / union


def supresion_no_maxima(
    detecciones: list[Deteccion],
    solapamiento_maximo: float = DEFAULT_SOLAPAMIENTO_MAXIMO,
) -> list[Deteccion]:
    """Deduplica detecciones solapadas (mismo objeto detectado varias veces).

    Greedy: ordena por confianza desc y conserva solo las cajas cuya maxima
    superposicion con las ya conservadas no supera `solapamiento_maximo` (IoU).
    Tambien resuelve confusiones entre productos: si dos cajas solapadas tienen
    productos distintos, gana la de mayor confianza.
    """
    if solapamiento_maximo <= 0:
        return detecciones
    ordenadas = sorted(detecciones, key=lambda d: d.confianza, reverse=True)
    conservadas: list[Deteccion] = []
    for deteccion in ordenadas:
        if any(iou(deteccion.bbox, otra.bbox) > solapamiento_maximo for otra in conservadas):
            continue
        conservadas.append(deteccion)
    return conservadas


def contar_detecciones(
    detecciones: list[Deteccion],
    productos: dict[str, Producto],
    default_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    solapamiento_maximo: float = DEFAULT_SOLAPAMIENTO_MAXIMO,
) -> ResultadoConteo:
    conteos: dict[str, int] = defaultdict(int)
    validas: list[Deteccion] = []
    revisar: list[Deteccion] = []

    for deteccion in supresion_no_maxima(detecciones, solapamiento_maximo):
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

