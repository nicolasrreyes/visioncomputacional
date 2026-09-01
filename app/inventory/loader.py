from __future__ import annotations

import csv
import json
from pathlib import Path

from app.inventory.schemas import Producto, StockEsperado, Zona


ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
FIXTURES_DIR = ROOT_DIR / "tests" / "fixtures"


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8-sig") as file:
        return json.load(file)


def cargar_productos(path: Path | None = None) -> dict[str, Producto]:
    data = load_json(path or DATA_DIR / "productos_objetivo.json")
    productos = {}
    for raw in data.get("productos_objetivo", []):
        producto = Producto(**raw)
        productos[producto.id] = producto
    if not productos:
        raise ValueError("No hay productos objetivo definidos.")
    return productos


def cargar_zonas(path: Path | None = None) -> dict[str, Zona]:
    data = load_json(path or DATA_DIR / "zonas.json")
    zonas = {}
    for raw in data.get("zonas", []):
        zona = Zona(**raw)
        zonas[zona.id] = zona
    if not zonas:
        raise ValueError("No hay zonas definidas.")
    return zonas


def cargar_stock(path: Path | None = None) -> list[StockEsperado]:
    stock_path = path or DATA_DIR / "stock_esperado.csv"
    registros: list[StockEsperado] = []
    with stock_path.open("r", encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            row["cantidad_esperada"] = int(row["cantidad_esperada"])
            registros.append(StockEsperado(**row))
    if not registros:
        raise ValueError("El stock esperado esta vacio.")
    return registros


def stock_por_zona(zona_id: str, stock: list[StockEsperado] | None = None) -> list[StockEsperado]:
    registros = stock if stock is not None else cargar_stock()
    return [item for item in registros if item.zona_id == zona_id]


def stock_por_producto(zona_id: str, stock: list[StockEsperado] | None = None) -> dict[str, int]:
    return {item.producto_id: item.cantidad_esperada for item in stock_por_zona(zona_id, stock)}


def validar_datos_base(
    productos: dict[str, Producto] | None = None,
    zonas: dict[str, Zona] | None = None,
    stock: list[StockEsperado] | None = None,
) -> None:
    productos = productos or cargar_productos()
    zonas = zonas or cargar_zonas()
    stock = stock or cargar_stock()

    for item in stock:
        if item.producto_id not in productos:
            raise ValueError(f"Producto desconocido en stock: {item.producto_id}")
        if item.zona_id not in zonas:
            raise ValueError(f"Zona desconocida en stock: {item.zona_id}")
        permitidos = zonas[item.zona_id].productos_permitidos
        if permitidos and item.producto_id not in permitidos:
            raise ValueError(f"Producto {item.producto_id} no permitido en zona {item.zona_id}")

