from app.detection import eval as evaluacion
from app.inventory.schemas import Deteccion


def _det(producto_id, conf, bbox):
    return Deteccion(producto_id=producto_id, label="x", confianza=conf, bbox=bbox)


def test_emparejar_casos_ideales():
    dets = [_det("a", 0.9, [0, 0, 10, 10]), _det("a", 0.8, [50, 50, 60, 60])]
    gt = [[0, 0, 10, 10], [50, 50, 60, 60]]
    assert evaluacion.emparejar(dets, gt, iou_umbral=0.5) == (2, 0, 0)


def test_emparejar_falsos_positivos_y_negativos():
    dets = [_det("a", 0.9, [0, 0, 10, 10]), _det("a", 0.7, [100, 100, 110, 110])]
    gt = [[0, 0, 10, 10]]
    assert evaluacion.emparejar(dets, gt, iou_umbral=0.5) == (1, 1, 0)
    assert evaluacion.emparejar([], gt, iou_umbral=0.5) == (0, 0, 1)


def test_emparejar_duplicado_solapado_cuenta_una_vez():
    dets = [_det("a", 0.9, [0, 0, 10, 10]), _det("a", 0.6, [1, 1, 11, 11])]
    gt = [[0, 0, 10, 10]]
    assert evaluacion.emparejar(dets, gt, iou_umbral=0.5) == (1, 1, 0)


def test_emparejar_filtra_por_confianza():
    dets = [_det("a", 0.4, [0, 0, 10, 10]), _det("a", 0.3, [50, 50, 60, 60])]
    gt = [[0, 0, 10, 10]]
    assert evaluacion.emparejar(dets, gt, iou_umbral=0.5, conf_umbral=0.5) == (0, 0, 1)


def test_precision_recall_f1():
    assert evaluacion.precision_recall_f1(2, 1, 1) == (0.6667, 0.6667, 0.6667)


def test_curva_pr_y_average_precision():
    dets = [_det("a", 0.9, [0, 0, 10, 10])]
    gt = [[0, 0, 10, 10]]
    curva = evaluacion.curva_pr(dets, gt)
    assert curva == [(1.0, 1.0)]
    assert evaluacion.average_precision(curva) == 1.0


def test_average_precision_vacio():
    assert evaluacion.average_precision([]) == 0.0


def test_metrics_bbox_mapa():
    dets = [
        _det("a", 0.95, [0, 0, 10, 10]),
        _det("b", 0.9, [20, 20, 30, 30]),
        _det("a", 0.8, [100, 100, 110, 110]),
    ]
    gt = {"a": [[0, 0, 10, 10]], "b": [[20, 20, 30, 30]]}
    resultado = evaluacion.metrics_bbox(dets, gt, ["a", "b"], iou_umbral=0.5, conf_umbral=0.5)
    assert resultado["mAP"] == 1.0
    assert resultado["por_producto"]["a"] == {
        "tp": 1, "fp": 1, "fn": 0,
        "precision": 0.5, "recall": 1.0, "f1": 0.6667, "ap": 1.0,
    }


def test_metrics_conteo_sin_discrepancias():
    resultado = evaluacion.metrics_conteo({"a": 3, "b": 1}, {"a": 3, "b": 1})
    assert resultado["global"] == {
        "tp": 4, "fp": 0, "fn": 0,
        "precision": 1.0, "recall": 1.0, "f1": 1.0, "porcentaje_coincidencia": 100.0,
    }


def test_metrics_conteo_con_faltantes_y_sobrantes():
    resultado = evaluacion.metrics_conteo({"a": 2, "b": 5}, {"a": 3, "b": 4})
    fila_a = resultado["por_producto"]["a"]
    fila_b = resultado["por_producto"]["b"]
    assert (fila_a["tp"], fila_a["fp"], fila_a["fn"]) == (2, 0, 1)
    assert (fila_b["tp"], fila_b["fp"], fila_b["fn"]) == (4, 1, 0)
    g = resultado["global"]
    assert (g["tp"], g["fp"], g["fn"]) == (6, 1, 1)
    assert g["porcentaje_coincidencia"] == round(100.0 * 6 / 7, 2)