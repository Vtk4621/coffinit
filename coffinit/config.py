"""User configuration persistence for coffinit.

Currently stores only the default UI language.

Precedence (highest -> lowest):
- CLI option (--lang)
- Environment variable (COFFINIT_LANG)
- Config file (~/.config/coffinit/config.json, etc.)
- Default (ja)
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import sys
from typing import Any


_SUPPORTED_LANGS: set[str] = {"ja", "en"}


@dataclass(frozen=True)
class CoffinitConfig:
    lang: str | None = None


def _get_config_dir() -> Path:
    """Return per-user config directory (cross-platform, stdlib only)."""

    # Windows
    if os.name == "nt":
        appdata = os.getenv("APPDATA")
        if appdata:
            return Path(appdata) / "coffinit"
        return Path.home() / "AppData" / "Roaming" / "coffinit"

    # macOS
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "coffinit"

    # Linux / other Unix
    xdg = os.getenv("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg) / "coffinit"
    return Path.home() / ".config" / "coffinit"


def get_config_path() -> Path:
    return _get_config_dir() / "config.json"


def load_config() -> CoffinitConfig:
    path = get_config_path()
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
        if not isinstance(data, dict):
            return CoffinitConfig()
        lang = data.get("lang")
        if isinstance(lang, str) and lang in _SUPPORTED_LANGS:
            return CoffinitConfig(lang=lang)
        return CoffinitConfig()
    except FileNotFoundError:
        return CoffinitConfig()
    except Exception:
        # Corrupted config should never break the CLI.
        return CoffinitConfig()


def save_config(config: CoffinitConfig) -> Path:
    path = get_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    payload: dict[str, Any] = {}
    if config.lang in _SUPPORTED_LANGS:
        payload["lang"] = config.lang

    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def get_saved_lang() -> str | None:
    return load_config().lang


def save_lang(lang: str) -> Path:
    if lang not in _SUPPORTED_LANGS:
        raise ValueError(f"Unsupported lang: {lang}")
    return save_config(CoffinitConfig(lang=lang))
