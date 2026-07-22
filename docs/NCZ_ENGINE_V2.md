# NCZ Engine v2 Roadmap

The 02CadGis NCZ engine remains licensed under GPL-2.0-or-later. The v2
implementation under `core/ncz_engine/v2/` is an independent, block-oriented
rewrite written against the format notes in [NCZ_FORMAT.md](NCZ_FORMAT.md)
rather than by adapting the upstream source line by line. Because that format
knowledge ultimately traces back to Jeomatik NCZ Reader, the upstream
copyright, source, license, and 02CadGis modification notices in
[THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md) are retained.

The goal is not to claim an unmeasured blanket speedup. Each improvement must
preserve decoded output and publish a reproducible result for a named
workload.

## Delivery status (v0.4.0)

The v2 engine is **implemented and active**. `NetcadBinaryReader.parse()`
uses v2 by default and falls back to the v1 decoder (reported as
`pure-python (v1 fallback)`) only if v2 raises on a real drawing.

Modules:

- `v2/binary.py` — a bounds-checked `Cursor` over the file buffer; every read
  is clamped and returns a neutral default instead of raising.
- `v2/blocks.py` — declarative block scanner, embedded-record detection, and
  drawing-metadata decoding (layers, colours, MPROJ, TILED_XML/EPSG).
- `v2/geometry.py` — a geometry-decoder registry keyed by numeric type.
- `v2/attributes.py` — `@TAB` marker scan and label/segment/ascii row decode.
- `v2/parser.py` — the `NczCatalog` two-phase orchestrator: a single index
  pass records metadata and record *positions*, then geometry is decoded
  either fully (`decode_all`) or for a chosen set of layer codes
  (`decode_layers`).

Verified parity: `tests/test_ncz_engine_v2.py` builds synthetic NCZ streams
(`tests/ncz_fixtures.py`) exercising every decoder path, both block layouts
(kind 21 and the GIS-shifted kind 22), embedded containers, metadata, and
`@TAB` tables, and asserts field-by-field equality between v1 and v2 output.
An opt-in test additionally asserts bit-exact (`.17g`) parity against a real
drawing named by `ZERO2CADGIS_NCZ_FIXTURE`; this was validated on a
1.2 MiB / 8163-entity municipal Netcad file (60 layers, ITRF/3 zone 42),
which exposed and fixed two v1 behaviours the synthetic corpus missed: a
colour fallback for non-standard per-feature colour codes, and matching v1's
exact `deg * (pi/180)` / `sqrt(x*x + y*y)` float forms in the box decoder.

Measured on a synthetic 1.5 MiB, ~10k-record drawing (CPython, one machine):

| Workload | Result vs v1 full decode |
| --- | ---: |
| v2 cold file-to-full-model | ~1.16x faster, byte-identical output |
| v2 file-to-layer-catalog (no geometry decode) | ~4.5x faster |
| v2 selective decode of 1 of 5 layers | ~3.4x faster |

These are synthetic figures; the aspirational targets below still require a
licensed real-file corpus, and the dock does not yet route imports through
`decode_layers` (next milestone).

## Stable API Contract

The following imports remain supported while the engine is modularized:

- NetcadCoordinate
- NetcadEntity
- NetcadAttributeRow
- NetcadAttributeTable
- NetcadParseResult
- NetcadBinaryReader(path).parse()

The dock must not depend on decoder offsets, block layout, or parser-internal
dictionaries.

As of 0.2.4, the stable result model has been separated into
core/ncz_engine/model.py while core/netcad_parser.py continues to re-export
the existing public names.

## Delivery Milestones

1. **Contract, safety, and baseline** — *done (v0.2.4 / v0.4.0)*
   - Record malformed-input behavior and prevent out-of-bounds reads.
   - Establish deterministic output hashing and repeatable benchmarks.
   - Build a licensed, provenance-tracked NCZ/NCA fixture corpus. *(Synthetic
     corpus in place; a real-file corpus is still outstanding.)*
2. **Modular decoder** — *done (v0.4.0)*
   - Separate result models, bounded binary reads, block iteration, geometry
     decoders, attribute-table decoders, and parser orchestration.
   - Compare normalized v1 and v2 output after every extraction.
3. **Lazy catalog and selective decode** — *done (v0.5.0)*
   - Index layer and record locations without fully materializing geometry.
   - Decode only the layers selected in the dock. The NCZ importer indexes on
     selection (via `NetcadLazyReader`) and calls `decode_layers` for the
     checked layers only; on a real 8163-entity drawing the on-selection cost
     dropped from a full decode (~160 ms) to an index (~15 ms).
4. **Cache and throughput optimization** — *index cache done (v0.6.0)*
   - Add a fingerprinted local index cache with explicit invalidation.
     `core/ncz_engine/v2/cache.py` stores a drawing's metadata, layer
     catalog, and attribute tables as per-user JSON keyed by a
     `(size, mtime_ns)` fingerprint and `CACHE_VERSION`. Reopening an
     unchanged drawing serves the catalog with no file read or block scan
     (~160x faster on a real 1.2 MiB file). Invalidation is automatic on
     file change, plus a dock **Clear cache** button and the
     `ZERO2CADGIS_NCZ_CACHE_DISABLE` env var.
   - Further throughput work (duplicate dictionaries, coordinate copies)
     remains open.

## Performance Gates

All comparisons use the same machine, Python/QGIS build, fixture bytes, and
output digest.

| Workload | Initial v2 target | Stretch target |
| --- | ---: | ---: |
| Cold file-to-full-model | at least 2x faster | profile-driven |
| Peak Python allocation | at most 70% of v1 | at most 50% of v1 |
| File-to-layer-catalog | at least 10x faster | 100x |
| Selective import when at most 5% of records are chosen | at least 10x faster | 100x |
| Valid cached reopen | at least 25x faster | 100x |

A public 100x statement is allowed only for the workload that reaches that
ratio across at least three representative large fixtures with identical
output digests. It must not be presented as a universal full-decode result.

## Benchmark

Run from the plugin workspace root:

~~~powershell
python zero2cadgis/benchmarks/ncz_engine_benchmark.py C:/path/small.ncz C:/path/large.ncz --label v1-baseline --output C:/path/v1-baseline.json
~~~

The report includes fixture SHA-256, runtime details, p50/p95 duration,
MiB/s, entities/s, peak Python allocation, decoded counts, and a normalized
output SHA-256. Timing is invalid if repeated output hashes differ.

## Fixture Policy

No third-party drawing is committed without permission. Each fixture must
have a manifest entry containing:

- file SHA-256 and byte size;
- producer and creation/export steps;
- permission or license;
- covered NCZ version, geometry types, metadata, and @TAB variants;
- expected entity/table counts and canonical JSON/WKT output location.

Required cases include every supported geometry, text and styling, layer
metadata, CRS, MapSheet, SmartObject, attribute tables, multiple NCZ
versions, truncation at block boundaries, invalid lengths, and extreme but
valid coordinate counts.
