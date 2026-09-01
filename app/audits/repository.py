from __future__ import annotations

import json
from pathlib import Path

from app.inventory.loader import ROOT_DIR
from app.inventory.schemas import Auditoria, model_to_dict


OUTPUTS_DIR = ROOT_DIR / "outputs" / "auditorias"


class AuditoriaRepository:
    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or OUTPUTS_DIR
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def guardar(self, auditoria: Auditoria) -> str:
        path = self._path(auditoria.auditoria_id)
        with path.open("w", encoding="utf-8") as file:
            json.dump(model_to_dict(auditoria), file, ensure_ascii=False, indent=2)
        return auditoria.auditoria_id

    def cargar(self, auditoria_id: str) -> Auditoria:
        path = self._path(auditoria_id)
        if not path.exists():
            raise FileNotFoundError(f"No existe la auditoria: {auditoria_id}")
        with path.open("r", encoding="utf-8") as file:
            return Auditoria(**json.load(file))

    def listar(self, zona_id: str | None = None) -> list[Auditoria]:
        auditorias = []
        for path in sorted(self.base_dir.glob("*.json")):
            with path.open("r", encoding="utf-8") as file:
                auditoria = Auditoria(**json.load(file))
            if zona_id is None or auditoria.zona_id == zona_id:
                auditorias.append(auditoria)
        return auditorias

    def siguiente_id(self) -> str:
        return f"auditoria_{len(list(self.base_dir.glob('*.json'))) + 1:03d}"

    def _path(self, auditoria_id: str) -> Path:
        safe_id = Path(auditoria_id).stem
        return self.base_dir / f"{safe_id}.json"

