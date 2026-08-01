# -*- coding: utf-8 -*-
# Copyright (C) 2026 Yusuf Eminoğlu
# SPDX-License-Identifier: GPL-2.0-or-later
"""crs_detect — work out which CRS a Netcad drawing is actually in.

A Netcad drawing does not store an EPSG code. It stores its own SRS id (for
example ``SRS=7936``, which is not an EPSG code and must never be used as one)
plus a human projection string such as ``ITRF / 3 / Zone 42``. Turkish survey
and planning data is almost always in one of a small, well-known family of
projections, so that string plus a look at the coordinates is enough to name
the CRS exactly.

The two signals answer different questions and both are needed:

* the **projection text** gives the datum — TUREF and ED50 differ by a couple of
  hundred metres over the same ground, and no amount of staring at coordinates
  will tell them apart;
* the **easting magnitude** gives the axis convention — a 6-digit easting is the
  TM form (false easting 500000), an 8-digit one is the 3-degree Gauss-Krüger
  form where the zone number is baked into the easting itself.

Every EPSG code below was read out of the PROJ database rather than recalled,
and each maps to exactly one (datum, central meridian, false easting) triple.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable, List, Optional, Sequence, Tuple

# Central meridians of the Turkish 3-degree zones. Zone index = cm // 3.
TURKISH_CENTRAL_MERIDIANS = (27, 30, 33, 36, 39, 42, 45)

# cm -> EPSG, false easting 500000 (no zone prefix in the easting)
TUREF_TM = {27: 5253, 30: 5254, 33: 5255, 36: 5256, 39: 5257, 42: 5258, 45: 5259}
ED50_TM = {27: 2319, 30: 2320, 33: 2321, 36: 2322, 39: 2323, 42: 2324, 45: 2325}

# cm -> EPSG, false easting zone*1_000_000 + 500000 (zone prefixed easting)
TUREF_GK = {27: 5269, 30: 5270, 33: 5271, 36: 5272, 39: 5273, 42: 5274, 45: 5275}
ED50_GK = {27: 2206, 30: 2207, 33: 2208, 36: 2209, 39: 2210, 42: 2211, 45: 2212}

# UTM zone -> EPSG, for the four zones that cover Turkey
WGS84_UTM = {35: 32635, 36: 32636, 37: 32637, 38: 32638}
ED50_UTM = {35: 23035, 36: 23036, 37: 23037, 38: 23038}

LABELS = {
    **{v: f"TUREF / TM{k}" for k, v in TUREF_TM.items()},
    **{v: f"ED50 / TM{k}" for k, v in ED50_TM.items()},
    **{v: f"TUREF / 3-degree Gauss-Kruger zone {k // 3}" for k, v in TUREF_GK.items()},
    **{v: f"ED50 / 3-degree Gauss-Kruger zone {k // 3}" for k, v in ED50_GK.items()},
    **{v: f"WGS 84 / UTM zone {k}N" for k, v in WGS84_UTM.items()},
    **{v: f"ED50 / UTM zone {k}N" for k, v in ED50_UTM.items()},
    4326: "WGS 84",
}

# Turkey spans roughly 36°N-42°N; a northing outside this band means the
# coordinates are not where the projection says they should be.
TURKEY_NORTHING = (3_800_000.0, 4_800_000.0)
GK_EASTING_FLOOR = 1_000_000.0

_TR_MAP = str.maketrans({"Ç": "C", "Ğ": "G", "İ": "I", "Ö": "O", "Ş": "S", "Ü": "U"})


@dataclass(frozen=True)
class CrsDetection:
    """What we concluded, how sure we are, and why — the reason is shown in the UI."""

    epsg: Optional[int] = None
    label: str = ""
    confidence: str = "none"          # "high" | "medium" | "none"
    reason: str = "No usable CRS hint in the drawing."

    @property
    def authid(self) -> str:
        return f"EPSG:{self.epsg}" if self.epsg else ""

    def __bool__(self) -> bool:
        return self.epsg is not None


def _normalize(text: Optional[str]) -> str:
    if not text:
        return ""
    return str(text).upper().translate(_TR_MAP)


def _datum_of(text: str) -> Optional[str]:
    """TUREF and ITRF are the same realization for our purposes here."""
    if re.search(r"\bED[\s\-_]?50\b|EUROPEAN|HAYFORD|INTERNATIONAL", text):
        return "ED50"
    if re.search(r"TUREF|ITRF|GRS[\s\-_]?80", text):
        return "TUREF"
    if re.search(r"WGS", text):
        return "WGS84"
    return None


def _zone_width_of(text: str) -> Optional[int]:
    if "UTM" in text:
        return 6
    match = re.search(r"(?<![\d.])([36])(?![\d.])", text)
    return int(match.group(1)) if match else None


def _zone_value_of(text: str) -> Optional[int]:
    match = re.search(r"(?:ZONE|DILIM|BOLGE)\D{0,4}(\d{1,2})", text)
    if match:
        return int(match.group(1))
    match = re.search(r"\bTM\s?(\d{2})\b", text)
    return int(match.group(1)) if match else None


def _median(values: Sequence[float]) -> float:
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2.0


def _sample(coordinates: Optional[Iterable[Tuple[float, float]]], limit: int = 4000):
    """Median easting/northing of up to *limit* finite coordinate pairs."""
    xs: List[float] = []
    ys: List[float] = []
    if not coordinates:
        return None, None
    for pair in coordinates:
        try:
            x, y = float(pair[0]), float(pair[1])
        except (TypeError, ValueError, IndexError):
            continue
        if x != x or y != y:          # NaN
            continue
        if x == 0.0 and y == 0.0:
            continue
        xs.append(abs(x))
        ys.append(y)
        if len(xs) >= limit:
            break
    if not xs:
        return None, None
    return _median(xs), _median(ys)


def _cm_from_zone_value(value: int, zone_width: Optional[int]) -> Optional[int]:
    """Netcad writes 'Zone 42' for a central meridian and 'Zone 14' for an index."""
    if zone_width == 6:
        if 35 <= value <= 38:                       # UTM zones covering Turkey
            return 6 * value - 183
        return None
    if value in TURKISH_CENTRAL_MERIDIANS:
        return value
    if 9 <= value <= 15:
        return value * 3
    return None


def _lookup(datum: str, cm: int, gauss_kruger: bool) -> Optional[int]:
    if gauss_kruger:
        table = ED50_GK if datum == "ED50" else TUREF_GK
    else:
        table = ED50_TM if datum == "ED50" else TUREF_TM
    return table.get(cm)


def detect_crs(
    projection_text: Optional[str] = None,
    coordinates: Optional[Iterable[Tuple[float, float]]] = None,
) -> CrsDetection:
    """Name the CRS of a drawing from its projection text and its coordinates.

    ``coordinates`` is any iterable of ``(x, y)`` pairs; only a sample is read.
    Returns a detection with ``epsg`` set only when it can be named with
    confidence — an unsure guess would silently put the data in the wrong place,
    which is worse than leaving the choice to the user.
    """
    text = _normalize(projection_text)
    east, north = _sample(coordinates)

    # Already geographic: both ordinates inside degree range.
    if east is not None and east <= 180.0 and abs(north) <= 90.0:
        return CrsDetection(
            4326, LABELS[4326], "high",
            "Coordinates are in degrees, so the drawing is in geographic WGS 84.")

    gauss_kruger = east is not None and east >= GK_EASTING_FLOOR
    datum = _datum_of(text)
    zone_width = _zone_width_of(text)
    zone_value = _zone_value_of(text)
    cm = _cm_from_zone_value(zone_value, zone_width) if zone_value is not None else None

    # A zone-prefixed easting states the zone outright; trust the data over the text.
    cm_from_easting = None
    if gauss_kruger:
        zone_index = int(east // 1_000_000)
        if 9 <= zone_index <= 15:
            cm_from_easting = zone_index * 3

    notes = []
    if cm_from_easting is not None:
        if cm is not None and cm != cm_from_easting:
            notes.append(
                f"the easting encodes zone {cm_from_easting // 3} while the "
                f"drawing says zone {cm // 3}, so the coordinates were followed")
        cm = cm_from_easting

    if cm is None:
        if datum and zone_value is not None:
            return CrsDetection(
                reason=f"Projection '{projection_text}' is not one of the Turkish "
                       f"3-degree or UTM zones, so the CRS was left unchanged.")
        return CrsDetection(
            reason="The drawing carries no usable projection information, and a "
                   "6-digit easting cannot reveal which zone it belongs to. "
                   "Please pick the CRS yourself.")

    # UTM is a different projection, not a variant of the 3-degree family.
    if zone_width == 6 and not gauss_kruger:
        utm_zone = (cm + 183) // 6
        table = ED50_UTM if datum == "ED50" else WGS84_UTM
        epsg = table.get(utm_zone)
        if epsg is None:
            return CrsDetection(
                reason=f"UTM zone {utm_zone} is outside the zones that cover Turkey.")
        return _finish(epsg, north, "high",
                       f"Read from the drawing's projection '{projection_text}'.",
                       notes)

    if datum is None:
        if not gauss_kruger:
            return CrsDetection(
                reason="The drawing names a zone but no datum, and TUREF and ED50 "
                       "cannot be told apart from the coordinates. Please pick "
                       "the CRS yourself.")
        # The zone is certain from the easting; only the datum is assumed.
        epsg = _lookup("TUREF", cm, True)
        return _finish(
            epsg, north, "medium",
            f"Zone {cm // 3} read from the zone-prefixed easting. The drawing "
            f"names no datum, so the modern TUREF was assumed — switch to the "
            f"ED50 equivalent if this is older data.", notes)

    epsg = _lookup(datum, cm, gauss_kruger)
    if epsg is None:
        return CrsDetection(
            reason=f"No EPSG code exists for {datum} at central meridian {cm}°.")
    return _finish(epsg, north, "high",
                   f"Read from the drawing's projection '{projection_text}'.", notes)


def _finish(epsg, north, confidence, reason, notes) -> CrsDetection:
    if north is not None and not (TURKEY_NORTHING[0] <= north <= TURKEY_NORTHING[1]):
        notes = notes + [
            f"the northing {north:,.0f} falls outside Turkey, so check this before "
            f"exporting"]
        confidence = "medium"
    if notes:
        reason = reason.rstrip(".") + " — " + "; ".join(notes) + "."
    return CrsDetection(epsg, LABELS.get(epsg, ""), confidence, reason)
