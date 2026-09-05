"""Validador de deteccion real sobre imagenes demo.

Uso:
    python scripts/validar_deteccion.py [--imagen RUTA [RUTA ...]] [--conf 0.25]
        [--zona estanteria_a] [--max-confs 15]

Imprime por imagen: detecciones crudas, validas por umbral, tras NMS y -si se
pasa una zona- el conteo comparado contra el stock esperado. Sirve de base
objetiva para afinar prompts, umbrales y narrativa de la demo.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.detection.counting import contar_detecciones
from app.detection.real_inference import RealDetector
from app.inventory.loader import (
    cargar_productos,
    cargar_stock,
    cargar_zonas,
    stock_por_producto,
)


def _resumen(detecciones, productos, umbrales_nms):
    conteos_validos = {}
    conteos_nms = {t: {} for t in umbrales_nms}
    lista_conf = {}
    for producto_id in productos:
        dets = [d for d in detecciones if d.producto_id == producto_id]
        conteos_validos[producto_id] = len(dets)
        lista_conf[producto_id] = sorted((d.confianza for d in dets), reverse=True)
    for umbral in umbrales_nms:
        resultado = contar_detecciones(detecciones, productos, solapamiento_maximo=umbral)
        for producto_id in productos:
            conteos_nms[umbral][producto_id] = resultado.conteos.get(producto_id, 0)
    return conteos_validos, conteos_nms, lista_conf


def _comparar_stock(conteos: dict[str, int], zona_id: str, stock_por_zona: dict[str, int]) -> None:
    print(f"\n  vs stock zona {zona_id}:")
    for producto_id, esperado in sorted(stock_por_zona.items()):
        detectado = conteos.get(producto_id, 0)
        marca = "OK" if detectado == esperado else ("falta" if detectado < esperado else "sobra")
        print(f"    {producto_id:<22} esperado={esperado:>3} detectado={detectado:>3}  {marca}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Valida deteccion real sobre imagenes demo")
    parser.add_argument(
        "--imagen", nargs="+", default=None, help="Rutas de imagenes (por defecto data/demo_images/*.jpg)"
    )
    parser.add_argument("--conf", type=float, default=0.25, help="Confianza minima cruda del modelo")
    parser.add_argument("--zona", default=None, help="Zona para comparar conteos contra stock")
    parser.add_argument("--max-confs", type=int, default=15, help="Cuantas confianzas mostrar por producto")
    parser.add_argument(
        "--nms", nargs="+", type=float, default=[0.5, 0.6, 0.7, 0.8],
        help="Umbrales IoU NMS a evaluar",
    )
    args = parser.parse_args()

    productos = cargar_productos()
    umbrales_nms = sorted(args.nms)
    if args.imagen:
        imagenes = [Path(p) for p in args.imagen]
    else:
        imagenes = sorted((PROJECT_ROOT / "data" / "demo_images").glob("*.jpg"))
    if not imagenes:
        print("No hay imagenes para validar.")
        return 1

    stock_por_zona_ctx = stock_por_producto(args.zona) if args.zona else None

    detector = RealDetector()
    prompts = {pid: list(p.prompts_deteccion) for pid, p in productos.items()}

    print(f"Evaluando {len(imagenes)} imagen(es) con {len(productos)} producto(s).")
    for ruta in imagenes:
        print(f"\n=== {ruta.name} ===")
        detecciones = detector.detectar(ruta, prompts, confianza=args.conf)
        validos, tras_nms, confs = _resumen(detecciones, productos, umbrales_nms)
        ancho_col = max(len(p.id) for p in productos.values())
        cabezas = "  ".join(f"NMS{t:.1f}" for t in umbrales_nms)
        print(f"  {'producto':<{ancho_col}}  crudos  validas  {cabezas}   confianzas (ordenadas)")
        for producto_id in sorted(productos):
            col_ancho = f"{producto_id:<{ancho_col}}"
            lista = confs[producto_id][: args.max_confs]
            conf_txt = " ".join(f"{c:.2f}" for c in lista) or "-"
            nms_txt = "  ".join(f"{tras_nms[t][producto_id]:>3}" for t in umbrales_nms)
            print(
                f"  {col_ancho}  {len([d for d in detecciones if d.producto_id == producto_id]):>5}  "
                f"{validos[producto_id]:>6}  {nms_txt}   {conf_txt}"
            )
        if args.zona:
            _comparar_stock(tras_nms[umbrales_nms[0]], args.zona, stock_por_zona_ctx)
    return 0


if __name__ == "__main__":
    sys.exit(main())