# NCZ Engine v2 Roadmap

The 02CadGis NCZ engine will continue as a GPL-2.0-or-later derivative of
Jeomatik NCZ Reader. Every derived source module must retain the upstream
copyright, source, license, and 02CadGis modification notice described in
[THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md).

The goal is not to claim an unmeasured blanket speedup. Each improvement must
preserve decoded output and publish a reproducible result for a named
workload.

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

1. **Contract, safety, and baseline**
   - Record malformed-input behavior and prevent out-of-bounds reads.
   - Establish deterministic output hashing and repeatable benchmarks.
   - Build a licensed, provenance-tracked NCZ/NCA fixture corpus.
2. **Modular decoder**
   - Separate result models, bounded binary reads, block iteration, geometry
     decoders, attribute-table decoders, and parser orchestration.
   - Compare normalized v1 and v2 output after every extraction.
3. **Lazy catalog and selective decode**
   - Index layer and record locations without fully materializing geometry.
   - Decode only the layers selected in the dock.
4. **Cache and throughput optimization**
   - Add a fingerprinted local index cache with explicit invalidation.
   - Reduce duplicate dictionaries, coordinate copies, and full-file scans.

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
