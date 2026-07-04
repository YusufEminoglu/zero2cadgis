# Changelog

## [0.1.5] - 2026-07-04

- Fix visible checked state for styled checkboxes

## [0.1.4] - 2026-07-04

- Add NCZ batch geometry merge and checkbox visibility fixes

## [0.1.3] - 2026-07-04

- Fix QGIS 3/4 GUI compatibility: pin all widget colours in QSS so the panel reads identically under any host theme (dark QGIS 4 no longer bleeds into combos, labels, tree items)
- Add visible checkbox indicator borders in the Netcad optimization panel.
- Add optional NCZ batch geometry merging by geometry type and CAD layer name while preserving the `source_file` attribute.

All notable changes to 02gpkg are documented here.

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
- Replaced the plugin icon system with a new premium 02gpkg main icon and distinct workflow-specific panel icons.
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