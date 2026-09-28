# -*- coding: utf-8 -*-
"""zoning_text_extractor — Spatial extraction and regex parsing of zoning parameters.

In Turkish spatial planning drawings (Netcad NCZ, DXF, DWG), building rights and
zoning parameters (yapı düzeni, kat adedi, emsal/KAKS, TAKS, Yençok/Hmax, çekme
mesafeleri, ada/parsel numaraları, yol genişlikleri) are typically placed as text
entities positioned inside or along planning geometries.

This module provides:
  1. Regex parsing of standardized and shorthand Turkish zoning text strings,
     cadastral parcel numbers (Ada/Parsel), and road widths (En-kesit).
  2. Point-in-polygon spatial association to extract and bind zoning attributes
     to their containing plan polygons according to official PlanGML / e-Plan
     specifications.
  3. Proximity-based assignment of road cross-section widths to road lines.

Copyright (C) 2026 Yusuf Eminoğlu
SPDX-License-Identifier: GPL-2.0-or-later
"""
from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass, field
import re
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


@dataclass
class ZoningParameters:
    """Parsed building regulations, cadastral and road parameters."""
    yapi_duzeni: Optional[str] = None          # AYRIK, BITISIK, BLOK, IKIZ, SERBEST
    kat_adedi: Optional[int] = None            # 1, 2, 3, 4, 5...
    emsal_kaks: Optional[float] = None         # e.g. 1.50
    taks: Optional[float] = None               # e.g. 0.35
    yapi_yuksekligi: Optional[float] = None    # e.g. 15.50 (in meters)
    yencok: Optional[str] = None               # Formatted string e.g. "15.50m"
    on_bahce: Optional[float] = None           # e.g. 5.0
    yan_bahce: Optional[float] = None          # e.g. 3.0
    arka_bahce: Optional[float] = None         # e.g. 3.0
    ada_no: Optional[str] = None               # e.g. "101"
    parsel_no: Optional[str] = None            # e.g. "5"
    yol_genisligi: Optional[float] = None      # e.g. 10.0, 12.0, 15.0
    raw_texts: List[str] = field(default_factory=list)

    @property
    def has_any(self) -> bool:
        """True if at least one meaningful zoning parameter was parsed."""
        return any(v is not None for v in (
            self.yapi_duzeni,
            self.kat_adedi,
            self.emsal_kaks,
            self.taks,
            self.yapi_yuksekligi,
            self.on_bahce,
            self.yan_bahce,
            self.arka_bahce,
            self.ada_no,
            self.parsel_no,
            self.yol_genisligi,
        ))

    def as_attribute_dict(self) -> Dict[str, Any]:
        """Convert to official PlanGML attribute dictionary."""
        return {
            "YapiDuzeni": self.yapi_duzeni or "",
            "KatAdedi": self.kat_adedi if self.kat_adedi is not None else None,
            "EmsalKaks": self.emsal_kaks if self.emsal_kaks is not None else None,
            "Taks": self.taks if self.taks is not None else None,
            "YapiYuksekligi": self.yapi_yuksekligi if self.yapi_yuksekligi is not None else None,
            "Yencok": self.yencok or ("" if self.yapi_yuksekligi is None else f"{self.yapi_yuksekligi:g}m"),
            "OnBahceMesafesi": self.on_bahce if self.on_bahce is not None else None,
            "YanBahceMesafesi": self.yan_bahce if self.yan_bahce is not None else None,
            "ArkaBahceMesafesi": self.arka_bahce if self.arka_bahce is not None else None,
            "AdaNo": self.ada_no or "",
            "ParselNo": self.parsel_no or "",
            "YolGenisligi": self.yol_genisligi if self.yol_genisligi is not None else None,
            # MPYY DegerTip: the drawing states a number -> "Deger". Left empty
            # otherwise: whether an absent value is Serbest or GecerliDegil is
            # a planning decision the drawing does not record.
            "EmsalKaksTip": "Deger" if self.emsal_kaks is not None else "",
            "TaksTip": "Deger" if self.taks is not None else "",
            "YapiYuksekligiTip": "Deger" if self.yapi_yuksekligi is not None else "",
            "PlanNotu": "; ".join(self.raw_texts)[:_PLAN_NOTU_MAX_CHARS],
        }


# -----------------------------------------------------------------------------
# Turkish Text Normalization and Regex Patterns
# -----------------------------------------------------------------------------

_TR_UPPER_MAP = str.maketrans({
    "ç": "Ç", "ğ": "Ğ", "ı": "I", "i": "İ", "ö": "Ö", "ş": "Ş", "ü": "Ü"
})

_NIZAM_MAP = {
    "A": "AYRIK",
    "AYRIK": "AYRIK",
    "B": "BITISIK",
    "BITISIK": "BITISIK",
    "BİTİŞİK": "BITISIK",
    "BL": "BLOK",
    "BLOK": "BLOK",
    "İ": "IKIZ",
    "I": "IKIZ",
    "IKIZ": "IKIZ",
    "İKİZ": "IKIZ",
    "S": "SERBEST",
    "SERBEST": "SERBEST",
}

# Regex for Nizam + Kat: e.g. A-3, B-4, BL-5, BLOK-4, A/3, İ-4, AYRIK-3
_RE_NIZAM_KAT = re.compile(
    r"\b(A|AYRIK|B|BITISIK|BİTİŞİK|BL|BLOK|İ|I|IKIZ|İKİZ|S|SERBEST)\s*[-/:]\s*(\d{1,2})\b",
    re.IGNORECASE
)

# Standalone Kat: e.g. "3 KAT", "KAT: 4", "KAT=5"
_RE_KAT_STANDALONE = re.compile(
    r"\b(?:KAT|KAT_ADEDI|KAT_SAYISI)\s*[:=]\s*(\d{1,2})\b|\b(\d{1,2})\s*KAT\b",
    re.IGNORECASE
)

# Emsal / KAKS: e.g. E=1.50, E: 1.2, EMSAL=2.07, KAKS: 1.80
_RE_EMSAL = re.compile(
    r"\b(?:E|EMSAL|KAKS)\s*[:=]\s*(\d+(?:[.,]\d+)?)\b",
    re.IGNORECASE
)

# TAKS: e.g. TAKS=0.35, TAKS: 0.40
_RE_TAKS = re.compile(
    r"\bTAKS\s*[:=]\s*(\d+(?:[.,]\d+)?)\b",
    re.IGNORECASE
)

# Yençok / Hmax / Yükseklik: e.g. Yençok=15.50m, YENÇOK: 12.50, Hmax=15.50, H: 12.50
_RE_YENCOK = re.compile(
    r"\b(?:YENÇOK|YENCOK|HMAX|H_MAX|H|YÜKSEKLİK|YUKSEKLIK)\s*[:=]\s*(\d+(?:[.,]\d+)?)\s*(?:M|METRE)?\b",
    re.IGNORECASE
)

# Setbacks: Ön Bahçe, Yan Bahçe, Arka Bahçe
_RE_ON_BAHCE = re.compile(
    r"\b(?:ÖN|ON)(?:\s*(?:BAHÇE|BAHCE|BAHÇESİ|BAHCESI))?\s*[:=]\s*(\d+(?:[.,]\d+)?)\s*(?:M|METRE)?\b",
    re.IGNORECASE
)
_RE_YAN_BAHCE = re.compile(
    r"\b(?:YAN)(?:\s*(?:BAHÇE|BAHCE|BAHÇESİ|BAHCESI))?\s*[:=]\s*(\d+(?:[.,]\d+)?)\s*(?:M|METRE)?\b",
    re.IGNORECASE
)
_RE_ARKA_BAHCE = re.compile(
    r"\b(?:ARKA)(?:\s*(?:BAHÇE|BAHCE|BAHÇESİ|BAHCESI))?\s*[:=]\s*(\d+(?:[.,]\d+)?)\s*(?:M|METRE)?\b",
    re.IGNORECASE
)

# Setback triplet: e.g. "5/3/3" or "5 - 3 - 3"
_RE_SETBACK_TRIPLET = re.compile(
    r"\b(\d+(?:[.,]\d+)?)\s*[/–-]\s*(\d+(?:[.,]\d+)?)\s*[/–-]\s*(\d+(?:[.,]\d+)?)\b"
)

# Cadastral parcel slash notation: "101/5", "2450/12"
_RE_ADA_PARSEL_SLASH = re.compile(
    r"^\s*(\d{1,6})\s*[/–-]\s*(\d{1,5})\s*$",
    re.IGNORECASE
)
_RE_ADA_EXPLICIT = re.compile(
    r"\bADA\s*[:=]?\s*(\d+)\b",
    re.IGNORECASE
)
_RE_PARSEL_EXPLICIT = re.compile(
    r"\bPARSEL\s*[:=]?\s*(\d+)\b",
    re.IGNORECASE
)

# Road width annotations: e.g. "10.00", "12.00m", "15 m", "7.00 m", "YOL: 12m".
# A standalone number must look like a width — decimals ("10.00") or a unit
# ("15 m"). A bare integer is not accepted: on a real drawing (FOÇA.NCZ) the
# bare integers near road lines were pole numbers ("3", 645 of them) and
# contour/spot-height labels ("20", "25", "35"), and every one became a width.
_RE_ROAD_WIDTH_STANDALONE = re.compile(
    r"^\s*(\d{1,2}(?:[.,]\d{1,2}\s*(?:M|METRE)?|\s*(?:M|METRE)))\.?\s*$",
    re.IGNORECASE
)
_RE_ROAD_WIDTH_PREFIX = re.compile(
    r"\b(?:YOL\s*GENİŞLİĞİ|YOL\s*GENISLIGI|GENİŞLİK|GENISLIK|EN\s*KESİT|EN\s*KESIT|YOL|EN)\s*[:=]?\s*(\d+(?:[.,]\d+)?)\s*(?:M|METRE)?\.?\b",
    re.IGNORECASE
)


def _to_float(val: str) -> Optional[float]:
    if not val:
        return None
    number = re.match(r"\s*(\d+(?:[.,]\d+)?)", val)
    if number is None:
        return None
    try:
        return float(number.group(1).replace(",", "."))
    except ValueError:
        return None


def parse_cadastral_numbers(texts: str | Iterable[str]) -> Tuple[Optional[str], Optional[str]]:
    """Extract cadastral Ada and Parsel numbers from text annotation(s).

    Supports formats like:
      - Slash notation: "101/5", "2450/12"
      - Explicit labels: "Ada: 101, Parsel: 5", "ADA: 245"

    Returns:
        Tuple ``(ada_no, parsel_no)``.
    """
    if isinstance(texts, str):
        texts = [texts]

    ada_no: Optional[str] = None
    parsel_no: Optional[str] = None

    for raw in texts:
        if not raw:
            continue
        line = str(raw).strip()
        m_slash = _RE_ADA_PARSEL_SLASH.search(line)
        if m_slash:
            return m_slash.group(1), m_slash.group(2)

        upper = line.translate(_TR_UPPER_MAP)
        m_ada = _RE_ADA_EXPLICIT.search(upper)
        if m_ada and not ada_no:
            ada_no = m_ada.group(1)

        m_parsel = _RE_PARSEL_EXPLICIT.search(upper)
        if m_parsel and not parsel_no:
            parsel_no = m_parsel.group(1)

    return ada_no, parsel_no


def parse_road_width(texts: str | Iterable[str]) -> Optional[float]:
    """Parse road cross-section / street width from text annotations."""
    if isinstance(texts, str):
        texts = [texts]

    for raw in texts:
        if not raw:
            continue
        line = str(raw).strip()
        m = _RE_ROAD_WIDTH_PREFIX.search(line.translate(_TR_UPPER_MAP))
        if m:
            w = _to_float(m.group(1))
            if w and 3.0 <= w <= 80.0:
                return w
        m2 = _RE_ROAD_WIDTH_STANDALONE.search(line)
        if m2:
            w = _to_float(m2.group(1))
            if w and 3.0 <= w <= 80.0:
                return w
    return None


_MERGED_FIELDS = (
    "yapi_duzeni", "kat_adedi", "emsal_kaks", "taks", "yapi_yuksekligi",
    "yencok", "on_bahce", "yan_bahce", "arka_bahce", "ada_no", "parsel_no",
    "yol_genisligi",
)
_PLAN_NOTU_MAX_CHARS = 1000


_NIZAM_LETTER = {"AYRIK": "A", "BITISIK": "B", "BLOK": "BL", "IKIZ": "İ", "SERBEST": "S"}
_FOLD = str.maketrans({"İ": "I", "ı": "I", "Ş": "S", "ş": "S", "Ç": "C", "ç": "C",
                       "Ğ": "G", "ğ": "G", "Ö": "O", "ö": "O", "Ü": "U", "ü": "U"})


def notation_texts(properties: Dict[str, str]) -> List[str]:
    """A Netcad 8 building-rights / road-width Smart Object as plan-notation text.

    The object stores what the planner typed into its form (``nizam``, ``kat``,
    ``taks``, ``kaks``, ``emsal``, ``hmax`` + ``HmaxType``, ``txtOn``, ``txtYan``,
    ``genislik``). Written back as the notation the plan prints ("A-4",
    "TAKS=0.30", "ÖN=5" ...), it goes through the same parser and the same
    agreement rule as the drawing's loose texts. ``choiceType`` says which pair
    the planner chose: 1 = TAKS/KAKS, 0 = Emsal.
    """
    p = {k: str(v).strip() for k, v in (properties or {}).items() if str(v).strip()}
    out: List[str] = []
    nizam = p.get("nizam", "").upper().translate(_FOLD)
    kat = p.get("kat")
    if nizam in _NIZAM_LETTER and kat:
        out.append(f"{_NIZAM_LETTER[nizam]}-{kat}")
    else:
        if nizam in _NIZAM_LETTER:
            out.append(nizam)
        if kat:
            out.append(f"KAT={kat}")
    choice = p.get("choiceType")
    if choice != "0":
        if "taks" in p:
            out.append(f"TAKS={p['taks']}")
        if "kaks" in p:
            out.append(f"KAKS={p['kaks']}")
    if choice != "1" and "emsal" in p:
        out.append(f"EMSAL={p['emsal']}")
    if "hmax" in p:
        if p.get("HmaxType", "M").upper().translate(_FOLD).startswith("KAT"):
            if not kat:
                out.append(f"KAT={p['hmax']}")
        else:
            out.append(f"HMAX={p['hmax']}")
    elif "yEncok" in p:
        out.append(f"YENCOK={p['yEncok']}")
    if "txtOn" in p:
        out.append(f"ÖN={p['txtOn']}")
    if "txtYan" in p:
        out.append(f"YAN={p['txtYan']}")
    if "genislik" in p:
        out.append(f"YOL={p['genislik']}")
    return out


def parse_zoning_parameters(texts: Iterable[str]) -> ZoningParameters:
    """Parse a collection of text labels into structured zoning parameters.

    Each text is parsed on its own; a parameter is kept only when every text
    that states it agrees. A plan area holding several parcels holds several
    ada/parsel numbers, and a zone with two building blocks may hold "A-3" and
    "A-5": picking whichever text came first would assign a value the area
    does not have. Disagreement leaves the field empty.

    Args:
        texts: An iterable of raw text strings found in or near a parcel/block.

    Returns:
        A populated :class:`ZoningParameters` object.
    """
    merged = ZoningParameters()
    seen: Dict[str, set] = {name: set() for name in _MERGED_FIELDS}
    raw_list: List[str] = []
    for raw in texts:
        if not raw:
            continue
        line = str(raw).strip()
        if not line:
            continue
        if line not in raw_list:
            raw_list.append(line)
        single = _parse_single_text(line)
        for name in _MERGED_FIELDS:
            value = getattr(single, name)
            if value is not None:
                seen[name].add(value)
    for name, values in seen.items():
        if len(values) == 1:
            setattr(merged, name, next(iter(values)))
    # Ada and parcel are one fact: keep the parcel only with its own block.
    if merged.ada_no is None:
        merged.parsel_no = None
    merged.raw_texts = raw_list
    return merged


def _parse_single_text(text: str) -> ZoningParameters:
    """Zoning parameters stated by one text entity."""
    params = ZoningParameters()
    raw_list: List[str] = []

    for raw in (text,):
        if not raw:
            continue
        line = str(raw).strip()
        if not line:
            continue
        raw_list.append(line)

        # Normalize casing for Turkish characters
        upper_line = line.translate(_TR_UPPER_MAP)

        # 1. Nizam + Kat
        if params.yapi_duzeni is None or params.kat_adedi is None:
            m = _RE_NIZAM_KAT.search(upper_line)
            if m:
                nizam_token = m.group(1).upper()
                params.yapi_duzeni = _NIZAM_MAP.get(nizam_token, nizam_token)
                with suppress(ValueError):
                    params.kat_adedi = int(m.group(2))

        # Standalone Kat if not found yet
        if params.kat_adedi is None:
            m = _RE_KAT_STANDALONE.search(upper_line)
            if m:
                val = m.group(1) or m.group(2)
                with suppress(ValueError):
                    params.kat_adedi = int(val)

        # Standalone Nizam if not found yet
        if params.yapi_duzeni is None:
            for token, norm in _NIZAM_MAP.items():
                if len(token) > 1 and re.search(rf"\b{token}\b", upper_line):
                    params.yapi_duzeni = norm
                    break

        # 2. Emsal / KAKS
        if params.emsal_kaks is None:
            m = _RE_EMSAL.search(upper_line)
            if m:
                params.emsal_kaks = _to_float(m.group(1))

        # 3. TAKS
        if params.taks is None:
            m = _RE_TAKS.search(upper_line)
            if m:
                params.taks = _to_float(m.group(1))

        # 4. Yençok / Hmax
        if params.yapi_yuksekligi is None:
            m = _RE_YENCOK.search(upper_line)
            if m:
                h = _to_float(m.group(1))
                if h is not None:
                    params.yapi_yuksekligi = h
                    params.yencok = f"{h:g}m"

        # 5. Setbacks
        if params.on_bahce is None:
            m = _RE_ON_BAHCE.search(upper_line)
            if m:
                params.on_bahce = _to_float(m.group(1))

        if params.yan_bahce is None:
            m = _RE_YAN_BAHCE.search(upper_line)
            if m:
                params.yan_bahce = _to_float(m.group(1))

        if params.arka_bahce is None:
            m = _RE_ARKA_BAHCE.search(upper_line)
            if m:
                params.arka_bahce = _to_float(m.group(1))

        # Check setback triplet e.g. "5/3/3"
        if params.on_bahce is None and params.yan_bahce is None and params.arka_bahce is None:
            m = _RE_SETBACK_TRIPLET.search(upper_line)
            if m:
                v1, v2, v3 = _to_float(m.group(1)), _to_float(m.group(2)), _to_float(m.group(3))
                if v1 and v2 and v3 and all(0.5 <= v <= 30.0 for v in (v1, v2, v3)):
                    params.on_bahce = v1
                    params.yan_bahce = v2
                    params.arka_bahce = v3

        # 6. Ada / Parsel No
        if params.ada_no is None or params.parsel_no is None:
            m_slash = _RE_ADA_PARSEL_SLASH.search(upper_line)
            if m_slash:
                params.ada_no = m_slash.group(1)
                params.parsel_no = m_slash.group(2)
            else:
                m_ada = _RE_ADA_EXPLICIT.search(upper_line)
                if m_ada and params.ada_no is None:
                    params.ada_no = m_ada.group(1)
                m_parsel = _RE_PARSEL_EXPLICIT.search(upper_line)
                if m_parsel and params.parsel_no is None:
                    params.parsel_no = m_parsel.group(1)

        # 7. Yol Genişliği
        if params.yol_genisligi is None:
            m_road = _RE_ROAD_WIDTH_PREFIX.search(upper_line)
            if m_road:
                w = _to_float(m_road.group(1))
                if w and 3.0 <= w <= 80.0:
                    params.yol_genisligi = w
            elif "YOL" in upper_line:
                m_num = _RE_ROAD_WIDTH_STANDALONE.search(upper_line)
                if m_num:
                    w = _to_float(m_num.group(1))
                    if w and 3.0 <= w <= 80.0:
                        params.yol_genisligi = w

    params.raw_texts = raw_list
    return params


# -----------------------------------------------------------------------------
# Spatial Join Engine (Point-in-Polygon & Line Proximity Association)
# -----------------------------------------------------------------------------

# Upper groups whose polygons are boundaries, not plan areas: a plan-approval
# or municipal boundary encloses every text on the sheet, and none of those
# texts is a value *of the boundary*.
_BOUNDARY_UPPER_GROUPS = frozenset(("121000", "122000"))


def is_boundary_tabaka(tabaka: Any) -> bool:
    """True for administrative and planning boundary tabaka (SNR_*, 121000/122000)."""
    if tabaka is None:
        return False
    name = str(tabaka).strip().upper()
    if not name or name == "NULL":
        return False
    if name.startswith(("SNR_", "SNR-")):
        return True
    with suppress(Exception):
        from .plangml_schema import lookup_tabaka
        identity = lookup_tabaka(name)
        if identity is not None:
            return identity.ust_grup_id in _BOUNDARY_UPPER_GROUPS
    return False


def _is_zoning_target(tabaka: Any) -> bool:
    """Zoning values belong to plan areas and blocks — not to boundaries, and
    not to closed contour lines or other survey polygons that merely enclose
    spot heights."""
    if is_boundary_tabaka(tabaka):
        return False
    from .cad_polygonizer import is_plan_area_tabaka
    return is_plan_area_tabaka(None if tabaka is None else str(tabaka))


def assign_zoning_parameters_to_polygons(
    polygon_layer: Any,
    text_points: Sequence[Tuple[float, float, str]],
) -> int:
    """Enrich polygon features with zoning parameters extracted from contained texts.

    Supports both QGIS runtime (:class:`QgsVectorLayer`) and pure headless Python.

    Args:
        polygon_layer: A QgsVectorLayer of polygon geometry, or an object with getFeatures.
        text_points: A list of tuples ``(x, y, text_label)``.

    Returns:
        The count of polygons enriched with zoning parameters.
    """
    if not polygon_layer or not text_points:
        return 0

    # Ensure PlanGML zoning fields exist on the layer
    with suppress(Exception):
        from qgis.core import QgsField  # type: ignore
        from qgis.PyQt.QtCore import QMetaType  # type: ignore

        existing_names = {f.name() for f in polygon_layer.fields()}
        new_fields = []
        schema_specs = [
            ("YapiDuzeni", QMetaType.Type.QString),
            ("KatAdedi", QMetaType.Type.Int),
            ("EmsalKaks", QMetaType.Type.Double),
            ("Taks", QMetaType.Type.Double),
            ("YapiYuksekligi", QMetaType.Type.Double),
            ("Yencok", QMetaType.Type.QString),
            ("OnBahceMesafesi", QMetaType.Type.Double),
            ("YanBahceMesafesi", QMetaType.Type.Double),
            ("ArkaBahceMesafesi", QMetaType.Type.Double),
            ("AdaNo", QMetaType.Type.QString),
            ("ParselNo", QMetaType.Type.QString),
            ("YolGenisligi", QMetaType.Type.Double),
            ("PlanNotu", QMetaType.Type.QString),
            ("EmsalKaksTip", QMetaType.Type.QString),
            ("TaksTip", QMetaType.Type.QString),
            ("YapiYuksekligiTip", QMetaType.Type.QString),
        ]
        for name, qtype in schema_specs:
            if name not in existing_names:
                new_fields.append(QgsField(name, qtype))

        if new_fields:
            polygon_layer.dataProvider().addAttributes(new_fields)
            polygon_layer.updateFields()

    layer_name = (polygon_layer.name() if hasattr(polygon_layer, "name") else "") or ""
    with suppress(Exception):
        from .cad_engine import is_helper_or_noise_layer
        if is_helper_or_noise_layer(layer_name):
            return 0

    # Build spatial index on candidate text points for O(log N) lookup
    point_map = {}
    spatial_index = None
    with suppress(Exception):
        from qgis.core import QgsPointXY, QgsGeometry, QgsSpatialIndex, QgsFeature  # type: ignore
        spatial_index = QgsSpatialIndex()
        for idx, (x, y, txt) in enumerate(text_points):
            if not txt:
                continue
            pt_geom = QgsGeometry.fromPointXY(QgsPointXY(x, y))
            f = QgsFeature(idx)
            f.setGeometry(pt_geom)
            spatial_index.addFeature(f)
            point_map[idx] = (x, y, txt, pt_geom)

    if not point_map:
        return 0

    enriched_count = 0
    with suppress(Exception):
        polygon_layer.startEditing()

    layer_field_names = [f.name() for f in polygon_layer.fields()]
    # The drawing's tabaka: PlanGML-era layers named it uip_tabaka, CAD layers
    # carry it as layer_name. Without one, no feature can be told apart from a
    # contour or a boundary, so nothing is enriched rather than everything.
    tabaka_field = next((f for f in ("uip_tabaka", "layer_name") if f in layer_field_names), None)
    if tabaka_field is None:
        return 0

    for feat in polygon_layer.getFeatures():
        geom = feat.geometry()
        if not geom or geom.isEmpty():
            continue
        if tabaka_field and not _is_zoning_target(feat[tabaka_field]):
            continue

        bbox = geom.boundingBox()
        if spatial_index is not None:
            candidate_ids = spatial_index.intersects(bbox)
        else:
            candidate_ids = [cid for cid, (x, y, _, _) in point_map.items() if bbox.contains(x, y)]

        if not candidate_ids:
            continue

        # One prepared engine per polygon: many point tests against one shape.
        engine = QgsGeometry.createGeometryEngine(geom.constGet())
        engine.prepareGeometry()
        candidate_texts = []
        for cid in candidate_ids:
            x, y, txt, pt_geom = point_map[cid]
            if engine.contains(pt_geom.constGet()):
                candidate_texts.append(txt)

        if not candidate_texts:
            continue

        params = parse_zoning_parameters(candidate_texts)
        if not params.has_any and not params.raw_texts:
            continue

        attr_dict = params.as_attribute_dict()
        for field_name, val in attr_dict.items():
            if val is not None and field_name in layer_field_names:
                feat[field_name] = val

        with suppress(Exception):
            polygon_layer.updateFeature(feat)
        enriched_count += 1

    with suppress(Exception):
        polygon_layer.commitChanges()

    return enriched_count


def assign_road_widths_to_lines(
    line_layer: Any,
    text_points: Sequence[Tuple[float, float, str]],
    max_distance: float = 20.0,
) -> int:
    """Assign road width (YolGenisligi) to road lines based on spatial proximity to width labels.

    Args:
        line_layer: QgsVectorLayer of LineString geometry representing road centerlines or axes.
        text_points: Sequence of (x, y, text_label) tuples from CAD text entities.
        max_distance: Search radius in map units (default 20 meters).

    Returns:
        Number of line features updated with YolGenisligi.
    """
    if not line_layer or not text_points:
        return 0

    # Only process layers whose names indicate roads, streets, corridors or transportation axes
    layer_name = (line_layer.name() if hasattr(line_layer, "name") else "") or ""
    tr_map = str.maketrans({"Ç": "C", "Ğ": "G", "İ": "I", "Ö": "O", "Ş": "S", "Ü": "U"})
    layer_name_clean = layer_name.upper().translate(tr_map)
    road_keywords = ("YOL", "TASIT", "SOKAK", "CADDE", "BULVAR", "KARAYOLU", "GUZERGAH", "AKSI", "GIRIS", "CIKIS")
    if not any(kw in layer_name_clean for kw in road_keywords):
        return 0

    with suppress(Exception):
        from qgis.core import QgsField  # type: ignore
        from qgis.PyQt.QtCore import QMetaType  # type: ignore

        if "YolGenisligi" not in [f.name() for f in line_layer.fields()]:
            line_layer.dataProvider().addAttributes([QgsField("YolGenisligi", QMetaType.Type.Double)])
            line_layer.updateFields()

    width_map = {}
    spatial_index = None
    with suppress(Exception):
        from qgis.core import QgsPointXY, QgsGeometry, QgsSpatialIndex, QgsFeature  # type: ignore
        spatial_index = QgsSpatialIndex()
        for idx, (x, y, txt) in enumerate(text_points):
            w = parse_road_width([txt])
            if w is not None:
                pt_geom = QgsGeometry.fromPointXY(QgsPointXY(x, y))
                f = QgsFeature(idx)
                f.setGeometry(pt_geom)
                spatial_index.addFeature(f)
                width_map[idx] = (x, y, w, pt_geom)

    if not width_map:
        return 0

    enriched = 0
    with suppress(Exception):
        line_layer.startEditing()

    for feat in line_layer.getFeatures():
        geom = feat.geometry()
        if not geom or geom.isEmpty():
            continue

        if spatial_index is not None:
            search_box = geom.boundingBox().buffered(max_distance)
            candidate_ids = spatial_index.intersects(search_box)
        else:
            candidate_ids = list(width_map.keys())

        if not candidate_ids:
            continue

        best_w = None
        min_dist = max_distance + 1.0
        for cid in candidate_ids:
            x, y, w, pt_geom = width_map[cid]
            d = geom.distance(pt_geom)
            if d <= max_distance and d < min_dist:
                min_dist = d
                best_w = w

        if best_w is not None:
            feat["YolGenisligi"] = best_w
            enriched += 1
            with suppress(Exception):
                line_layer.updateFeature(feat)

    with suppress(Exception):
        line_layer.commitChanges()

    return enriched
