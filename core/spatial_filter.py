# -*- coding: utf-8 -*-
# Copyright (C) 2026 Yusuf Eminoğlu
# SPDX-License-Identifier: GPL-2.0-or-later
"""spatial_filter — Fast spatial extent detection and filtering for CAD & GIS files.

Enables selective batch import of datasets (NCZ, DXF, DWG, DGN, KML/KMZ, GDB,
Shapefile, GeoJSON, etc.) whose spatial extents intersect or match a target boundary
(current map canvas extent, selected polygon features, or print layout extents).
Allows scanning hundreds of drawings in seconds without loading or converting
unmatched files into memory.
"""
from __future__ import annotations

import os
from contextlib import suppress
from dataclasses import dataclass, field
from typing import Callable, Iterable, Sequence

from .crs_detect import detect_crs
from .path_utils import has_extension


@dataclass
class ExtentBox:
    """Pure bounding box with min/max bounds."""
    min_x: float
    min_y: float
    max_x: float
    max_y: float

    @property
    def is_valid(self) -> bool:
        return (
            self.max_x >= self.min_x
            and self.max_y >= self.min_y
            and not (self.min_x == 0.0 and self.max_x == 0.0 and self.min_y == 0.0 and self.max_y == 0.0)
        )

    @property
    def width(self) -> float:
        return max(0.0, self.max_x - self.min_x)

    @property
    def height(self) -> float:
        return max(0.0, self.max_y - self.min_y)

    @property
    def center(self) -> tuple[float, float]:
        return ((self.min_x + self.max_x) / 2.0, (self.min_y + self.max_y) / 2.0)

    def intersects(self, other: "ExtentBox") -> bool:
        """Check if two bounding boxes overlap."""
        if not self.is_valid or not other.is_valid:
            return False
        return not (
            self.max_x < other.min_x
            or self.min_x > other.max_x
            or self.max_y < other.min_y
            or self.min_y > other.max_y
        )

    def contains(self, other: "ExtentBox") -> bool:
        """Check if this bounding box completely encloses another."""
        if not self.is_valid or not other.is_valid:
            return False
        return (
            self.min_x <= other.min_x
            and self.max_x >= other.max_x
            and self.min_y <= other.min_y
            and self.max_y >= other.max_y
        )


@dataclass
class ExtentInspectionResult:
    """Inspection outcome for a single file."""
    file_path: str
    format_key: str
    box: ExtentBox
    crs_authid: str = ""
    feature_count: int = 0
    matches: bool = False
    match_reason: str = ""
    error: str = ""

    @property
    def file_name(self) -> str:
        return os.path.basename(self.file_path)

    @property
    def file_size_bytes(self) -> int:
        with suppress(Exception):
            return os.path.getsize(self.file_path)
        return 0

    @property
    def formatted_size(self) -> str:
        size = self.file_size_bytes
        if size < 1024:
            return f"{size} B"
        if size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        return f"{size / (1024 * 1024):.1f} MB"


SUPPORTED_FILTER_EXTENSIONS: tuple[str, ...] = (
    ".ncz",
    ".nca",
    ".dxf",
    ".dwg",
    ".dgn",
    ".kml",
    ".kmz",
    ".shp",
    ".gdb",
    ".geojson",
    ".json",
    ".gml",
    ".sqlite",
    ".db",
    ".gpx",
    ".accdb",
    ".mdb",
    ".csv",
    ".tsv",
)


def discover_files(
    root_path: str,
    extensions: Sequence[str] | None = None,
    recursive: bool = True,
) -> list[str]:
    """Find all supported files in a directory or validate a single file path."""
    if not os.path.exists(root_path):
        return []

    exts = tuple(e.lower() for e in (extensions or SUPPORTED_FILTER_EXTENSIONS))

    # Single file
    if os.path.isfile(root_path):
        if any(root_path.lower().endswith(ext) for ext in exts):
            return [os.path.normpath(root_path)]
        return []

    # FileGDB directory
    if os.path.isdir(root_path) and root_path.lower().endswith(".gdb"):
        return [os.path.normpath(root_path)]

    discovered: list[str] = []
    if recursive:
        for root, dirs, files in os.walk(root_path):
            # Check for .gdb subdirectories
            for d in list(dirs):
                if d.lower().endswith(".gdb"):
                    discovered.append(os.path.normpath(os.path.join(root, d)))
                    dirs.remove(d)  # Don't descend into the .gdb directory
            for f in files:
                if any(f.lower().endswith(ext) for ext in exts):
                    discovered.append(os.path.normpath(os.path.join(root, f)))
    else:
        for item in os.listdir(root_path):
            full = os.path.join(root_path, item)
            if os.path.isdir(full) and item.lower().endswith(".gdb"):
                discovered.append(os.path.normpath(full))
            elif os.path.isfile(full) and any(item.lower().endswith(ext) for ext in exts):
                discovered.append(os.path.normpath(full))

    discovered.sort()
    return discovered


def inspect_ncz_extent(file_path: str, fallback_crs: str = "") -> ExtentInspectionResult:
    """Inspect spatial extent and CRS of a Netcad .ncz or .nca drawing."""
    from .ncz_engine.v2.parser import NczCatalog
    from .netcad_parser import parse_netcad_binary_stream

    format_key = "ncz"
    try:
        with open(file_path, "rb") as handle:
            data = handle.read()

        catalog = NczCatalog(data).index()
        entities = catalog.decode_all()
        if not entities:
            # Fallback to v1 parser if v2 decoded zero entities
            fallback_res = parse_netcad_binary_stream(file_path)
            raw_entities = fallback_res.get("entities", [])
            coords = []
            for e in raw_entities:
                for c in getattr(e, "coordinates", []):
                    coords.append((c.x, c.y))
        else:
            coords = []
            for entity in entities:
                for pt in entity.get("coordinates", []):
                    coords.append((pt["x"], pt["y"]))

        if not coords:
            return ExtentInspectionResult(
                file_path=file_path,
                format_key=format_key,
                box=ExtentBox(0.0, 0.0, 0.0, 0.0),
                error="No coordinates found in drawing",
            )

        min_x = min(p[0] for p in coords)
        max_x = max(p[0] for p in coords)
        min_y = min(p[1] for p in coords)
        max_y = max(p[1] for p in coords)

        # Detect CRS
        epsg_str = catalog.metadata.epsg or ""
        proj_text = catalog.metadata.projection_text or ""
        detected_authid = ""

        if epsg_str and epsg_str.isdigit():
            detected_authid = f"EPSG:{epsg_str}"
        elif epsg_str and "EPSG:" in epsg_str.upper():
            detected_authid = epsg_str.upper()

        if not detected_authid:
            sample = coords[:100]
            detection = detect_crs(proj_text, sample)
            if detection and detection.epsg:
                detected_authid = detection.authid

        final_crs = detected_authid or fallback_crs

        return ExtentInspectionResult(
            file_path=file_path,
            format_key=format_key,
            box=ExtentBox(min_x, min_y, max_x, max_y),
            crs_authid=final_crs,
            feature_count=len(entities) if entities else len(coords),
        )

    except Exception as exc:
        return ExtentInspectionResult(
            file_path=file_path,
            format_key=format_key,
            box=ExtentBox(0.0, 0.0, 0.0, 0.0),
            error=str(exc),
        )


def inspect_ogr_extent(file_path: str, fallback_crs: str = "") -> ExtentInspectionResult:
    """Inspect spatial extent and CRS using GDAL/OGR."""
    format_key = os.path.splitext(file_path.rstrip("\\/"))[1].lstrip(".").lower() or "gis"
    try:
        from osgeo import ogr
    except ImportError:
        return ExtentInspectionResult(
            file_path=file_path,
            format_key=format_key,
            box=ExtentBox(0.0, 0.0, 0.0, 0.0),
            error="GDAL/OGR is not available in current environment",
        )

    try:
        ds = ogr.Open(file_path)
        if ds is None:
            return ExtentInspectionResult(
                file_path=file_path,
                format_key=format_key,
                box=ExtentBox(0.0, 0.0, 0.0, 0.0),
                error="Could not open dataset with OGR",
            )

        layer_count = ds.GetLayerCount()
        if layer_count == 0:
            return ExtentInspectionResult(
                file_path=file_path,
                format_key=format_key,
                box=ExtentBox(0.0, 0.0, 0.0, 0.0),
                error="Dataset contains 0 layers",
            )

        min_x = float("inf")
        min_y = float("inf")
        max_x = float("-inf")
        max_y = float("-inf")
        detected_crs = ""
        total_features = 0
        found_valid = False

        for idx in range(layer_count):
            layer = ds.GetLayer(idx)
            if layer is None:
                continue

            with suppress(Exception):
                total_features += max(0, layer.GetFeatureCount())

            with suppress(Exception):
                if not detected_crs:
                    srs = layer.GetSpatialRef()
                    if srs is not None:
                        auth_code = srs.GetAuthorityCode(None)
                        auth_name = srs.GetAuthorityName(None) or "EPSG"
                        if auth_code:
                            detected_crs = f"{auth_name}:{auth_code}"

            with suppress(Exception):
                # layer.GetExtent() -> (minX, maxX, minY, maxY)
                ext = layer.GetExtent(force=True)
                if ext and len(ext) == 4:
                    lx_min, lx_max, ly_min, ly_max = ext
                    if lx_max >= lx_min and ly_max >= ly_min and not (lx_min == 0.0 and lx_max == 0.0):
                        min_x = min(min_x, lx_min)
                        max_x = max(max_x, lx_max)
                        min_y = min(min_y, ly_min)
                        max_y = max(max_y, ly_max)
                        found_valid = True

        ds = None

        if not found_valid:
            return ExtentInspectionResult(
                file_path=file_path,
                format_key=format_key,
                box=ExtentBox(0.0, 0.0, 0.0, 0.0),
                error="Dataset layers contain empty or invalid extents",
            )

        # If CRS was not found in OGR header, try Turkish CRS detection
        final_crs = detected_crs
        if not final_crs:
            sample_coords = [((min_x + max_x) / 2.0, (min_y + max_y) / 2.0)]
            detection = detect_crs("", sample_coords)
            if detection and detection.epsg:
                final_crs = detection.authid

        if not final_crs:
            final_crs = fallback_crs

        return ExtentInspectionResult(
            file_path=file_path,
            format_key=format_key,
            box=ExtentBox(min_x, min_y, max_x, max_y),
            crs_authid=final_crs,
            feature_count=total_features,
        )

    except Exception as exc:
        return ExtentInspectionResult(
            file_path=file_path,
            format_key=format_key,
            box=ExtentBox(0.0, 0.0, 0.0, 0.0),
            error=str(exc),
        )


def inspect_file_extent(file_path: str, fallback_crs: str = "") -> ExtentInspectionResult:
    """Inspect spatial extent and CRS of any supported file format."""
    lower = file_path.lower()
    if lower.endswith((".ncz", ".nca")):
        return inspect_ncz_extent(file_path, fallback_crs=fallback_crs)
    return inspect_ogr_extent(file_path, fallback_crs=fallback_crs)


def evaluate_extent_intersection(
    candidate_box: ExtentBox,
    candidate_crs_authid: str,
    target_box: ExtentBox,
    target_crs_authid: str,
    predicate: str = "intersects",
    buffer_distance: float = 0.0,
) -> tuple[bool, str]:
    """Pure coordinate intersection evaluation when QGIS transforms are unavailable."""
    if not candidate_box.is_valid:
        return False, "Candidate box is invalid or empty"
    if not target_box.is_valid:
        return False, "Target box is invalid or empty"

    # If same CRS or no CRS specified, do direct geometric comparison
    buffered_target = ExtentBox(
        min_x=target_box.min_x - buffer_distance,
        min_y=target_box.min_y - buffer_distance,
        max_x=target_box.max_x + buffer_distance,
        max_y=target_box.max_y + buffer_distance,
    )

    if predicate == "within":
        matches = buffered_target.contains(candidate_box)
        reason = "Within target extent" if matches else "Outside target extent"
    else:
        matches = candidate_box.intersects(buffered_target)
        reason = "Intersects target extent" if matches else "Does not intersect target extent"

    return matches, reason


def evaluate_qgis_spatial_match(
    candidate: ExtentInspectionResult,
    target_geometry,  # QgsGeometry
    target_crs,       # QgsCoordinateReferenceSystem
    predicate: str = "intersects",
    buffer_distance: float = 0.0,
) -> tuple[bool, str]:
    """Evaluate spatial match using real QGIS geometry transforms."""
    if not candidate.box.is_valid:
        return False, f"Invalid candidate extent: {candidate.error or 'empty extent'}"

    try:
        from qgis.core import (
            QgsCoordinateReferenceSystem,
            QgsCoordinateTransform,
            QgsGeometry,
            QgsProject,
            QgsRectangle,
        )

        rect = QgsRectangle(
            candidate.box.min_x,
            candidate.box.min_y,
            candidate.box.max_x,
            candidate.box.max_y,
        )
        cand_geom = QgsGeometry.fromRect(rect)

        # Coordinate transformation
        src_crs = (
            QgsCoordinateReferenceSystem(candidate.crs_authid)
            if candidate.crs_authid
            else target_crs
        )

        if src_crs.isValid() and target_crs.isValid() and src_crs != target_crs:
            transform = QgsCoordinateTransform(
                src_crs, target_crs, QgsProject.instance()
            )
            cand_geom.transform(transform)

        eval_target = target_geometry
        if buffer_distance > 0.0:
            eval_target = target_geometry.buffer(buffer_distance, 5)

        if predicate == "within":
            matches = eval_target.contains(cand_geom)
            reason = (
                "Completely within target boundary"
                if matches
                else "Not within target boundary"
            )
        else:
            matches = cand_geom.intersects(eval_target)
            reason = (
                "Intersects target boundary"
                if matches
                else "Outside target boundary"
            )

        return matches, reason

    except Exception as exc:
        return False, f"Spatial evaluation error: {exc}"


def scan_and_filter_files(
    file_paths: Sequence[str],
    target_geometry=None,
    target_crs=None,
    target_box: ExtentBox | None = None,
    predicate: str = "intersects",
    buffer_distance: float = 0.0,
    fallback_crs: str = "",
    progress_callback: Callable[[int, int, str], None] | None = None,
) -> list[ExtentInspectionResult]:
    """Inspect and filter candidate files against the target boundary."""
    results: list[ExtentInspectionResult] = []
    total = len(file_paths)

    for idx, path in enumerate(file_paths):
        if progress_callback:
            progress_callback(idx + 1, total, os.path.basename(path))

        res = inspect_file_extent(path, fallback_crs=fallback_crs)

        if res.box.is_valid:
            if target_geometry is not None and target_crs is not None:
                matches, reason = evaluate_qgis_spatial_match(
                    res,
                    target_geometry,
                    target_crs,
                    predicate=predicate,
                    buffer_distance=buffer_distance,
                )
            elif target_box is not None:
                matches, reason = evaluate_extent_intersection(
                    res.box,
                    res.crs_authid,
                    target_box,
                    fallback_crs,
                    predicate=predicate,
                    buffer_distance=buffer_distance,
                )
            else:
                matches = True
                reason = "No filter applied"
            res.matches = matches
            res.match_reason = reason
        else:
            res.matches = False
            res.match_reason = res.error or "Invalid extent"

        results.append(res)

    return results
