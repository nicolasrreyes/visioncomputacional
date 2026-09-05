from app.audits.metrics import calcular_metricas, porcentaje_auditorias_con_discrepancias
from app.detection.counting import contar_detecciones
from app.detection.mock_inference import cargar_detecciones_fixture
from app.inventory.compare import comparar_con_stock
from app.inventory.loader import cargar_productos, stock_por_zona


def test_calcula_metricas_de_estanteria_a():
    conteo = contar_detecciones(cargar_detecciones_fixture("detecciones_estanteria_a.json"), cargar_productos())
    discrepancias = comparar_con_stock(
        stock_por_zona("estanteria_a"),
        conteo.conteos,
        conteo.detecciones_validas,
        conteo.detecciones_a_revisar,
    )
    metricas = calcular_metricas(discrepancias, conteo.detecciones_validas, conteo.detecciones_a_revisar, 3)
    assert metricas.total_esperado == 26
    assert metricas.total_detectado == 19
    assert metricas.diferencia_total == -7
    assert metricas.cantidad_discrepancias == 2
    assert metricas.items_a_revisar == 0


def test_metricas_sin_detecciones():
    conteo = contar_detecciones([], cargar_productos())
    discrepancias = comparar_con_stock(stock_por_zona("estanteria_a"), conteo.conteos)
    metricas = calcular_metricas(discrepancias, [], [], 1)
    assert metricas.total_detectado == 0
    assert metricas.confianza_promedio == 0
    assert metricas.porcentaje_coincidencia >= 0


def test_porcentaje_historico_discrepancias():
    auditorias = [
        {"metricas": {"cantidad_discrepancias": 0}},
        {"metricas": {"cantidad_discrepancias": 2}},
    ]
    assert porcentaje_auditorias_con_discrepancias(auditorias) == 50


def test_tiempo_ahorrado_nunca_negativo():
    from app.inventory.schemas import Deteccion

    # duracion enorme (> 26*0.25 min) -> el ahorro se clampa a 0
    metricas = calcular_metricas([], [], [], duracion_proceso_segundos=60 * 60)
    assert metricas.tiempo_ahorrado_minutos >= 0


def test_items_a_revisar_cuenta_productos_unicos():
    from app.inventory.schemas import Deteccion

    revisar = [
        Deteccion(producto_id="botella_plastica", label="a", confianza=0.2, bbox=[0, 0, 1, 1]),
        Deteccion(producto_id="botella_plastica", label="b", confianza=0.19, bbox=[1, 1, 2, 2]),
        Deteccion(producto_id="caja_carton_chica", label="c", confianza=0.3, bbox=[0, 0, 1, 1]),
    ]
    metricas = calcular_metricas([], [], revisar, 1)
    assert metricas.items_a_revisar == 2

