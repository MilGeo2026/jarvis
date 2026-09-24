"""Zentrale Theme-Konfiguration fuer die JARVIS-Oberflaeche (Farben, Transparenz, Animationen)."""
from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path

logger = logging.getLogger("jarvis.ui")


@dataclass(frozen=True)
class Theme:
    primary_color: str = "#00BFFF"
    secondary_color: str = "#0088AA"
    error_color: str = "#FF4B4B"
    background_color: str = "#04070C"
    background_opacity: float = 0.85
    text_color: str = "#E4F6FF"
    font_family: str = "Consolas"
    glow: bool = True
    animations: bool = True

    @classmethod
    def load(cls, path: str | Path) -> "Theme":
        """Laedt das Theme aus einer JSON-Datei. Fehlt die Datei oder ist sie ungueltig,
        wird das Standard-Theme verwendet, statt die Anwendung abstuerzen zu lassen."""
        file_path = Path(path)
        if not file_path.exists():
            logger.warning("Theme-Datei '%s' nicht gefunden, verwende Standard-Theme.", file_path)
            return cls()
        try:
            raw = json.loads(file_path.read_text(encoding="utf-8")).get("theme", {})
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Theme-Datei '%s' konnte nicht gelesen werden (%s), verwende Standard-Theme.", file_path, exc)
            return cls()

        defaults = cls()
        return cls(
            primary_color=str(raw.get("primaryColor", defaults.primary_color)),
            secondary_color=str(raw.get("secondaryColor", defaults.secondary_color)),
            error_color=str(raw.get("errorColor", defaults.error_color)),
            background_color=str(raw.get("backgroundColor", defaults.background_color)),
            background_opacity=float(raw.get("backgroundOpacity", defaults.background_opacity)),
            text_color=str(raw.get("textColor", defaults.text_color)),
            font_family=str(raw.get("fontFamily", defaults.font_family)),
            glow=bool(raw.get("glow", defaults.glow)),
            animations=bool(raw.get("animations", defaults.animations)),
        )

    def save(self, path: str | Path) -> None:
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "theme": {
                "primaryColor": self.primary_color,
                "secondaryColor": self.secondary_color,
                "errorColor": self.error_color,
                "backgroundColor": self.background_color,
                "backgroundOpacity": self.background_opacity,
                "textColor": self.text_color,
                "fontFamily": self.font_family,
                "glow": self.glow,
                "animations": self.animations,
            }
        }
        file_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def as_dict(self) -> dict:
        return asdict(self)
