from __future__ import annotations

from pathlib import Path

import yaml

from . import __version__

_RULES_FILE = Path(__file__).parent / "rules" / "author_rules.yaml"
_VENUE_DIR = Path(__file__).parent / "venues"


def rules_version() -> str:
    return yaml.safe_load(_RULES_FILE.read_text(encoding="utf-8")).get("rules_version", "unknown")


def venue_versions() -> dict[str, str]:
    out: dict[str, str] = {}
    for path in sorted(_VENUE_DIR.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        out[data.get("venue", path.stem)] = data.get("profile_version", "unknown")
    return out


def knowledge_versions() -> dict[str, object]:
    return {
        "engine": __version__,
        "rules_version": rules_version(),
        "venues": venue_versions(),
    }
