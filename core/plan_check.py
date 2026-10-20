# -*- coding: utf-8 -*-
"""plan_check — what an imported imar plan says that does not add up.

Run on the plan-area polygons a plan-mode import builds (tabaka in
``layer_name``, building rights in the MPYY field names ``Taks``,
``EmsalKaks``, ``KatAdedi``) and on the drawing's own notation points. Each
check reports a finding where it occurs; none changes the data.

* ``unreachable_kaks`` — KAKS above TAKS x floors cannot be built: the
  footprint times the storey count is the most floor area a parcel can hold.
  KAKS *below* TAKS x floors is not reported; it is the usual case of the
  KAKS being the binding limit.
* ``kaks_below_taks`` — less floor area than one full storey of footprint.
* ``value_out_of_range`` — TAKS outside (0, 1], fewer than one storey, a
  non-positive KAKS: not a plan decision but a reading or typing error, and
  the MPYY transfer leaves such a value out.
* ``notation_disagrees`` — the notation inside one plan area states
  different values for one field, so the area carries none (the notation
  layer still shows each). Often legitimate: one area spanning several
  blocks; reported so the empty field is explained.
* ``notation_outside_areas`` — building notation that lies in no plan area.
* ``overlapping_areas`` — two land-use decisions (``PL_`` tabaka) covering
  the same ground; ``duplicate_area`` when one is the other drawn twice,
  reported once per extra copy. A drawing can store an object twice, byte for
  byte (TİRE UİP: 1 486 polygons); each copy then becomes a feature and its
  area counts twice in any sum. Constraint (``KST_``) and boundary (``SNR_``)
  tabaka overlap land use by design and are not compared.

Thresholds are stated, not tuned: density compares at 0.01, the precision
plans state ratios at; an overlap counts from 1 m², below which it is the
drawing's snapping noise.

Copyright (C) 2026 Yusuf Eminoğlu
SPDX-License-Identifier: GPL-2.0-or-later
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Sequence

ERROR, WARNING, INFO = "error", "warning", "info"

DENSITY_TOLERANCE = 0.01
OVERLAP_MIN_AREA_M2 = 1.0
# Two polygons whose overlap covers this share of both are one area drawn twice.
DUPLICATE_SHARE = 0.99

CHECK_LABELS = {
    "unreachable_kaks": "KAKS above TAKS × floors",
    "kaks_below_taks": "KAKS below TAKS",
    "value_out_of_range": "Value outside its physical range",
    "notation_disagrees": "Notation in one area disagrees",
    "notation_outside_areas": "Notation outside every plan area",
    "overlapping_areas": "Land-use areas overlap",
    "duplicate_area": "Area drawn twice",
}
SEVERITY_OF = {
    "unreachable_kaks": WARNING,
    "kaks_below_taks": WARNING,
    "value_out_of_range": ERROR,
    "notation_disagrees": INFO,
    "notation_outside_areas": WARNING,
    "overlapping_areas": WARNING,
    "duplicate_area": WARNING,
}
NOTATION_FIELDS = ("YapiDuzeni", "KatAdedi", "Taks", "EmsalKaks", "YapiYuksekligi",
                   "OnBahceMesafesi", "YanBahceMesafesi")
TABAKA_FIELDS = ("layer_name", "uip_tabaka", "Layer")


@dataclass
class PlanFinding:
    check: str
    message: str
    geometry: Any                    # QgsGeometry: a point, or the overlap polygon
    tabaka: str = ""
    other_tabaka: str = ""
    values: Dict[str, Any] = field(default_factory=dict)

    @property
    def severity(self) -> str:
        return SEVERITY_OF[self.check]

    @property
    def label(self) -> str:
        return CHECK_LABELS[self.check]


@dataclass
class PlanCheckResult:
    findings: List[PlanFinding] = field(default_factory=list)
    areas_checked: int = 0
    notation_checked: int = 0

    def count(self, check: str) -> int:
        return sum(f.check == check for f in self.findings)

    def by_severity(self) -> Dict[str, int]:
        counts = {ERROR: 0, WARNING: 0, INFO: 0}
        for finding in self.findings:
            counts[finding.severity] += 1
        return counts

    def summary(self) -> str:
        if not self.findings:
            return (f"Plan check: nothing to report on {self.areas_checked} plan areas "
                    f"and {self.notation_checked} notation points.")
        parts = [f"{label} ({self.count(check)})"
                 for check, label in CHECK_LABELS.items() if self.count(check)]
        return (f"Plan check on {self.areas_checked} plan areas and "
                f"{self.notation_checked} notation points: " + "; ".join(parts) + ".")


def _value(feature, name: str) -> Optional[float]:
    """A numeric attribute, or None when absent, NULL or not a number."""
    try:
        raw = feature[name]
    except (KeyError, IndexError):
        return None
    if raw is None or str(raw) in ("", "NULL"):
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def _tabaka_field(layer) -> Optional[str]:
    names = layer.fields().names()
    return next((name for name in TABAKA_FIELDS if name in names), None)


def _is_land_use(tabaka: str) -> bool:
    """A plan decision on land use: the ``PL_`` tabaka (local spellings folded)."""
    from .cad_polygonizer import _tokens
    tokens = _tokens(tabaka or "")
    return bool(tokens) and tokens[0] == "PL"


def _anchor(geometry):
    point = geometry.pointOnSurface()
    return point if point and not point.isEmpty() else geometry.centroid()


def _fmt(value: float) -> str:
    return f"{value:.2f}".rstrip("0").rstrip(".") if value is not None else "-"


def _density_findings(feature, geometry, tabaka: str) -> List[PlanFinding]:
    taks, kaks, floors = (_value(feature, n) for n in ("Taks", "EmsalKaks", "KatAdedi"))
    found = []
    stated = {k: v for k, v in (("Taks", taks), ("EmsalKaks", kaks), ("KatAdedi", floors))
              if v is not None}
    bad = []
    if taks is not None and not 0.0 < taks <= 1.0:
        bad.append(f"TAKS {_fmt(taks)} (must be above 0 and at most 1)")
    if kaks is not None and kaks <= 0.0:
        bad.append(f"KAKS {_fmt(kaks)} (must be above 0)")
    if floors is not None and floors < 1:
        bad.append(f"{_fmt(floors)} floors (at least 1)")
    if bad:
        found.append(PlanFinding(
            "value_out_of_range",
            f"{tabaka}: " + ", ".join(bad) + "; the MPYY transfer leaves it out.",
            _anchor(geometry), tabaka, values=stated))
        return found
    if taks is not None and kaks is not None and floors is not None:
        reachable = taks * floors
        if kaks > reachable + DENSITY_TOLERANCE:
            found.append(PlanFinding(
                "unreachable_kaks",
                f"{tabaka}: KAKS {_fmt(kaks)} cannot be built with TAKS {_fmt(taks)} "
                f"on {int(floors)} floors (at most {_fmt(reachable)}).",
                _anchor(geometry), tabaka, values=stated))
    if taks is not None and kaks is not None and kaks + DENSITY_TOLERANCE < taks:
        found.append(PlanFinding(
            "kaks_below_taks",
            f"{tabaka}: KAKS {_fmt(kaks)} is below TAKS {_fmt(taks)}, less than one "
            "full storey of footprint.",
            _anchor(geometry), tabaka, values=stated))
    return found


def _without_block_repeats(density) -> List[PlanFinding]:
    """Density findings, without a block's copy of a land-use area's finding.

    The zoning values reach every polygon around a notation, so an ADAKENARI
    block and the PL_ area inside it carry the same values and the same fault.
    """
    land_use = [(finding, geometry) for finding, geometry, is_land_use in density if is_land_use]
    kept = [finding for finding, _geometry in land_use]
    for finding, geometry, is_land_use in density:
        if is_land_use:
            continue
        repeated = any(other.check == finding.check and other.values == finding.values
                       and geometry.contains(other.geometry)
                       for other, _other_geometry in land_use)
        if not repeated:
            kept.append(finding)
    return kept


def check_plan(
        polygon_layers: Sequence[Any],
        notation_points: Iterable[Any] = (),
        overlap_min_area: float = OVERLAP_MIN_AREA_M2) -> PlanCheckResult:
    """Run every check over *polygon_layers* and the drawing's *notation_points*.

    A layer without a tabaka field is read as plan areas throughout (an MPYY
    layer: every feature is a plan decision of the layer's own type). Layers
    are expected in a projected CRS; areas are compared in its units.
    """
    from qgis.core import QgsGeometry, QgsPointXY, QgsSpatialIndex, QgsFeature, QgsWkbTypes
    from .cad_engine import is_helper_or_noise_layer
    from .zoning_text_extractor import _is_zoning_target

    result = PlanCheckResult()
    areas = []          # (geometry, tabaka, land_use)
    density = []        # (finding, area geometry, land_use)
    for layer in polygon_layers:
        if layer is None or layer.geometryType() != QgsWkbTypes.GeometryType.PolygonGeometry:
            continue
        tabaka_field = _tabaka_field(layer)
        for feature in layer.getFeatures():
            geometry = feature.geometry()
            if not geometry or geometry.isEmpty():
                continue
            if not geometry.isGeosValid():
                geometry = geometry.makeValid()
                if not geometry or geometry.isEmpty() or geometry.area() <= 0:
                    continue
            tabaka = str(feature[tabaka_field]) if tabaka_field else layer.name()
            if tabaka_field and (is_helper_or_noise_layer(tabaka) or not _is_zoning_target(tabaka)):
                continue
            result.areas_checked += 1
            land_use = _is_land_use(tabaka) if tabaka_field else True
            density.extend((finding, geometry, land_use)
                           for finding in _density_findings(feature, geometry, tabaka))
            areas.append((geometry, tabaka, land_use))
    result.findings.extend(_without_block_repeats(density))

    index = QgsSpatialIndex()
    for area_id, (geometry, _tabaka, _land_use) in enumerate(areas):
        indexed = QgsFeature(area_id)
        indexed.setGeometry(geometry)
        index.addFeature(indexed)

    # Notation against the areas it lies in.
    by_area: Dict[int, List[Any]] = defaultdict(list)
    for point in notation_points:
        if not getattr(point, "values", None):
            continue                              # a road width: no area expected
        result.notation_checked += 1
        geometry = QgsGeometry.fromPointXY(QgsPointXY(point.x, point.y))
        holders = [area_id for area_id in index.intersects(geometry.boundingBox())
                   if areas[area_id][0].contains(geometry)]
        if not holders:
            result.findings.append(PlanFinding(
                "notation_outside_areas",
                "Building notation (" + ", ".join(f"{k} {v}" for k, v in sorted(point.values.items())
                                                 if not k.endswith("Tip")) + ") lies in no plan area.",
                geometry, getattr(point, "tabaka", ""), values=dict(point.values)))
        for area_id in holders:
            by_area[area_id].append(point)
    for area_id, points in sorted(by_area.items()):
        geometry, tabaka, _land_use = areas[area_id]
        differing = {}
        for name in NOTATION_FIELDS:
            stated = {p.values[name] for p in points if p.values.get(name) is not None}
            if len(stated) > 1:
                differing[name] = sorted(stated, key=str)
        if differing:
            detail = "; ".join(f"{name} " + " / ".join(str(v) for v in values)
                               for name, values in differing.items())
            result.findings.append(PlanFinding(
                "notation_disagrees",
                f"{tabaka}: {len(points)} notations in this area disagree ({detail}); "
                "the area carries no value for these fields.",
                _anchor(geometry), tabaka,
                values={name: " / ".join(str(v) for v in values)
                        for name, values in differing.items()}))

    # Land-use decisions covering the same ground. A copy is reported once, as
    # a copy, and then left out of every further comparison: its twin speaks
    # for both.
    copies: set = set()
    for area_id, (geometry, tabaka, land_use) in enumerate(areas):
        if not land_use or area_id in copies:
            continue
        engine = QgsGeometry.createGeometryEngine(geometry.constGet())
        engine.prepareGeometry()
        for other_id in sorted(index.intersects(geometry.boundingBox())):
            if other_id <= area_id or other_id in copies:
                continue
            other, other_tabaka, other_land_use = areas[other_id]
            if not other_land_use or not engine.intersects(other.constGet()):
                continue
            overlap = geometry.intersection(other)
            if overlap is None or overlap.isEmpty():
                continue
            shared = overlap.area()
            if shared < overlap_min_area:
                continue
            twice = (shared >= DUPLICATE_SHARE * geometry.area()
                     and shared >= DUPLICATE_SHARE * other.area())
            if twice:
                copies.add(other_id)
                check = "duplicate_area"
                message = (f"{tabaka} and {other_tabaka}: the same {shared:,.0f} m² area is drawn twice."
                           if tabaka != other_tabaka else
                           f"{tabaka}: the same {shared:,.0f} m² area is drawn twice.")
            else:
                check = "overlapping_areas"
                message = f"{tabaka} and {other_tabaka} overlap by {shared:,.1f} m²."
            result.findings.append(PlanFinding(
                check, message, overlap, tabaka, other_tabaka,
                values={"overlap_m2": round(shared, 2)}))
    return result


FINDING_COLOURS = {ERROR: "#d7191c", WARNING: "#fdae61", INFO: "#2b83ba"}


def build_finding_layers(result: PlanCheckResult, crs) -> List[Any]:
    """A point layer of every finding and a polygon layer of the overlaps."""
    from qgis.core import (
        QgsCategorizedSymbolRenderer, QgsFeature, QgsField, QgsFillSymbol, QgsGeometry,
        QgsMarkerSymbol, QgsRendererCategory, QgsVectorLayer, QgsWkbTypes,
    )
    from qgis.PyQt.QtCore import QMetaType

    if not result.findings:
        return []
    string, double = QMetaType.Type.QString, QMetaType.Type.Double
    fields = [("severity", string), ("check", string), ("label", string), ("message", string),
              ("tabaka", string), ("other_tabaka", string), ("Taks", double),
              ("EmsalKaks", double), ("KatAdedi", double), ("overlap_m2", double)]

    def make(geometry_type: str, name: str):
        layer = QgsVectorLayer(f"{geometry_type}?crs={crs.authid()}", name, "memory")
        layer.dataProvider().addAttributes([QgsField(n, t) for n, t in fields])
        layer.updateFields()
        return layer

    points, overlaps = make("Point", "Plan check"), make("MultiPolygon", "Plan check overlaps")
    notes = make("Point", "Plan check notes")
    point_features, overlap_features, note_features = [], [], []
    for finding in result.findings:
        numeric = {}
        for name in ("Taks", "EmsalKaks", "KatAdedi", "overlap_m2"):
            value = finding.values.get(name)
            numeric[name] = value if isinstance(value, (int, float)) else None
        attributes = [finding.severity, finding.check, finding.label, finding.message,
                      finding.tabaka, finding.other_tabaka, numeric["Taks"],
                      numeric["EmsalKaks"], numeric["KatAdedi"], numeric["overlap_m2"]]
        geometry = finding.geometry
        is_area = geometry.type() == QgsWkbTypes.GeometryType.PolygonGeometry
        feature = QgsFeature(points.fields())
        feature.setAttributes(attributes)
        feature.setGeometry(_anchor(geometry) if is_area else geometry)
        (note_features if finding.severity == INFO else point_features).append(feature)
        if is_area:
            polygon = QgsFeature(overlaps.fields())
            polygon.setAttributes(attributes)
            area = QgsGeometry(geometry)
            area.convertToMultiType()
            polygon.setGeometry(area)
            overlap_features.append(polygon)
    def styled(layer, features):
        layer.dataProvider().addFeatures(features)
        layer.updateExtents()
        categories = []
        for severity, colour in FINDING_COLOURS.items():
            symbol = QgsMarkerSymbol.createSimple({
                "name": "circle", "color": colour, "outline_color": "#ffffff",
                "outline_width": "0.4", "size": "4"})
            categories.append(QgsRendererCategory(severity, symbol, severity.capitalize()))
        layer.setRenderer(QgsCategorizedSymbolRenderer("severity", categories))
        return layer

    layers = []
    if point_features:
        layers.append(styled(points, point_features))
    if note_features:
        # Explanations, not faults: listed, but off until asked for.
        styled(notes, note_features).setCustomProperty("zero2cadgis/hidden", True)
        layers.append(notes)
    if overlap_features:
        overlaps.dataProvider().addFeatures(overlap_features)
        overlaps.updateExtents()
        overlaps.renderer().setSymbol(QgsFillSymbol.createSimple({
            "color": "215,25,28,90", "outline_color": "#d7191c", "outline_width": "0.5"}))
        layers.append(overlaps)
    return layers
