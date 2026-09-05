from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DESTINO = ROOT / "data" / "demo_images"

NAV_UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
}

# (nombre_archivo_en_commons, nombre_local)
IMAGENES: list[tuple[str, str]] = [
    ("Soda bottle shelf.jpg", "botellas_en_estante.jpg"),
    ("Supermarket in Brno; softdrink bottles.JPG", "estante_supermercado.jpg"),
    ("Soft drink shelf.JPG", "estante_gaseosas.jpg"),
    ("Cardboard box with office supplies.jpg", "caja_carton.jpg"),
]


def _api(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "AuditoriaVisualPOC/1.0"})
    with urllib.request.urlopen(req, timeout=60) as response:
        return json.load(response)


def _descargar(commons_file: str, local_name: str) -> None:
    api = "https://commons.wikimedia.org/w/api.php"
    params = {
        "action": "query",
        "titles": f"File:{commons_file}",
        "prop": "imageinfo",
        "iiprop": "url|extmetadata",
        "format": "json",
    }
    data = _api(api + "?" + urllib.parse.urlencode(params))
    for _, page in data["query"]["pages"].items():
        info = page["imageinfo"][0]
        url = info["url"]
        licencia = info.get("extmetadata", {}).get("LicenseShortName", {}).get("value", "?")
        autor = info.get("extmetadata", {}).get("Artist", {}).get("value", "?")
        request = urllib.request.Request(url, headers=NAV_UA)
        with urllib.request.urlopen(request, timeout=120) as response:
            contenido = response.read()
        (DESTINO / local_name).write_bytes(contenido)
        print(f"OK {local_name} ({len(contenido)} bytes) | {commons_file} | {licencia} | {autor}")


def main() -> None:
    DESTINO.mkdir(parents=True, exist_ok=True)
    for commons_file, local_name in IMAGENES:
        try:
            _descargar(commons_file, local_name)
        except Exception as exc:  # noqa: BLE001
            print(f"ERR {commons_file}: {exc}")


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT))
    main()