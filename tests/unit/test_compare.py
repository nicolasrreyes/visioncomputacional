from app.detection.counting import contar_detecciones
from app.detection.mock_inference import cargar_detecciones_fixture
from app.inventory.compare import comparar_con_stock
from app.inventory.loader import cargar_productos, stock_por_zona
from app.inventory.schemas import EstadoOperativo


def test_compara_faltantes_y_ok():
    productos = cargar_productos()
    detecciones = cargar_detecciones_fixture("detecciones_estanteria_a.json")
    conteo = contar_detecciones(detecciones, productos)
    discrepancias = comparar_con_stock(
        stock_por_zona("estanteria_a"),
        conteo.conteos,
        conteo.detecciones_validas,
        conteo.detecciones_a_revisar,
    )
    por_producto = {item.producto_id: item for item in discrepancias}
    assert por_producto["caja_carton_chica"].estado_operativo == EstadoOperativo.OK
    assert por_producto["botella_plastica"].estado_operativo == EstadoOperativo.FALTANTE
    assert por_producto["botella_plastica"].diferencia == -1
    assert por_producto["lata_metalica"].diferencia == -6


def test_producto_no_esperado_detectado_es_sobrante():
    discrepancias = comparar_con_stock([], {"caja_carton_chica": 2})
    assert discrepancias[0].estado_operativo == EstadoOperativo.SOBRANTE
    assert discrepancias[0].cantidad_esperada == 0


def test_baja_confianza_queda_revisar():
    productos = cargar_productos()
    detecciones = cargar_detecciones_fixture("detecciones_con_baja_confianza.json")
    conteo = contar_detecciones(detecciones, productos)
    discrepancias = comparar_con_stock(
        stock_por_zona("estanteria_a"),
        conteo.conteos,
        conteo.detecciones_validas,
        conteo.detecciones_a_revisar,
    )
    por_producto = {item.producto_id: item for item in discrepancias}
    assert por_producto["caja_carton_chica"].estado_operativo == EstadoOperativo.REVISAR
    assert por_producto["caja_carton_chica"].requiere_revision is True

