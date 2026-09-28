# -*- coding: utf-8 -*-
"""mpyy_transfer — imported CAD layers -> MPYY 1.1.7 workspace with MPYY styles.

The MPYY UİP / NİP / ÇDP styles are MPYY Studio's: one Ministry e-Plan SLD per
MPYY feature type, with Ek-1e catalog corrections and the plan symbol fonts.
They are carried inside this plugin under ``zero2cadgis/mpyy`` (copied unchanged
by ``tools/sync_mpyy_styles.py``), so nothing here needs MPYY Studio installed.

Those styles are written for MPYY feature types and their XSD attributes
(``Konut`` with ``KonutTip=GelismeKonut``), not for CAD tabaka. The route is
MPYY Studio's own: create a MPYY workspace GeoPackage for the plan level, write
each CAD feature into it by its tabaka through the crosswalk table
(``import_cad_layer``), and load the workspace layers, which styles them.

A tabaka the crosswalk does not define, or whose geometry does not fit its MPYY
type, is not guessed: it is reported, and its features stay in the ordinary
02CadGis layers returned as ``leftovers``.

Copyright (C) 2026 Yusuf Eminoğlu
SPDX-License-Identifier: GPL-2.0-or-later
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

MPYY_LEVELS = ("UIP", "NIP", "CDP")
LEVEL_TITLES = {"UIP": "UİP", "NIP": "NİP", "CDP": "ÇDP"}


@dataclass
class MpyyTransferResult:
    """What one transfer produced."""

    level: str
    workspace: str
    layers: List[Any] = field(default_factory=list)       # styled MPYY layers with features
    leftovers: List[Any] = field(default_factory=list)    # 02CadGis layers of untransferred tabaka
    report: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def transferred(self) -> int:
        return sum(int(r.get("aktarilan") or 0) for r in self.report)

    @property
    def unmatched(self) -> List[Dict[str, Any]]:
        return [r for r in self.report if not r.get("aktarilan") or r.get("geometri_uyusmayan")]

    def summary(self) -> str:
        left = sorted({r["tabaka"] for r in self.unmatched if r.get("tabaka")})
        text = (f"MPYY {LEVEL_TITLES.get(self.level, self.level)}: {self.transferred} nesne "
                f"{len(self.layers)} MPYY katmanına aktarıldı")
        if left:
            shown = ", ".join(left[:12]) + (" …" if len(left) > 12 else "")
            text += f"; eşleşmeyen {len(left)} tabaka ayrı grupta kaldı ({shown})"
        return text


def transfer_to_mpyy(
    layers: List[Any],
    level: str,
    workspace_path: str,
    group_name: str,
    tabaka_field: str = "layer_name",
    project: Any = None,
) -> MpyyTransferResult:
    """Write ``layers`` into a new MPYY workspace of ``level`` and load it styled.

    ``workspace_path`` must not exist yet. The loaded MPYY layers are placed in a
    layer-tree group named ``group_name``; feature types that received nothing
    are not loaded. Untransferred features are returned as memory layers.
    """
    from qgis.core import QgsFeatureRequest, QgsProject

    from ..mpyy.core import mpyy_import, mpyy_workspace

    if level not in MPYY_LEVELS:
        raise ValueError(f"MPYY kademesi desteklenmiyor: {level}")
    project = project or QgsProject.instance()
    layers = [lyr for lyr in layers if lyr is not None and lyr.isValid()
              and lyr.fields().indexFromName(tabaka_field) >= 0]
    if not layers:
        raise ValueError(f"Aktarılacak katmanlarda tabaka alanı yok: {tabaka_field}")

    mpyy_workspace.create_mpyy_workspace(workspace_path, layers[0].crs(), level)
    result = MpyyTransferResult(level=level, workspace=workspace_path)
    left_by_layer: Dict[int, set] = {}
    for index, layer in enumerate(layers):
        rows = mpyy_import.import_cad_layer(layer, tabaka_field, workspace_path, project=project)
        result.report.extend(rows)
        left_by_layer[index] = {r["tabaka"] for r in rows
                                if not r.get("aktarilan") or r.get("geometri_uyusmayan")}

    # MPYY Studio's load_mpyy_layers styles every type of the level (97 for
    # UİP) although an import fills a handful; styling is the slow step, so
    # only the types that received features are loaded — with the same calls,
    # in the same order, into the same Alanlar / Çizgiler / Noktalar groups.
    filled = {r["mpyy_tipi"] for r in result.report if r.get("aktarilan")}
    result.layers = _load_filled_types(
        mpyy_workspace, workspace_path, level, filled, group_name, project)

    for index, layer in enumerate(layers):
        tabakas = sorted(t for t in left_by_layer.get(index, ()) if t is not None)
        if not tabakas:
            continue
        quoted = ", ".join("'" + str(t).replace("'", "''") + "'" for t in tabakas)
        request = QgsFeatureRequest().setFilterExpression(f'"{tabaka_field}" IN ({quoted})')
        leftover = layer.materialize(request)
        if leftover.featureCount():
            leftover.setName(layer.name())
            result.leftovers.append(leftover)
    return result


def _load_filled_types(mpyy_workspace, workspace_path, level, filled, group_name, project):
    from qgis.core import QgsVectorLayer

    schema = mpyy_workspace.level_schema(level)
    root = project.layerTreeRoot()
    base = root.insertGroup(0, group_name)
    loaded = []
    for sub_name, geometries in mpyy_workspace._GROUPS:
        members = sorted((t for t in schema["feature_types"]
                          if t["geometry"] in geometries and t["name"] in filled),
                         key=lambda t: t["name"])
        if not members:
            continue
        group = base.addGroup(sub_name)
        for feature_type in members:
            layer = QgsVectorLayer(
                f"{workspace_path}|layername={feature_type['name']}", feature_type["name"], "ogr")
            if not layer.isValid():
                raise RuntimeError("Katman açılamadı: " + feature_type["name"])
            mpyy_workspace.configure_mpyy_layer(layer, feature_type, schema["codelists"])
            if not str(layer.customProperty("mpyy/symbology") or "").startswith(
                    ("e-Plan SLD", "Detay kataloğu")):
                mpyy_workspace.apply_eplan_symbology(layer, level, feature_type["name"])
            if not layer.labelsEnabled() and not mpyy_workspace.apply_line_labels(
                    layer, level, feature_type["name"]):
                mpyy_workspace.apply_building_notation(layer)
            project.addMapLayer(layer, False)
            group.addLayer(layer)
            loaded.append(layer)
    base.setExpanded(True)
    return loaded


def mpyy_level_for(plan_type: Optional[str]) -> Optional[str]:
    """The MPYY level a resolved 02CadGis plan type maps to, if any."""
    value = (plan_type or "").upper()
    return value if value in MPYY_LEVELS else None
