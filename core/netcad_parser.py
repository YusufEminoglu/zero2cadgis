# -*- coding: utf-8 -*-
# Copyright (C) 2026 Yusuf Eminoğlu
# SPDX-License-Identifier: GPL-2.0-or-later
"""Netcad drawing readers built on NCZ Engine v2.

This module is the only place the rest of the plugin touches an NCZ file.
It re-exports the result model so callers have a single import to remember,
and offers two readers over the same engine:

* :class:`NetcadBinaryReader` decodes a whole drawing in one call, for the
  batch converter and the extent scanner.
* :class:`NetcadLazyReader` indexes first — metadata, a per-layer catalog
  and the attribute tables — and materialises geometry only for the layers
  the user actually picked. It also fronts the on-disk index cache, so
  reopening an unchanged drawing costs no block scan at all.

Both report the backend they used through ``parser_backend``. There is one
engine, so that string is constant, but keeping it in the result means a
consumer never has to guess which decoder produced a payload.
"""
from __future__ import annotations

import dataclasses

from .ncz_engine.model import (
    NetcadAttributeRow,
    NetcadAttributeTable,
    NetcadCoordinate,
    NetcadEntity,
    NetcadParseResult,
)
from .ncz_engine.v2 import PARSER_BACKEND_V2, NczCatalog
from .ncz_engine.v2 import cache as ncz_cache
from .ncz_engine.v2 import parse_file as parse_file_v2

__all__ = [
    "NetcadAttributeRow",
    "NetcadAttributeTable",
    "NetcadBinaryReader",
    "NetcadCoordinate",
    "NetcadEntity",
    "NetcadLazyReader",
    "NetcadParseResult",
    "NczLayerSummary",
    "PARSER_BACKEND_V2",
]

# The entity fields that hold coordinate objects rather than plain values.
# The engine writes them as nested dicts, so they are rebuilt on the way in
# while every other field is copied straight across.
_NESTED_ENTITY_FIELDS = frozenset({"coordinates", "interior_rings"})


def _coordinate(payload: dict) -> NetcadCoordinate:
    """One vertex from the engine's ``{"x": …, "y": …, "z": …}`` form."""
    return NetcadCoordinate(
        x=payload["x"], y=payload["y"], z=payload.get("z", 0.0))


class NetcadBinaryReader:
    """Whole-drawing decoder: a file path in, a parse result out."""

    def __init__(self, file_path: str):
        self.file_path = file_path

    def parse(self) -> NetcadParseResult:
        """Decode every geometry record in the drawing."""
        payload = parse_file_v2(self.file_path)
        return self._result_from_payload(
            payload, payload.get("parser_backend", PARSER_BACKEND_V2))

    def _result_from_payload(
            self, payload: dict, backend: str) -> NetcadParseResult:
        return NetcadParseResult(
            entities=[
                self._entity_from_dict(item) for item in payload["entities"]],
            attribute_tables=[
                self._attribute_table_from_dict(item)
                for item in payload.get("attribute_tables", [])],
            layer_names=list(payload["layer_names"]),
            layer_colors=list(payload["layer_colors"]),
            parser_backend=backend,
            version_name=payload.get("version_name", ""),
            epsg=payload.get("epsg", ""),
            projection_text=payload.get("projection_text", ""),
            unsupported_geometry_types={
                int(key): value
                for key, value in dict(
                    payload.get("unsupported_geometry_types", {})).items()},
        )

    def _entity_from_dict(self, payload) -> NetcadEntity:
        """Rebuild one entity from an engine payload dict.

        The engine writes one key per entity field, under the field's own
        name, so the flat fields are read off the dataclass definition
        instead of being transcribed here: adding a field to
        :class:`NetcadEntity` lets the engine start setting it with no edit
        in this file, and the fallbacks are the dataclass's own defaults
        rather than a second copy of them that can drift. Only the nested
        coordinate structures need interpreting.
        """
        values = {}
        for spec in dataclasses.fields(NetcadEntity):
            if spec.name in _NESTED_ENTITY_FIELDS:
                continue
            if spec.name in payload:
                values[spec.name] = payload[spec.name]
            elif spec.default is not dataclasses.MISSING:
                values[spec.name] = spec.default
            elif spec.default_factory is not dataclasses.MISSING:
                values[spec.name] = spec.default_factory()
        values["coordinates"] = [
            _coordinate(item) for item in payload.get("coordinates") or ()]
        values["interior_rings"] = [
            [_coordinate(item) for item in ring]
            for ring in payload.get("interior_rings") or ()]
        # A shallow copy, so a caller that mutates one entity's bag cannot
        # reach back into the payload it came from.
        values["properties"] = dict(values.get("properties") or {})
        return NetcadEntity(**values)

    def _attribute_table_from_dict(self, payload) -> NetcadAttributeTable:
        return NetcadAttributeTable(
            table_ref=payload.get("table_ref", ""),
            rows=[
                NetcadAttributeRow(
                    row_index=item.get("row_index", 0),
                    columns=dict(item.get("columns", {})),
                )
                for item in payload.get("rows", [])
            ],
        )


class NczLayerSummary:
    """One CAD layer as seen before geometry is decoded."""

    __slots__ = ("layer_code", "layer_name", "record_count", "families")

    def __init__(self, layer_code: int, layer_name: str,
                 record_count: int, families):
        self.layer_code = layer_code
        self.layer_name = layer_name
        self.record_count = record_count
        self.families = set(families)

    def to_dict(self) -> dict:
        return {
            "layer_code": self.layer_code,
            "layer_name": self.layer_name,
            "record_count": self.record_count,
            "families": sorted(self.families),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "NczLayerSummary":
        return cls(
            data["layer_code"], data["layer_name"],
            data["record_count"], data.get("families", []))


class NetcadLazyReader:
    """Catalog-backed reader for selective, layer-by-layer NCZ decoding.

    ``index()`` scans the drawing once and records its metadata, a per-layer
    catalog and its attribute-table markers, without decoding geometry.
    ``decode_layers()`` then materialises only the requested layers. An
    unchanged drawing is served straight from the on-disk index cache.
    """

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.backend = ""
        self.from_cache = False
        self._reader = NetcadBinaryReader(file_path)
        self._metadata = None       # DrawingMetadata
        self._summaries: list[NczLayerSummary] = []
        self._attr_dicts: list[dict] = []
        self._catalog: NczCatalog | None = None  # kept on a fresh decode

    def index(self) -> "NetcadLazyReader":
        cached = ncz_cache.load(self.file_path)
        if cached is not None:
            # Cache hit: show the catalog with no file read or block scan.
            self._metadata = cached["metadata"]
            self._summaries = [
                NczLayerSummary.from_dict(s) for s in cached["summaries"]]
            self._attr_dicts = cached["attribute_tables"]
            self.from_cache = True
            self.backend = PARSER_BACKEND_V2
            return self

        with open(self.file_path, "rb") as handle:
            data = handle.read()
        catalog = NczCatalog(data).index()
        self._catalog = catalog
        self._metadata = catalog.metadata
        self._summaries = [
            NczLayerSummary(s.layer_code, s.layer_name,
                            s.record_count, s.families)
            for s in catalog.layer_catalog()
        ]
        self._attr_dicts = catalog.decode_attribute_tables()
        self.backend = PARSER_BACKEND_V2
        ncz_cache.save(
            self.file_path, self._metadata,
            [s.to_dict() for s in self._summaries], self._attr_dicts)
        return self

    @property
    def version_name(self) -> str:
        return self._metadata.version_name if self._metadata else ""

    @property
    def epsg(self) -> str:
        return self._metadata.epsg if self._metadata else ""

    @property
    def projection_text(self) -> str:
        return self._metadata.projection_text if self._metadata else ""

    def layer_summaries(self) -> list[NczLayerSummary]:
        return list(self._summaries)

    def attribute_tables(self) -> list[NetcadAttributeTable]:
        return [
            self._reader._attribute_table_from_dict(table)
            for table in self._attr_dicts
        ]

    def sample_coordinates(self, limit: int = 2000) -> list[tuple[float, float]]:
        """A cheap coordinate sample, for working out the drawing's CRS.

        Decodes the smallest layers only — a few dozen records are plenty to
        read the easting magnitude and the northing band, and this runs while
        the user is still looking at the layer tree.
        """
        summaries = sorted(
            (s for s in self.layer_summaries() if s.record_count > 0),
            key=lambda s: s.record_count)
        wanted, budget = set(), 0
        for summary in summaries:
            wanted.add(summary.layer_code)
            budget += summary.record_count
            if budget >= 50:
                break
        if not wanted:
            return []

        sample: list[tuple[float, float]] = []
        for entity in self.decode_layers(wanted):
            for coordinate in entity.coordinates:
                sample.append((coordinate.x, coordinate.y))
                if len(sample) >= limit:
                    return sample
        return sample

    def decode_layers(self, layer_codes) -> list[NetcadEntity]:
        """Decode only the geometry records in *layer_codes*."""
        wanted = set(layer_codes)
        if not wanted:
            return []
        # On a cache hit the block scan was skipped; read and index the file
        # now (the bytes are needed to decode geometry regardless).
        if self._catalog is None:
            with open(self.file_path, "rb") as handle:
                self._catalog = NczCatalog(handle.read()).index()
        return [
            self._reader._entity_from_dict(payload)
            for payload in self._catalog.decode_layers(wanted)
        ]
