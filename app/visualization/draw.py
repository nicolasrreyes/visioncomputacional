from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from app.inventory.schemas import Deteccion, Producto


def _color_hex_a_rgb(color: str | None) -> tuple[int, int, int]:
    if color and len(color) == 7 and color.startswith("#"):
        try:
            return tuple(int(color[i : i + 2], 16) for i in (1, 3, 5))
        except ValueError:
            pass
    return (0, 255, 0)


def _fuente(tamano: int = 16) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype("arial.ttf", tamano)
    except OSError:
        return ImageFont.load_default()


def _dibujar_en(imagen: Image.Image, detecciones: list[Deteccion], productos: dict[str, Producto]) -> Image.Image:
    draw = ImageDraw.Draw(imagen)
    fuente = _fuente()

    for deteccion in detecciones:
        producto = productos.get(deteccion.producto_id)
        color = _color_hex_a_rgb(producto.color_bbox if producto else None)
        x1, y1, x2, y2 = deteccion.bbox
        draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
        etiqueta = f"{deteccion.label} {deteccion.confianza:.0%}"
        fallo = draw.textbbox((x1, y1), etiqueta, font=fuente)
        draw.rectangle([fallo[0], fallo[1], fallo[2], fallo[3]], fill=color)
        draw.text((x1, y1), etiqueta, fill=(0, 0, 0), font=fuente)
    return imagen


def dibujar_bounding_boxes(
    imagen_ruta: str | Path,
    detecciones: list[Deteccion],
    productos: dict[str, Producto],
    salida: str | Path | None = None,
) -> Path:
    """Dibuja los bounding boxes sobre la imagen y guarda la evidencia anotada.

    Devuelve la ruta de la imagen generada.
    """
    imagen = Image.open(imagen_ruta)
    imagen = imagen.convert("RGB")
    _dibujar_en(imagen, detecciones, productos)

    ruta_salida = Path(salida) if salida else Path(imagen_ruta).with_suffix(".anotada.jpg")
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    imagen.save(ruta_salida, "JPEG", quality=90)
    return ruta_salida


def dibujar_sobre_array(
    imagen_rgb: Any,
    detecciones: list[Deteccion],
    productos: dict[str, Producto],
) -> Image.Image:
    """Dibuja los bounding boxes sobre un frame RGB en memoria (video en vivo)."""
    imagen = Image.fromarray(imagen_rgb)
    return _dibujar_en(imagen, detecciones, productos)