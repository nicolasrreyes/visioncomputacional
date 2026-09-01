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

