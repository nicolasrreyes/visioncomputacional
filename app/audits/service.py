from __future__ import annotations

import shutil
import time
from pathlib import Path

from app.audits.metrics import calcular_metricas
from app.audits.repository import AuditoriaRepository
from app.detection.counting import contar_detecciones
from app.detection.mock_inference import cargar_detecciones_fixture
from app.detection.real_inference import RealDetector, obtener_detector_compartido
from app.inventory.compare import comparar_con_stock
from app.inventory.loader import (
    DATA_DIR,
    ROOT_DIR,
    cargar_productos,
    cargar_zonas,
    load_json,
    stock_por_zona,
)
from app.inventory.schemas import Auditoria, Deteccion, FuenteAuditoria
from app.visualization.draw import dibujar_bounding_boxes, dibujar_sobre_array


INPUTS_DIR = ROOT_DIR / "inputs"
EVIDENCIA_DIR = ROOT_DIR / "outputs" / "evidencia"


def _armar_y_guardar(
    zona_id: str,
    fuente: FuenteAuditoria,
    detecciones: list[Deteccion],
    duracion_proceso_segundos: float,
    repository: AuditoriaRepository,
    archivo_original: str | None = None,
    evidencia_path: str | None = None,
    auditoria_id: str | None = None,
) -> Auditoria:
    zonas = cargar_zonas()
    if zona_id not in zonas:
        raise ValueError(f"Zona desconocida: {zona_id}")

    productos = cargar_productos()
    resultado_conteo = contar_detecciones(detecciones, productos)
    stock_zona = stock_por_zona(zona_id)
    discrepancias = comparar_con_stock(
        stock_zona=stock_zona,
        conteos=resultado_conteo.conteos,
        detecciones_validas=resultado_conteo.detecciones_validas,
        detecciones_a_revisar=resultado_conteo.detecciones_a_revisar,
    )
    metricas = calcular_metricas(
        discrepancias=discrepancias,
        detecciones_validas=resultado_conteo.detecciones_validas,
        detecciones_a_revisar=resultado_conteo.detecciones_a_revisar,
        duracion_proceso_segundos=duracion_proceso_segundos,
    )
    auditoria = Auditoria.nueva(
        auditoria_id=auditoria_id or repository.siguiente_id(),
        zona_id=zona_id,
        fuente=fuente,
        duracion_proceso_segundos=round(duracion_proceso_segundos, 4),
        detecciones=detecciones,
        conteos=resultado_conteo.conteos,
        discrepancias=discrepancias,
        metricas=metricas,
        archivo_original=archivo_original,
        evidencia_path=evidencia_path,
    )
    repository.guardar(auditoria)
    return auditoria


def simular_auditoria(
    zona_id: str,
    fixture: str,
    fuente: FuenteAuditoria = FuenteAuditoria.IMAGEN,
    repository: AuditoriaRepository | None = None,
) -> Auditoria:
    inicio = time.perf_counter()
    detecciones = cargar_detecciones_fixture(fixture)
    duracion = time.perf_counter() - inicio
    return _armar_y_guardar(
        zona_id=zona_id,
        fuente=fuente,
        detecciones=detecciones,
        duracion_proceso_segundos=duracion,
        repository=repository or AuditoriaRepository(),
    )


def _prompts_por_producto(zona_id: str) -> dict[str, list[str]]:
    zonas = cargar_zonas()
    if zona_id not in zonas:
        raise ValueError(f"Zona desconocida: {zona_id}")
    productos = cargar_productos()
    permitidos = zonas[zona_id].productos_permitidos or list(productos)
    return {
        producto_id: productos[producto_id].prompts_deteccion
        for producto_id in permitidos
        if producto_id in productos
    }


def _prompts_background() -> list[str]:
    data = load_json(DATA_DIR / "productos_objetivo.json")
    return list(data.get("prompts_background", []))


def build_prompts_con_background(
    zona_id: str, con_background: bool = True
) -> tuple[dict[str, list[str]], list[str]]:
    """Prompts de la zona + clases negativas de background.

    Las negativas entran al softmax del modelo (suben precision) pero el
    detector las filtra del output.
    """
    prompts = _prompts_por_producto(zona_id)
    negativos = _prompts_background() if con_background else []
    return prompts, negativos


def procesar_imagen(
    zona_id: str,
    ruta_imagen: str | Path,
    fuente: FuenteAuditoria = FuenteAuditoria.IMAGEN,
    detector: RealDetector | None = None,
    repository: AuditoriaRepository | None = None,
    inputs_dir: Path | None = None,
    evidencia_dir: Path | None = None,
) -> Auditoria:
    """Flujo con deteccion real: imagen -> detecciones -> auditoria guardada.

    Guarda la imagen original en inputs/ y la evidencia anotada en
    outputs/evidencia/, dejando rutas relativas compatibles con el schema.
    """
    inicio = time.perf_counter()
    ruta = Path(ruta_imagen)
    if not ruta.exists():
        raise FileNotFoundError(f"No existe la imagen: {ruta_imagen}")

    prompts, prompts_negativos = build_prompts_con_background(zona_id)
    if not prompts:
        raise ValueError(f"La zona {zona_id} no tiene productos para detectar.")

    model = detector or obtener_detector_compartido()
    detecciones = model.detectar(ruta, prompts, prompts_negativos=prompts_negativos)
    duracion = time.perf_counter() - inicio

    repo = repository or AuditoriaRepository()
    auditoria_id = repo.siguiente_id()

    original_rel = _guardar_original(ruta, auditoria_id, inputs_dir or INPUTS_DIR)
    evidencia_rel = _generar_evidencia(ruta, auditoria_id, detecciones, evidencia_dir or EVIDENCIA_DIR)

    return _armar_y_guardar(
        zona_id=zona_id,
        fuente=fuente,
        detecciones=detecciones,
        duracion_proceso_segundos=duracion,
        repository=repo,
        archivo_original=original_rel,
        evidencia_path=evidencia_rel,
        auditoria_id=auditoria_id,
    )


def _guardar_original(ruta_origen: Path, auditoria_id: str, inputs_dir: Path) -> str:
    inputs_dir.mkdir(parents=True, exist_ok=True)
    sufijo = ruta_origen.suffix or ".jpg"
    destino = inputs_dir / f"{auditoria_id}_original{sufijo}"
    shutil.copyfile(ruta_origen, destino)
    return f"inputs/{destino.name}"


def _generar_evidencia(
    ruta_origen: Path, auditoria_id: str, detecciones: list[Deteccion], evidencia_dir: Path
) -> str:
    destino = evidencia_dir / f"{auditoria_id}_anotada.jpg"
    dibujar_bounding_boxes(
        imagen_ruta=ruta_origen,
        detecciones=detecciones,
        productos=cargar_productos(),
        salida=destino,
    )
    return f"outputs/evidencia/{destino.name}"


def guardar_auditoria_viva(
    zona_id: str,
    detecciones: list[Deteccion],
    duracion_proceso_segundos: float,
    frame_rgb,
    repository: AuditoriaRepository | None = None,
    inputs_dir: Path | None = None,
    evidencia_dir: Path | None = None,
) -> Auditoria:
    """Persiste una auditoria desde video en vivo (fuente camara_viva).

    Guarda el ultimo frame como original y la version anotada como evidencia.
    """
    from PIL import Image

    repo = repository or AuditoriaRepository()
    auditoria_id = repo.siguiente_id()
    inputs_dir = inputs_dir or INPUTS_DIR
    evidencia_dir = evidencia_dir or EVIDENCIA_DIR
    inputs_dir.mkdir(parents=True, exist_ok=True)
    evidencia_dir.mkdir(parents=True, exist_ok=True)

    original_destino = inputs_dir / f"{auditoria_id}_original.jpg"
    Image.fromarray(frame_rgb).save(original_destino, "JPEG", quality=88)

    anotada = dibujar_sobre_array(frame_rgb, detecciones, cargar_productos())
    evidencia_destino = evidencia_dir / f"{auditoria_id}_anotada.jpg"
    anotada.save(evidencia_destino, "JPEG", quality=90)

    return _armar_y_guardar(
        zona_id=zona_id,
        fuente=FuenteAuditoria.CAMARA_VIVA,
        detecciones=detecciones,
        duracion_proceso_segundos=duracion_proceso_segundos,
        repository=repo,
        archivo_original=f"inputs/{original_destino.name}",
        evidencia_path=f"outputs/evidencia/{evidencia_destino.name}",
        auditoria_id=auditoria_id,
    )