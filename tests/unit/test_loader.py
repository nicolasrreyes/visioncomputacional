from app.inventory.loader import cargar_productos, cargar_stock, cargar_zonas, stock_por_zona


def test_cargar_productos():
    productos = cargar_productos()
    assert "caja_carton_chica" in productos
    assert productos["caja_carton_chica"].umbral_confianza == 0.6


def test_cargar_zonas():
    zonas = cargar_zonas()
    assert "estanteria_a" in zonas
    assert "botella_plastica" in zonas["estanteria_a"].productos_permitidos


def test_cargar_stock():
    stock = cargar_stock()
    assert len(stock) >= 9
    assert all(item.cantidad_esperada >= 0 for item in stock)


def test_stock_por_zona():
    stock = stock_por_zona("estanteria_a")
    cantidades = {item.producto_id: item.cantidad_esperada for item in stock}
    assert cantidades["caja_carton_chica"] == 8
    assert cantidades["botella_plastica"] == 12


def test_stock_por_zona_b_solo_botellas():
    stock = stock_por_zona("estanteria_b")
    cantidades = {item.producto_id: item.cantidad_esperada for item in stock}
    assert cantidades == {"botella_plastica": 40}

