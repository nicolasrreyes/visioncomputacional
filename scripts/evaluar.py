"""Harness de evaluacion de deteccion contra ground truth.

Dos modos segun el formato de `--etiquetas` (JSON por imagen):

  Bbox (mAP/P/R/F1 por IoU):
      {
        "foto.jpg": {"zona": "estanteria_b",
                     "cajas": {"botella_plastica": [[x1,y1,x2,y2], ...]}},
        ...
      }

  Conteo (comparacion de recuentos post-NMS; util sin anotar bboxes):
      {
        "foto.jpg": {"zona": "estanteria_b",
                     "conteos": {"botella_plastica": 41}},
        ...
      }

Uso:
    python scripts/evaluar.py --etiquetas data/evaluacion/etiquetas_conteo.json \\
        --dir data/demo_images --conf 0.1 [--sweep "0.2 0.3 0.4 0.5"]
        [--no-background] [--json outputs/evaluacion.json]

Reporta por producto P/R/F1 (y mAP en modo bbox), y en modo conteo el umbral
que maximiza F1 por producto (ligado a data/productos_objetivo.json).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.detection import eval as evaluacion
from app.detection.counting import contar_detecciones
from app.detection.real_inference import RealDetector, obtener_detector_compartido
from app.inventory.loader import cargar_productos, cargar_zonas, load_json


def _cargar_etiquetas(ruta: Path) -> dict:
    try:
        return load_json(ruta)
    except Exception as exc:
        raise SystemExit(f"No se pudo leer el archivo de etiquetas {ruta}: {exc}")


def _modo_imagen(etiqueta: dict) -> str:
    if "cajas" in etiqueta:
        return "bbox"
    if "conteos" in etiqueta:
        return "conteo"
    raise ValueError("La etiqueta debe tener 'cajas' (bbox) o 'conteos' (conteo).")


def _detectar_detecciones(detector, ruta: Path, zona_id, productos, con_background):
    zona = _zonas[zona_id]
    permitidos = zona.productos_permitidos or list(productos)
    prompts = {
        pid: productos[pid].prompts_deteccion for pid in permitidos if pid in productos
    }
    negativos = _background if con_background else None
    return detector.detectar(ruta, prompts, confianza=_conf, prompts_negativos=negativos)


def _filtrar_stock(conteos: dict[str, int], zona_id: str) -> dict[str, int]:
    permitidos = set(_zonas[zona_id].productos_permitidos or [])
    return {k: v for k, v in conteos.items() if not permitidos or k in permitidos}


def _mostrar_tabla_conteo(resultado: dict) -> None:
    por_producto = resultado["por_producto"]
    ancho = max(len(p) for p in por_producto) if por_producto else 10
    print(f"  {'producto':<{ancho}}  esperado  detectado  TP  FP  FN   P     R     F1")
    for producto_id, fila in sorted(por_producto.items()):
        print(
            f"  {producto_id:<{ancho}}  {fila['esperado']:>7}  {fila['detectado']:>8}  "
            f"{fila['tp']:>2}  {fila['fp']:>2}  {fila['fn']:>2}   "
            f"{fila['precision']:>5.2f}  {fila['recall']:>5.2f}  {fila['f1']:>5.2f}"
        )
    g = resultado["global"]
    print(
        f"  {'TOTAL':<{ancho}}  {'':>15}  {'':>3}  {'':>2}  {'':>2}"
        f"   {g['precision']:>5.2f}  {g['recall']:>5.2f}  {g['f1']:>5.2f}"
        f"   (coincidencia {g['porcentaje_coincidencia']}%)"
    )


def _mostrar_tabla_bbox(resultado: dict) -> None:
    por_producto = resultado["por_producto"]
    ancho = max(len(p) for p in por_producto) if por_producto else 10
    print(f"  {'producto':<{ancho}}  TP  FP  FN   P     R     F1    AP")
    for producto_id, fila in sorted(por_producto.items()):
        print(
            f"  {producto_id:<{ancho}}  {fila['tp']:>2}  {fila['fp']:>2}  {fila['fn']:>2}   "
            f"{fila['precision']:>5.2f}  {fila['recall']:>5.2f}  {fila['f1']:>5.2f}  {fila['ap']:>5.3f}"
        )
    print(f"  mAP@0.5: {resultado['mAP']:.3f}")


def _sweep_umbrales(detecciones_por_imagen, gt_por_imagen):
    """Modo conteo: umbral optimo por F1 para cada producto.

    Mantiene el NMS global (todos los productos, como en produccion) y solo
    varia el umbral del producto evaluado.
    """
    umbrales = sorted(_sweep)
    productos = cargar_productos()
    mejores: dict[str, dict] = {}
    for producto_id in productos:
        gts_acumuladas = sum(
            (gt["conteos"].get(producto_id, 0) for gt in gt_por_imagen.values())
        )
        if gts_acumuladas <= 0:
            continue
        mejor: tuple[float, dict] | None = None
        for umbral in umbrales:
            productos_mod = {
                pid: (p.model_copy(update={"umbral_confianza": umbral}) if pid == producto_id else p)
                for pid, p in productos.items()
            }
            total_detectado = 0
            for detalle in detecciones_por_imagen.values():
                res = contar_detecciones(
                    detalle["detecciones"], productos_mod, solapamiento_maximo=_nms
                )
                total_detectado += res.conteos.get(producto_id, 0)
            f1 = evaluacion.metrics_conteo(
                {producto_id: total_detectado}, {producto_id: gts_acumuladas}
            )["global"]["f1"]
            if mejor is None or f1 > mejor[0]:
                mejor = (
                    f1,
                    {
                        "umbral": umbral,
                        "f1": f1,
                        "detectado": total_detectado,
                        "esperado": gts_acumuladas,
                    },
                )
        if mejor:
            mejores[producto_id] = mejor[1]
    return mejores


def main() -> int:
    parser = argparse.ArgumentParser(description="Evalua deteccion contra ground truth")
    parser.add_argument("--etiquetas", required=True, help="JSON con ground truth por imagen")
    parser.add_argument("--dir", default=str(PROJECT_ROOT / "data" / "demo_images"), help="Directorio de imagenes")
    parser.add_argument("--conf", type=float, default=0.1, help="Confianza cruda de inferencia")
    parser.add_argument("--iou", type=float, default=0.5, help="Umbral IoU para emparejar (modo bbox)")
    parser.add_argument("--nms", type=float, default=0.7, help="IoU NMS para el conteo (modo conteo)")
    parser.add_argument("--sweep", default=None, help="Umbrales a barrer (modo conteo), ej '0.2 0.3 0.4 0.5'")
    parser.add_argument("--no-background", action="store_true", help="No usar prompts background del config")
    parser.add_argument("--json", default=None, help="Ruta opcional para guardar el reporte completo")
    args = parser.parse_args()

    global _conf, _nms, _sweep, _zonas, _background
    _conf = args.conf
    _nms = args.nms
    _sweep = [float(x) for x in args.sweep.split()] if args.sweep else []
    con_background = not args.no_background

    productos = cargar_productos()
    _zonas = cargar_zonas()
    _background = _cargar_background()

    etiquetas = _cargar_etiquetas(Path(args.etiquetas))
    directorio = Path(args.dir)
    if not etiquetas:
        print("El archivo de etiquetas esta vacio.")
        return 1

    directorio_imagenes = {p.name: p for p in sorted(directorio.glob("*.jpg"))}
    faltantes = [nombre for nombre in etiquetas if nombre not in directorio_imagenes]
    if faltantes:
        print(f"Faltan imagenes del directorio: {faltantes}")
        return 1

    detector: RealDetector = obtener_detector_compartido()
    detecciones_por_imagen: dict[str, dict] = {}
    gt_por_imagen: dict[str, dict] = {}
    for nombre, etiqueta in etiquetas.items():
        zona_id = etiqueta["zona"]
        detecciones = _detectar_detecciones(
            detector, directorio_imagenes[nombre], zona_id, productos, con_background
        )
        detecciones_por_imagen[nombre] = {"zona": zona_id, "detecciones": detecciones}
        gt_por_imagen[nombre] = etiqueta

    modos = {_modo_imagen(e) for e in etiquetas.values()}
    if len(modos) > 1:
        print("Mezclar modos bbox y conteo en un mismo set no esta soportado.")
        return 1
    modo = modos.pop()

    if modo == "bbox":
        print(f"Modo bbox: {len(etiquetas)} imagen(es), IoU >= {args.iou}, conf >= {args.conf}.")
        producto_ids = sorted(
            {pid for e in etiquetas.values() for pid in (e.get("cajas") or {})}
        )
        cajas_gt: dict[str, dict[str, list[list[float]]]] = {}
        acumulado_det: dict[str, list] = {pid: [] for pid in producto_ids}
        for nombre, detalle in detecciones_por_imagen.items():
            cajas_gt[nombre] = etiquetas[nombre]["cajas"]
            for d in detalle["detecciones"]:
                if d.producto_id in acumulado_det:
                    acumulado_det[d.producto_id].append(d)
        resultado = evaluacion.metrics_bbox(
            [d for lista in acumulado_det.values() for d in lista],
            {pid: [caja for e in cajas_gt.values() for caja in e.get(pid, [])] for pid in producto_ids},
            producto_ids,
            iou_umbral=args.iou,
            conf_umbral=args.conf,
        )
        _mostrar_tabla_bbox(resultado)
    else:
        print(f"Modo conteo: {len(etiquetas)} imagen(es), NMS {args.nms}, conf cruda {args.conf}.")
        conteos_gt: dict[str, int] = {}
        conteos_detectados: dict[str, int] = {}
        for nombre, detalle in detecciones_por_imagen.items():
            zona_id = detalle["zona"]
            resultado = contar_detecciones(
                detalle["detecciones"], productos, solapamiento_maximo=_nms
            )
            detecciones_validas = _filtrar_stock(resultado.conteos, zona_id)
            for pid, cant in detecciones_validas.items():
                conteos_detectados[pid] = conteos_detectados.get(pid, 0) + cant
            for pid, cant in _filtrar_stock(gt_por_imagen[nombre]["conteos"], zona_id).items():
                conteos_gt[pid] = conteos_gt.get(pid, 0) + cant
        resultado = evaluacion.metrics_conteo(conteos_detectados, conteos_gt)
        _mostrar_tabla_conteo(resultado)
        if _sweep:
            print(f"\nSweep de umbral ({', '.join(f'{u:.2f}' for u in sorted(_sweep))}):")
            mejores = _sweep_umbrales(detecciones_por_imagen, gt_por_imagen)
            for producto_id, info in sorted(mejores.items()):
                print(
                    f"  {producto_id:<24} mejor F1={info['f1']:.3f} con umbral "
                    f"{info['umbral']:.2f} (esperado {info['esperado']}, detectado {info['detectado']})"
                )

    if args.json:
        salida = {"modo": modo, **resultado}
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(json.dumps(salida, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nReporte guardado en {args.json}")
    return 0


def _cargar_background() -> list[str]:
    data = load_json(PROJECT_ROOT / "data" / "productos_objetivo.json")
    return list(data.get("prompts_background", []))


if __name__ == "__main__":
    sys.exit(main())