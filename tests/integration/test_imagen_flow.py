from PIL import Image

from app.audits.repository import AuditoriaRepository
from app.audits.service import procesar_imagen
from app.detection.real_inference import RealDetector
from app.inventory.schemas import Deteccion, FuenteAuditoria


class DetectorStub:
    """Sustituto de RealDetector para pruebas: devuelve detecciones fijas."""

    def __init__(self, detecciones: list[Deteccion]) -> None:
        self.detecciones = detecciones

    def detectar(self, imagen, prompts_por_producto, confianza=0.25) -> list[Deteccion]:
        return list(self.detecciones)


def _crear_imagen(tmp_path):
    ruta = tmp_path / "original.jpg"
    Image.new("RGB", (300, 300), (240, 240, 240)).save(ruta)
    return ruta


def test_procesar_imagen_genera_auditoria_con_evidencia(tmp_path):
    imagen = _crear_imagen(tmp_path)
    repo = AuditoriaRepository(tmp_path / "auditorias")
    detector = DetectorStub(
        [
            Deteccion(producto_id="caja_carton_chica", label="caja", confianza=0.88, bbox=[10, 10, 80, 80]),
            Deteccion(producto_id="caja_carton_chica", label="caja", confianza=0.82, bbox=[90, 10, 160, 80]),
            Deteccion(producto_id="botella_plastica", label="botella", confianza=0.91, bbox=[10, 100, 60, 200]),
            Deteccion(producto_id="botella_plastica", label="botella", confianza=0.77, bbox=[80, 100, 130, 200]),
        ]
    )

    auditoria = procesar_imagen(
        zona_id="estanteria_a",
        ruta_imagen=imagen,
        fuente=FuenteAuditoria.IMAGEN,
        detector=detector,
        repository=repo,
        inputs_dir=tmp_path / "inputs",
        evidencia_dir=tmp_path / "evidencia",
    )

    assert auditoria.conteos["caja_carton_chica"] == 2
    assert auditoria.conteos["botella_plastica"] == 2
    assert auditoria.archivo_original == "inputs/auditoria_001_original.jpg"
    assert auditoria.evidencia_path == "outputs/evidencia/auditoria_001_anotada.jpg"
    assert (tmp_path / "inputs" / "auditoria_001_original.jpg").exists()
    assert (tmp_path / "evidencia" / "auditoria_001_anotada.jpg").exists()
    cargada = repo.cargar(auditoria.auditoria_id)
    assert cargada.archivo_original == auditoria.archivo_original


def test_procesar_imagen_imagen_inexistente(tmp_path):
    try:
        procesar_imagen(
            zona_id="estanteria_a",
            ruta_imagen=tmp_path / "no_existe.jpg",
            detector=DetectorStub([]),
            repository=AuditoriaRepository(tmp_path / "auditorias"),
        )
    except FileNotFoundError:
        return
    raise AssertionError("Deberia lanzar FileNotFoundError")


def test_procesar_imagen_zona_desconocida(tmp_path, monkeypatch):
    imagen = _crear_imagen(tmp_path)
    try:
        procesar_imagen(
            zona_id="zona_inexistente",
            ruta_imagen=imagen,
            detector=DetectorStub([]),
        )
    except ValueError:
        return
    raise AssertionError("Deberia lanzar ValueError")


def test_real_detector_clase_importable():
    assert RealDetector._detectar_device() in {"cpu", "cuda"}