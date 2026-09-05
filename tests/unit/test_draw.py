from PIL import Image

from app.inventory.loader import cargar_productos
from app.inventory.schemas import Deteccion
from app.visualization.draw import dibujar_bounding_boxes, dibujar_sobre_array


def _imagen_prueba(tmp_path):
    ruta = tmp_path / "original.jpg"
    Image.new("RGB", (200, 200), (255, 255, 255)).save(ruta)
    return ruta


def test_dibuja_bounding_boxes_y_guarda_evidencia(tmp_path):
    ruta = _imagen_prueba(tmp_path)
    salida = tmp_path / "anotada.jpg"
    detecciones = [
        Deteccion(producto_id="caja_carton_chica", label="caja", confianza=0.9, bbox=[10, 10, 80, 80])
    ]
    resultado = dibujar_bounding_boxes(ruta, detecciones, cargar_productos(), salida=salida)
    assert resultado == salida
    assert salida.exists()
    with Image.open(salida) as imagen:
        assert imagen.size == (200, 200)


def test_acepta_detecciones_vacias(tmp_path):
    ruta = _imagen_prueba(tmp_path)
    salida = tmp_path / "sin_detecciones.jpg"
    resultado = dibujar_bounding_boxes(ruta, [], cargar_productos(), salida=salida)
    assert resultado == salida
    assert salida.exists()


def test_dibujar_sobre_array_aplica_color_del_producto():
    import numpy as np

    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    detecciones = [
        Deteccion(producto_id="caja_carton_chica", label="caja", confianza=0.9, bbox=[10, 10, 15, 15])
    ]
    imagen = dibujar_sobre_array(frame, detecciones, cargar_productos())
    assert imagen.size == (100, 100)
    # caja_carton_chica -> #FF6B6B (rojizo) en el borde del rectangulo
    r, g, b = imagen.getpixel((10, 10))
    assert r > 200 and g < 150 and b < 150


def test_dibujar_sobre_array_producto_desconocido_us_a_verde():
    import numpy as np

    frame = np.zeros((50, 50, 3), dtype=np.uint8)
    detecciones = [
        Deteccion(producto_id="sin_stock", label="cosa rara", confianza=0.5, bbox=[2, 2, 8, 8])
    ]
    imagen = dibujar_sobre_array(frame, detecciones, cargar_productos())
    r, g, b = imagen.getpixel((2, 2))
    assert g > 200 and r < 150