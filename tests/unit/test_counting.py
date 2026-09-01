from app.detection.counting import contar_detecciones
from app.detection.mock_inference import cargar_detecciones_fixture
from app.inventory.loader import cargar_productos
from app.inventory.schemas import Deteccion


def test_cuenta_detecciones_validas_por_producto():
    productos = cargar_productos()
    detecciones = cargar_detecciones_fixture("detecciones_estanteria_a.json")
    resultado = contar_detecciones(detecciones, productos)
    assert resultado.conteos["caja_carton_chica"] == 8
    assert resultado.conteos["botella_plastica"] == 11
    assert resultado.detecciones_a_revisar == []


def test_separa_detecciones_de_baja_confianza():
    productos = cargar_productos()
    detecciones = cargar_detecciones_fixture("detecciones_con_baja_confianza.json")
    resultado = contar_detecciones(detecciones, productos)
    assert resultado.conteos == {}
    assert len(resultado.detecciones_a_revisar) == 5


def test_lista_vacia_no_rompe():
    resultado = contar_detecciones([], cargar_productos())
    assert resultado.conteos == {}
    assert resultado.detecciones_validas == []
    assert resultado.detecciones_a_revisar == []


def test_confianza_igual_al_umbral_cuenta():
    deteccion = Deteccion(
        producto_id="caja_carton_chica",
        label="caja carton chica",
        confianza=0.65,
        bbox=[0, 0, 10, 10],
    )
    resultado = contar_detecciones([deteccion], cargar_productos())
    assert resultado.conteos["caja_carton_chica"] == 1

