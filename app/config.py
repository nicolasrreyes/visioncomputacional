from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Settings:
    """Configuracion centralizada.  Se pueden sobreescribir con env vars."""

    max_upload_mb: int = int(os.environ.get("VISINVENT_MAX_UPLOAD_MB", "10"))
    rtc_intervalo_seg: float = float(os.environ.get("VISINVENT_RTC_INTERVALO_SEG", "1.0"))
    rtc_max_dimension: int = int(os.environ.get("VISINVENT_RTC_MAX_DIMENSION", "640"))
    api_host: str = os.environ.get("VISINVENT_API_HOST", "127.0.0.1")
    api_port: int = int(os.environ.get("VISINVENT_API_PORT", "8000"))
    cors_origins: list[str] = field(default_factory=lambda: ["*"])
    log_level: str = os.environ.get("VISINVENT_LOG_LEVEL", "INFO")


settings = Settings()
