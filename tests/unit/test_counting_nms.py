from __future__ import annotations

from app.detection.counting import iou, supresion_no_maxima
from app.inventory.schemas import Deteccion


def _deteccion(producto_id, confianza, bbox, label="x"):
    return Deteccion(producto_id=producto_id, label=label, confianza=confianza, bbox=bbox)


def test_iou_cajas_identicas_es_1():
    caja = [10, 10, 50, 50]
    assert iou(caja, caja) == 1.0


def test_iou_cajas_disjuntas_es_0():
    assert iou([10, 10, 20, 20], [30, 30, 40, 40]) == 0.0


def test_iou_solape_parcial():
    # 20x20 con 10x20 comunes: inter = 200, union = 600
    assert round(iou([0, 0, 20, 20], [10, 0, 30, 20]), 3) == round(200 / 600, 3)


def test_supresion_dedup_mismo_producto():
    detecciones = [
        _deteccion("caja_carton_chica", 0.90, [10, 10, 100, 100]),
        _deteccion("caja_carton_chica", 0.80, [15, 15, 105, 105]),
        _deteccion("caja_carton_chica", 0.70, [200, 200, 300, 300]),
    ]
    conservadas = supresion_no_maxima(detecciones)
    assert len(conservadas) == 2
    assert conservadas[0].confianza == 0.90
    assert conservadas[1].bbox == [200, 200, 300, 300]


def test_supresion_cross_producto_gana_mayor_confianza():
    detecciones = [
        _deteccion("botella_plastica", 0.92, [10, 10, 100, 200]),
        _deteccion("caja_carton_chica", 0.88, [20, 20, 110, 210]),
    ]
    conservadas = supresion_no_maxima(detecciones)
    assert len(conservadas) == 1
    assert conservadas[0].producto_id == "botella_plastica"


def test_supresion_plica_occlusion_parcial_densa():
    # Cajas adyacentes en estante denso: IoU bajo -> se conservan ambas
    a = _deteccion("botella_plastica", 0.9, [0, 0, 100, 400])
    b = _deteccion("botella_plastica", 0.8, [50, 0, 150, 400])
    # inter=20000, union=60000 -> IoU 0.333 (< 0.5)
    assert 0 < iou(a.bbox, b.bbox) <= 0.5
    assert len(supresion_no_maxima([a, b])) == 2


def test_supresion_desactivada_con_umbral_0():
    detecciones = [
        _deteccion("p", 0.9, [10, 10, 100, 100]),
        _deteccion("p", 0.8, [15, 15, 105, 105]),
    ]
    assert len(supresion_no_maxima(detecciones, solapamiento_maximo=0)) == 2


def test_contar_detecciones_usa_nms_antes_del_umbral():
    from app.detection.counting import contar_detecciones
    from app.inventory.schemas import Producto

    productos = {"caja_carton_chica": Producto(id="caja_carton_chica", nombre="Caja", prompts_deteccion=["box"], umbral_confianza=0.65)}
    detecciones = [
        _deteccion("caja_carton_chica", 0.90, [10, 10, 100, 100]),
        _deteccion("caja_carton_chica", 0.80, [15, 15, 105, 105]),
        _deteccion("caja_carton_chica", 0.70, [200, 200, 300, 300]),
    ]
    resultado = contar_detecciones(detecciones, productos)
    assert resultado.conteos == {"caja_carton_chica": 2}