from __future__ import annotations

from typing import Iterable

from app.detection.counting import iou
from app.inventory.schemas import Deteccion


def emparejar(
    detecciones: list[Deteccion],
    cajas_gt: list[list[float]],
    iou_umbral: float = 0.5,
    conf_umbral: float = 0.0,
) -> tuple[int, int, int]:
    """Cuenta TP/FP/FN de un producto contra sus cajas ground truth.

    Greedy: procesa las detecciones de mayor a menor confianza y asigna cada
    caja GT a lo sumo una vez (emparejamiento IoU >= iou_umbral).
    """
    dets = sorted(
        (d for d in detecciones if d.confianza >= conf_umbral),
        key=lambda d: d.confianza,
        reverse=True,
    )
    casadas = set()
    tp = 0
    for det in dets:
        mejor_iou, mejor_indice = 0.0, -1
        for pos, gt in enumerate(cajas_gt):
            if pos in casadas:
                continue
            solape = iou(det.bbox, gt)
            if solape > mejor_iou:
                mejor_iou, mejor_indice = solape, pos
        if mejor_indice >= 0 and mejor_iou >= iou_umbral:
            tp += 1
            casadas.add(mejor_indice)
    fp = len(dets) - tp
    fn = len(cajas_gt) - tp
    return tp, fp, fn


def precision_recall_f1(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return round(precision, 4), round(recall, 4), round(f1, 4)


def curva_pr(
    detecciones: list[Deteccion],
    cajas_gt: list[list[float]],
    iou_umbral: float = 0.5,
) -> list[tuple[float, float]]:
    """Curva Precision-Recall (un punto por deteccion, por confianza desc)."""
    if not cajas_gt:
        return []
    ordenadas = sorted(detecciones, key=lambda d: d.confianza, reverse=True)
    casadas = set()
    tp, fp = 0, 0
    puntos: list[tuple[float, float]] = []
    for det in ordenadas:
        mejor_iou, mejor_indice = 0.0, -1
        for pos, gt in enumerate(cajas_gt):
            if pos in casadas:
                continue
            solape = iou(det.bbox, gt)
            if solape > mejor_iou:
                mejor_iou, mejor_indice = solape, pos
        if mejor_indice >= 0 and mejor_iou >= iou_umbral:
            tp += 1
            casadas.add(mejor_indice)
        else:
            fp += 1
        recall = tp / len(cajas_gt)
        precision = tp / (tp + fp) if tp + fp else 0.0
        puntos.append((round(recall, 4), round(precision, 4)))
    return puntos


def average_precision(puntos: list[tuple[float, float]]) -> float:
    """AP 11-point (PASCAL VOC): max precision para recall >= r, r in 0..1 paso 0.1."""
    if not puntos:
        return 0.0
    ap = 0.0
    for nivel in range(11):
        r_objetivo = nivel / 10.0
        max_precision = max(
            (p for r, p in puntos if r >= r_objetivo),
            default=0.0,
        )
        ap += max_precision
    return round(ap / 11.0, 4)


def metrics_bbox(
    detecciones: list[Deteccion],
    cajas_gt: dict[str, list[list[float]]],
    producto_ids: Iterable[str],
    iou_umbral: float = 0.5,
    conf_umbral: float = 0.0,
) -> dict[str, dict]:
    """Metricas bbox por producto y mAP: P, R, F1, TP/FP/FN + AP."""
    por_producto: dict[str, dict] = {}
    aps: list[float] = []
    for producto_id in producto_ids:
        dets = [d for d in detecciones if d.producto_id == producto_id]
        gts = list(cajas_gt.get(producto_id, []))
        tp, fp, fn = emparejar(dets, gts, iou_umbral=iou_umbral, conf_umbral=conf_umbral)
        precision, recall, f1 = precision_recall_f1(tp, fp, fn)
        ap = average_precision(curva_pr(dets, gts, iou_umbral=iou_umbral))
        aps.append(ap)
        por_producto[producto_id] = {
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "ap": ap,
        }
    mapa = round(sum(aps) / len(aps), 4) if aps else 0.0
    return {"por_producto": por_producto, "mAP": mapa}


def metrics_conteo(
    conteos_detectados: dict[str, int],
    conteos_gt: dict[str, int],
) -> dict:
    """Compara conteos (post-NMS + umbral de config) contra un recuento GT.

    TP = min(detectado, esperado); FP = sobrante; FN = faltante (por producto).
    Incluye F1 global ponderado por unidades esperadas.
    """
    productos = sorted(set(conteos_detectados) | set(conteos_gt))
    por_producto: dict[str, dict] = {}
    tp_total = fp_total = fn_total = 0
    for producto_id in productos:
        detectado = conteos_detectados.get(producto_id, 0)
        esperado = conteos_gt.get(producto_id, 0)
        tp = min(detectado, esperado)
        fp = detectado - tp
        fn = esperado - tp
        tp_total += tp
        fp_total += fp
        fn_total += fn
        precision, recall, f1 = precision_recall_f1(tp, fp, fn)
        por_producto[producto_id] = {
            "esperado": esperado,
            "detectado": detectado,
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }
    precision, recall, f1 = precision_recall_f1(tp_total, fp_total, fn_total)
    filas = list(por_producto.values())
    coincidencia = (
        round(100.0 * tp_total / max(1, sum(r["esperado"] for r in filas)), 2)
        if filas
        else 0.0
    )
    return {
        "por_producto": por_producto,
        "global": {
            "tp": tp_total,
            "fp": fp_total,
            "fn": fn_total,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "porcentaje_coincidencia": coincidencia,
        },
    }