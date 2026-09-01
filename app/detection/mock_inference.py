from __future__ import annotations

from pathlib import Path

from app.inventory.loader import FIXTURES_DIR, load_json
from app.inventory.schemas import Deteccion


def cargar_detecciones_fixture(fixture: str, fixtures_dir: Path | None = None) -> list[Deteccion]:
    base_dir = fixtures_dir or FIXTURES_DIR
    fixture_path = base_dir / Path(fixture).name
    if not fixture_path.exists():
        raise FileNotFoundError(f"No existe el fixture de detecciones: {fixture}")
    raw = load_json(fixture_path)
    if not isinstance(raw, list):
        raise ValueError("El fixture de detecciones debe ser una lista JSON.")
    return [Deteccion(**item) for item in raw]

