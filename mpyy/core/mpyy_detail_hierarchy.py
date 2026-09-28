"""Catalog hierarchy for MPYY polygon and line symbols.

The MPYY XSD remains the authoritative edit schema.  This companion mapping
only supplies the regulation catalog's human-facing classification for the
renderer and the ``mpyy_detay_katalogu`` GeoPackage table.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from qgis.core import QgsRuleBasedRenderer


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
HIERARCHY_PATH = PLUGIN_ROOT / "styles" / "mpyy_detail_hierarchy.json"
CURRENT_OF = {"MUIP": "UIP", "MNIP": "NIP", "MCDP25": "CDP", "MCDP100": "CDP"}


@lru_cache(maxsize=1)
def hierarchy() -> dict:
    return json.loads(HIERARCHY_PATH.read_text(encoding="utf-8"))


def records_for(level: str, type_name: str) -> list[dict]:
    """Catalog rows for a feature type, borrowing the current-level mapping for M levels."""
    source_level = CURRENT_OF.get(level, level)
    return [
        record for record in hierarchy()["records"]
        if record["plan_kademesi"] == source_level and record["plan_gml_tipi"] == type_name
    ]


def records_for_level(level: str) -> list[dict]:
    """All catalog rows for one workspace's plan level."""
    source_level = CURRENT_OF.get(level, level)
    return [record for record in hierarchy()["records"] if record["plan_kademesi"] == source_level]


def apply_renderer_hierarchy(layer, level: str, type_name: str) -> list[dict]:
    """Expose catalog names in a rule renderer and retain its full hierarchy as layer metadata."""
    records = records_for(level, type_name)
    renderer = layer.renderer()
    if isinstance(renderer, QgsRuleBasedRenderer):
        for rule in renderer.rootRule().children():
            technical_label = rule.label()
            record = record_for_rule(records, technical_label)
            if record:
                rule.setDescription(
                    f"{record['sembol_adi']} → {record['detay_sinifi']} → {record['detay_alt_sinifi']}"
                )
    classes = sorted({record["detay_sinifi"] for record in records})
    subclasses = sorted({record["detay_alt_sinifi"] for record in records})
    if classes:
        layer.setCustomProperty("mpyy/detay_sinifi", " | ".join(classes))
        layer.setCustomProperty("mpyy/detay_alt_sinifi", " | ".join(subclasses))
        layer.setCustomProperty("mpyy/detay_hiyerarsisi", json.dumps(records, ensure_ascii=False))
    else:
        for key in ("mpyy/detay_sinifi", "mpyy/detay_alt_sinifi", "mpyy/detay_hiyerarsisi"):
            layer.removeCustomProperty(key)
    return records


def record_for_rule(records: list[dict], label: str) -> dict | None:
    for record in records:
        if record["sld_kurali"] == label:
            return record
    return None
