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

The local drawing templates (Yerel UİP, Yerel NİP) have their own function
vocabulary, kept in the workspace's own lookup tables (``uipPolygonTable``,
``uipLineTable``, ``fonksiyonlar-5000_tablo``) or in the value list of the
function field. ``local_functions`` reads it from the loaded workspace, so a
choice fills exactly the values the planner's template defines: nothing is
mapped across vocabularies and nothing is invented.
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
    layer_mark: str = ""    # the target layer's mpyy/template mark; "" = the MPYY type's
    source: str = "ek1e"    # "ek1e" (Ministry catalogue) or "yerel" (local template)

    @property
    def mark(self) -> str:
        return self.layer_mark or "mpyy:" + self.feature_type

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


def find_layer(feature_type: str, project=None, mark: str = ""):
    """The loaded workspace layer carrying ``mark`` (default: the MPYY type's), if any."""
    from qgis.core import QgsProject

    project = project or QgsProject.instance()
    wanted = mark or "mpyy:" + feature_type
    for layer in project.mapLayers().values():
        if layer.customProperty("mpyy/template") == wanted:
            return layer
    return None


# Local templates: drawing layer -> (level, lookup table or None, name field,
# group field, {drawing-layer field: lookup field}, geometry word).
LOCAL_SOURCES = {
    "uip-alanlar": ("UIP", "uipPolygonTable", "uip_fonksiyon", "ust_konu_grup",
                    {"uipfonksiyon": "uip_fonksiyon", "ustkonugrup": "ust_konu_grup",
                     "uip_tabaka": "uip_tabaka", "id1": "id1", "id2": "id2", "id3": "id3"}, "alan"),
    "uip_cizgiler": ("UIP", "uipLineTable", "uip_fonksiyon", "ust_konu_grup",
                     {"uipfonksiyon": "uip_fonksiyon"}, "çizgi"),
    "alanlar-5000": ("NIP", "fonksiyonlar-5000_tablo", "nip_fonksiyon", "ust_konu_grup",
                     {"nipfonksiyon": "nip_fonksiyon"}, "alan"),
    "cizgiler_5000_v2": ("NIP", None, "nipfonksiyon", None, {}, "çizgi"),
}


def _value_map(layer, field: str) -> list:
    """The stored values of a ValueMap widget, in the order the form shows them."""
    index = layer.fields().indexFromName(field)
    if index < 0:
        return []
    setup = layer.editorWidgetSetup(index)
    if setup.type() != "ValueMap":
        return []
    entries = setup.config().get("map", [])
    if isinstance(entries, dict):
        entries = [{k: v} for k, v in entries.items()]
    values = []
    for entry in entries:
        for value in entry.values():
            text = "" if value is None else str(value)
            # QGIS writes NULL in a value map as a fixed placeholder string.
            if text and not text.startswith("{2839923C") and text not in values:
                values.append(text)
    return values


def _blank(value) -> bool:
    return value is None or str(value) in ("", "NULL")


def local_functions(level: str, project=None) -> list:
    """The functions of the loaded local template workspace(s) of ``level``."""
    from qgis.core import QgsProject

    project = project or QgsProject.instance()
    by_mark = {}
    for layer in project.mapLayers().values():
        mark = layer.customProperty("mpyy/template")
        if mark:
            by_mark.setdefault(str(mark), layer)
    out = []
    for mark, (lvl, table, name_field, group_field, fields, kind) in LOCAL_SOURCES.items():
        target = by_mark.get(mark)
        if lvl != level or target is None:
            continue
        if table:
            lookup = by_mark.get(table)
            if lookup is None:
                continue
            names = lookup.fields().names()
            rows = [{name: feature[name] for name in names} for feature in lookup.getFeatures()]
        else:
            rows = [{name_field: value} for value in _value_map(target, name_field)]
            fields = {name_field: name_field}
        present = set(target.fields().names())
        level_word = "UİP" if lvl == "UIP" else "NİP"
        for n, row in enumerate(rows):
            name = row.get(name_field)
            if _blank(name):
                continue
            attrs = tuple((field, str(row[source])) for field, source in fields.items()
                          if field in present and not _blank(row.get(source)))
            group = "" if not group_field or _blank(row.get(group_field)) else str(row[group_field])
            out.append(PlanFunction(
                record_id=f"yerel:{mark}:{n}", name=str(name), group=group,
                subgroup=(group + " · " if group else "") + f"Yerel {level_word} {kind}",
                level=lvl, feature_type=target.name(), attrs=attrs, page=0, layer_mark=mark, source="yerel"))
    return out


def loaded_kinds(project=None) -> dict:
    """Which workspaces are loaded: {"mpyy": bool, "yerel": {levels}}."""
    from qgis.core import QgsProject

    project = project or QgsProject.instance()
    marks = {str(layer.customProperty("mpyy/template") or "") for layer in project.mapLayers().values()}
    return {"mpyy": any(m.startswith("mpyy:") for m in marks),
            "yerel": {source[0] for mark, source in LOCAL_SOURCES.items() if mark in marks}}


def activate(function: PlanFunction, project=None, iface=None):
    """Open the function's layer for drawing with its values as defaults.

    Returns the layer, or raises ``LookupError`` when the workspace has no such
    layer loaded. Defaults set by an earlier choice on the same layer are
    cleared first, so switching from YERLEŞİK to GELİŞME konut never leaves
    the old value behind.
    """
    from qgis.core import QgsDefaultValue

    layer = find_layer(function.feature_type, project, function.mark)
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
        if index < 0:
            continue
        if layer.fields().at(index).isNumeric():
            try:
                literal = repr(float(code)) if "." in str(code) else str(int(code))
            except ValueError:
                continue
        else:
            literal = "'" + str(code).replace("'", "''") + "'"
        layer.setDefaultValueDefinition(index, QgsDefaultValue(literal))
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
