from __future__ import annotations

import logging
import os


def configurar_logging() -> None:
    """Configura el logging raiz de la app.

    Lee el nivel de LOG_LEVEL (default INFO). Se llama una vez al inicio
    de ``app.api.main``.
    """
    nivel = os.environ.get("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=nivel,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    # Silenciar libs ruidosas en POC.
    for nombre in ("urllib3", "httpcore", "httpx"):
        logging.getLogger(nombre).setLevel(logging.WARNING)
