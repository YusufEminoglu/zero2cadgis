"""Draw by plan function: pick "YERLEŞİK KONUT ALANI", draw, and the MPYY type follows.

A planner thinks in functions from the Ek-1e catalogue, not in MPYY 1.1.7 tables
and their code lists. Here each catalogue row of a level becomes a choice:

* its name, class and sub-class are the Ek-1e detail hierarchy's
  (``styles/mpyy_detail_hierarchy.json``);
* its MPYY type is the row's ``plan_gml_tipi``;
* its attribute values are the conditions of the Ministry SLD rule the row is
  drawn by (``styles/mpyy_sld/mapping.json``: rule ``YERLESIK_KONUT`` is
  ``KonutTip = YerlesikKonut``). A row whose rule is the whole type (``*``) sets
  no attribute: none is invented.

``activate`` opens that type's layer for editing, makes those values the
defaults of every new feature and starts the add-feature tool, so the drawn
feature already carries its function; the form can still change it.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
HIERARCHY_PATH = PLUGIN_ROOT / "styles" / "mpyy_detail_hierarchy.json"
MAPPING_PATH = PLUGIN_ROOT / "styles" / "mpyy_sld" / "mapping.json"
ACTIVE_PROPERTY = "mpyy/aktif_fonksiyon"


@dataclass(frozen=True)
class PlanFunction:
    record_id: str
    name: str
    group: str
    subgroup: str
    level: str
    feature_type: str
    attrs: tuple            # ((field, code), ...)
    page: int

    @property
    def label(self) -> str:
        return f"{self.name}  —  {self.subgroup}"

    def describe(self) -> str:
        values = ", ".join(f"{field}={code}" for field, code in self.attrs)
        return self.feature_type + (f" ({values})" if values else "")


@lru_cache(maxsize=None)
def _mapping() -> dict:
    return json.loads(MAPPING_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def _records() -> tuple:
    return tuple(json.loads(HIERARCHY_PATH.read_text(encoding="utf-8"))["records"])


def plan_functions(level: str) -> list[PlanFunction]:
    """Every catalogue function of a plan level, in catalogue order."""
    types = _mapping()["levels"].get(level, {}).get("types", {})
    out = []
    for record in _records():
        if record["plan_kademesi"] != level:
            continue
        if "+" in record["plan_gml_tipi"]:
            # Six road records ("Yolorta + AdaKenari + DigerYolNesneleri") are drawn
            # by three tables together: no single layer to draw them in.
            continue
        rules = {rule["title"]: rule for rule in types.get(record["plan_gml_tipi"], {}).get("rules", [])}
        rule = rules.get(record["sld_kurali"])
        attrs = ()
        if rule is not None and not rule.get("dropped"):
            attrs = tuple((c["field"], c["code"]) for c in rule.get("conditions", []) if c.get("code"))
        out.append(PlanFunction(
            record_id=record["id"], name=record["sembol_adi"], group=record["detay_sinifi"],
            subgroup=record["detay_alt_sinifi"], level=level, feature_type=record["plan_gml_tipi"],
            attrs=attrs, page=int(record.get("kaynak_sayfa") or 0)))
    return out


def find_layer(feature_type: str, project=None):
    """The loaded MPYY workspace layer of ``feature_type``, if any."""
    from qgis.core import QgsProject

    project = project or QgsProject.instance()
    for layer in project.mapLayers().values():
        if layer.customProperty("mpyy/template") == "mpyy:" + feature_type:
            return layer
    return None


def activate(function: PlanFunction, project=None, iface=None):
    """Open the function's layer for drawing with its values as defaults.

    Returns the layer, or raises ``LookupError`` when the workspace has no such
    layer loaded. Defaults set by an earlier choice on the same layer are
    cleared first, so switching from YERLEŞİK to GELİŞME konut never leaves
    the old value behind.
    """
    from qgis.core import QgsDefaultValue

    layer = find_layer(function.feature_type, project)
    if layer is None:
        raise LookupError(
            f"'{function.feature_type}' katmanı yüklü bir MPYY çalışma alanında bulunamadı.")
    previous = layer.customProperty(ACTIVE_PROPERTY) or ""
    for field in [f for f in str(previous).split(",") if f]:
        index = layer.fields().indexFromName(field)
        if index >= 0:
            layer.setDefaultValueDefinition(index, QgsDefaultValue())
    for field, code in function.attrs:
        index = layer.fields().indexFromName(field)
        if index >= 0:
            layer.setDefaultValueDefinition(index, QgsDefaultValue("'" + code.replace("'", "''") + "'"))
    layer.setCustomProperty(ACTIVE_PROPERTY, ",".join(field for field, _code in function.attrs))
    layer.setCustomProperty("mpyy/aktif_fonksiyon_adi", function.name)
    if not layer.isEditable():
        layer.startEditing()
    if iface is not None:
        iface.setActiveLayer(layer)
        action = iface.actionAddFeature()
        if action is not None:
            action.trigger()
    return layer
