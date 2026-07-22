# Changelog

## [0.4.1] - 2026-07-22

### Fixed

- NCZ Engine v2 now reproduces the v1 decoder bit for bit on real municipal
  drawings, validated against a 1.2 MiB / 8163-entity Netcad file:
  - An entity whose per-feature colour code is non-standard (does not resolve
    directly) now falls back to its layer's colour, matching the v1 post-pass,
    instead of being left without a colour.
  - Box rotation and rectangle-edge math use the same `deg * (pi/180)` and
    `sqrt(x*x + y*y)` forms as v1, removing last-bit floating-point drift in
    box corner coordinates and box height.

### Added

- Opt-in real-file parity test: set `ZERO2CADGIS_NCZ_FIXTURE` to a real
  `.ncz`/`.nca` path to run a bit-exact v1-vs-v2 comparison. No third-party
  drawing is committed.

## [0.4.0] - 2026-07-22

### Added

- **NCZ Engine v2** (`core/ncz_engine/v2/`): an independent, block-oriented
  Netcad decoder written against the documented format layout in
  `docs/NCZ_FORMAT.md`, replacing the monolithic v1 decoder as the active
  engine. It is composed of a bounds-checked binary cursor, a declarative
  block scanner with embedded-record detection, a geometry-decoder registry,
  an `@TAB` attribute decoder, and a two-phase orchestrator (`NczCatalog`).
- **Lazy layer catalog and selective decode**: the v2 engine can index a
  drawing's layers and record positions without decoding geometry, then
  decode only chosen layer codes. On a synthetic 1.5 MiB / ~10k-record
  drawing this builds a layer catalog about 4.5x faster than a full decode
  and decodes a single layer about 3.4x faster.
- New format reference `docs/NCZ_FORMAT.md` and a synthetic NCZ test corpus
  (`tests/ncz_fixtures.py`) covering every geometry type, both block layouts,
  embedded containers, metadata, and attribute tables.

### Changed

- `NetcadBinaryReader.parse()` now uses the v2 engine and falls back to the
  v1 decoder (reported as `pure-python (v1 fallback)`) only if v2 raises on a
  real drawing. v2 is ~1.16x faster than v1 on the synthetic full-decode
  workload with byte-identical output.

### Verified

- Field-by-field v1↔v2 output parity across the full synthetic corpus, plus
  malformed-input safety and selective-decode correctness
  (`tests/test_ncz_engine_v2.py`). Real-QGIS smoke tests pass on QGIS 3.44
  LTR and QGIS 4.

## [0.3.0] - 2026-07-21

### Added

- New import formats in the CAD & GIS Converter: **GML**, **GeoJSON**,
  **SpatiaLite/SQLite**, **GPX**, and **delimited text (CSV/TSV/TXT)**.
- Delimited-text geometry sniffer: delimiter, X/Y (or lon/lat) columns and
  WKT columns are auto-detected, WGS84 is pre-selected for lon/lat data, and
  every detection can be overridden in the new **Delimited Text Geometry**
  card before import.
- **Drag & drop**: drop any supported file onto the dock; the dataset type is
  detected from the extension and Netcad NCZ/NCA files route straight to the
  NCZ importer tab.
- **Pre-conversion layer preview**: after choosing a source, its layers are
  listed with geometry type and feature count, and only checked layers are
  converted.
- Target GeoPackage name is pre-suggested from the source file name, and the
  file dialogs now start from the remembered import/export folders.
- Conversion and cleanup options are remembered across QGIS sessions.

### Changed

- Success and warning notifications moved from blocking pop-ups to the QGIS
  message bar; progress bars now update live per converted layer.
- The converter engine opens each source dataset once, converts only the
  selected layer subset, and reports per-layer progress.
- GML/GeoJSON sources that carry a non-integer `fid` attribute no longer fail
  GeoPackage writing (the primary key is moved to a separate column).
- Field type constants migrated from `QVariant` to `QMetaType.Type` for
  QGIS 4 / Qt6 (PyQt6) compatibility, verified on QGIS 3.44 LTR and QGIS 4.
- The exporter's layer list refreshes automatically when project layers are
  added or removed.

## [0.2.4.1] - 2026-07-17

- Remove the developer-supplied `.bandit` configuration so QGIS Plugin Hub
  scans use the standard security rules without overrides.
- Replace all silent `except/pass` blocks reported by Bandit B110 while
  preserving the existing best-effort QGIS compatibility behavior.

## [0.2.4] - 2026-07-16

- Restore the upstream copyright, source, and GPL-2.0-or-later notices for
  the NCZ implementation derived from Jeomatik NCZ Reader by
  Erdinç Örsan ÜNAL.
- Document the NCZ engine's historical lineage and component scope in the
  README and `THIRD_PARTY_NOTICES.md`.
- Guard short Layer, MPROJ, and LEX.ST2 blocks against out-of-bounds reads.
- Add NCZ parser contract and malformed-input regression tests.
- Add a deterministic NCZ benchmark harness and measurable Engine v2 roadmap.
- Extract the NCZ result model into a modular engine package while preserving
  the existing public imports used by the QGIS dock.

## [0.2.3] - 2026-07-10

- Security hotfix: exclude pytest cache artifacts and resolve Hub-reported Flake8 findings

All notable changes to **02CadGis** are documented here.

## [0.2.2] - 2026-07-10

- Remove the shared top-level "PlanX" QGIS menu registration; the plugin now only adds its dockable-panel toggle icon to its own toolbar, so it no longer piles up in a menu shared with other plugins.
- Remember the last import folder (DXF, KML/KMZ, DGN, GDB, personal geodatabase, Netcad NCZ/NCA) between QGIS sessions, symmetric with the existing remembered export folder.

## [0.2.1] - 2026-07-10

- Remember the last DXF, KML, or KMZ export folder between QGIS sessions.
- Replace opaque white icon padding with a transparent background for clean display on QGIS themes.

## [0.2.0] - 2026-07-04

- Rename plugin package to zero2cadgis and update display name to 02CadGis Universal CAD/GIS Importer

## [0.1.9] - 2026-07-04

- Fix DXF export failure by skipping attribute table creation

## [0.1.8] - 2026-07-04

- Fix scratch layer attributes mapping and dynamic KML options in UI

## [0.1.7] - 2026-07-04

- Move DWG import to future enhancement and keep DXF DGN GDB active

## [0.1.6] - 2026-07-04

- Fix QGIS 4 NCZ geometry preservation

## [0.1.5] - 2026-07-04

- Fix visible checked state for styled checkboxes

## [0.1.4] - 2026-07-04

- Add NCZ batch geometry merge and checkbox visibility fixes

## [0.1.3] - 2026-07-04

- Fix QGIS 3/4 GUI compatibility: pin all widget colours in QSS so the panel reads identically under any host theme (dark QGIS 4 no longer bleeds into combos, labels, tree items)
- Add visible checkbox indicator borders in the Netcad optimization panel.
- Add optional NCZ batch geometry merging by geometry type and CAD layer name while preserving the `source_file` attribute.

All notable changes to 02CadGis are documented here.

## [0.1.2] - 2026-07-04

### Security
- Replaced `xml.etree.ElementTree.parse` in KML GroundOverlay scanning with a dependency-free QGIS/PyQt XML parser path.
- Reject KML documents with `DOCTYPE` declarations before overlay scanning.

### Fixed
- Cleaned Hub-reported flake8 issues across plugin Python files.
- Removed silent exception handling in the Netcad CRS detection path.
## [0.1.1] - 2026-07-04

### Added
- Batch NCZ import for selecting and processing multiple Netcad drawings together.
- Temporary scratch-layer output for CAD/GIS and NCZ import workflows.
- CAD/GIS exporter tab for DXF, KML, and KMZ output from active QGIS vector layers.
- KML/KMZ GroundOverlay extraction to georeferenced GeoTIFF rasters.
- Built-in dock Guide button with an expanded quick-start workflow reference, including detailed Netcad NCZ/NCA import guidance.

### Changed
- Replaced the plugin icon system with a new premium 02CadGis main icon and distinct workflow-specific panel icons.
- Updated metadata to use the canonical `icons/icon.png` path.
- Redesigned the GitHub README with workflow icon cards, clearer format support, installation, Netcad notes, and troubleshooting sections.
- Consolidated repeated 0.1.1 release notes into one coherent entry.

### Fixed
- Fixed first-click dock behavior so the panel opens immediately after creation.
- Fixed case-insensitive handling for output and input extensions such as `.GPKG`, `.GDB`, `.DXF`, `.KML`, and `.KMZ`.
- Fixed temporary import mode so scratch workflows no longer silently write hidden temporary GeoPackages when memory layers are available.
- Fixed polygon closure logic so open polylines are only closed inside tolerance unless the source entity is explicitly closed.
- Fixed triangle NCZ entities so they are treated as closed polygon geometry.
- Reduced SQLite lock risk by keeping the per-layer temporary GeoPackage merge path and cleaning temporary files with `finally`.
- Removed an unsafe vector writer geometry override from the GIS conversion path.

## [0.1.0] - 2026-07-04

### Added
- Initial QGIS plugin release for the PlanX monorepo.
- Docked English interface for CAD/GIS conversion, Netcad NCZ import, and vector export.
- DXF, DWG, KML, KMZ, DGN, GDB, and NCZ input workflows.
- GeoPackage writer integration, CAD cleanup, styling, labels, geometry metrics, and `@TAB` joins.
