# -*- coding: utf-8 -*-
# Copyright (C) 2026 Yusuf Eminoğlu
# SPDX-License-Identifier: GPL-2.0-or-later
"""Reproducible performance baseline for the 02CadGis NCZ engine."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import statistics
import sys
import time
import tracemalloc
from datetime import datetime, timezone
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from zero2cadgis.core.netcad_parser import NetcadBinaryReader  # noqa: E402


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _feed(digest, value) -> None:
    digest.update(str(value).encode("utf-8", errors="surrogatepass"))
    digest.update(b"\x1f")


def _result_digest(result) -> str:
    digest = hashlib.sha256()
    for value in (
        result.version_name,
        result.epsg,
        result.projection_text,
        result.layer_names,
        result.layer_colors,
        sorted(result.unsupported_geometry_types.items()),
    ):
        _feed(digest, value)

    for entity in result.entities:
        for value in (
            entity.geometry_kind,
            entity.layer_code,
            entity.layer_name,
            entity.color_argb,
            entity.name,
            entity.label_text,
            entity.text_height,
            entity.rotation_degrees,
            entity.box_width,
            entity.box_height,
            entity.scale,
            entity.grid_x,
            entity.grid_y,
            entity.radius,
            entity.start_angle,
            entity.end_angle,
            entity.is_closed,
        ):
            _feed(digest, value)
        for coordinate in entity.coordinates:
            _feed(digest, format(coordinate.x, ".17g"))
            _feed(digest, format(coordinate.y, ".17g"))
            _feed(digest, format(coordinate.z, ".17g"))

    for table in result.attribute_tables:
        _feed(digest, table.table_ref)
        for row in table.rows:
            _feed(digest, row.row_index)
            for key, value in sorted(row.columns.items()):
                _feed(digest, key)
                _feed(digest, value)
    return digest.hexdigest()


def _percentile_95(values: list[float]) -> float:
    ordered = sorted(values)
    rank = max(1, (len(ordered) * 95 + 99) // 100)
    return ordered[min(rank - 1, len(ordered) - 1)]


def _benchmark_case(path: Path, warmups: int, runs: int) -> dict:
    reader = NetcadBinaryReader(str(path))

    for _ in range(warmups):
        _result_digest(reader.parse())

    elapsed_ms = []
    output_digests = set()
    last_result = None
    for _ in range(runs):
        started = time.perf_counter_ns()
        result = reader.parse()
        elapsed_ms.append((time.perf_counter_ns() - started) / 1_000_000)
        output_digests.add(_result_digest(result))
        last_result = result

    tracemalloc.start()
    memory_result = reader.parse()
    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    output_digests.add(_result_digest(memory_result))

    if len(output_digests) != 1:
        raise RuntimeError(f"Non-deterministic parser output for {path}")
    if last_result is None:
        raise RuntimeError("At least one measured run is required")

    file_size = path.stat().st_size
    p50_ms = statistics.median(elapsed_ms)
    duration_seconds = p50_ms / 1000.0
    table_rows = sum(
        len(table.rows)
        for table in last_result.attribute_tables
    )

    return {
        "path": str(path),
        "file_sha256": _file_sha256(path),
        "file_bytes": file_size,
        "warmups": warmups,
        "runs": runs,
        "p50_ms": round(p50_ms, 6),
        "p95_ms": round(_percentile_95(elapsed_ms), 6),
        "throughput_mib_s": (
            round((file_size / (1024 * 1024)) / duration_seconds, 6)
            if duration_seconds > 0
            else None
        ),
        "entities_per_second": (
            round(len(last_result.entities) / duration_seconds, 3)
            if duration_seconds > 0
            else None
        ),
        "peak_python_mib": round(peak_bytes / (1024 * 1024), 6),
        "entity_count": len(last_result.entities),
        "attribute_table_count": len(last_result.attribute_tables),
        "attribute_row_count": table_rows,
        "output_sha256": next(iter(output_digests)),
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Benchmark the 02CadGis NCZ parser with output parity checks."
        )
    )
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--warmups", type=int, default=2)
    parser.add_argument("--runs", type=int, default=7)
    parser.add_argument("--label", default="")
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.warmups < 0:
        raise ValueError("--warmups must be zero or greater")
    if args.runs < 3:
        raise ValueError("--runs must be at least 3")

    paths = [path.resolve() for path in args.files]
    for path in paths:
        if not path.is_file():
            raise FileNotFoundError(path)

    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "label": args.label,
        "runtime": {
            "python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
            "processor": platform.processor(),
        },
        "cases": [
            _benchmark_case(path, args.warmups, args.runs)
            for path in paths
        ],
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output is not None:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
