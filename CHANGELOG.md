# Changelog - 02gpkg CAD/GIS Converter

## [0.1.1] - 2026-07-04

- Fix OGR temp GPKG action

## [0.1.1] - 2026-07-04

- Fix SQLite locking via OGR merge

## [0.1.1] - 2026-07-04

- Fix SQLite locking on physical GPKG

## [0.1.1] - 2026-07-04

- Fix SQLite database locking

## [0.1.1] - 2026-07-04

- Implement temporary GPKG layer support

## [0.1.1] - 2026-07-04

- Fix QgsPointXY method call

## [0.1.1] - 2026-07-04

- Update metadata details

## [0.1.1] - 2026-07-04

- Update icons to ultra-minimalist

## [0.1.1] - 2026-07-04

- Fix Indentation

## [0.1.1] - 2026-07-04

- Fix TypeError and add temporary memory layer support

## [0.1.1] - 2026-07-04

- Fix AttributeError

## [0.1.1] - 2026-07-04

- Fix NameError

## [0.1.1] - 2026-07-04

- Bump version for metadata updates

## [0.1.0] - 2026-07-04

- Refactored release

## [0.1.0] - 2026-07-04

- Refactored release

## [0.1.0] - 2026-07-04

- Initial release

All notable changes to this project will be documented in this file.

## [0.1.0] - 2026-07-04

### Added
- Initial Release under **Yusuf Eminoğlu** ownership for the PlanX monorepo.
- 100% English multi-tab docked interface (`dialogs/dock.py`).
- **CAD & GIS Converter Tab:**
  - Converts DXF, DWG, KML, KMZ, DGN, and GDB datasets directly into local GeoPackage (`.gpkg`) tables.
  - Automatically unzips KMZ archives to extract internal KML documents.
  - Resolves sublayers recursively using OGR drivers.
- **Netcad NCZ Importer Tab:**
  - Dedicated NCZ binary parser integration.
  - Reads geometry, tables, and version metadata.
  - Custom polyline closure tolerance spinbox.
- **Optimization Tools:** Collinear node simplification and duplicate node cleanup.
- **Styling & Annotation:** Auto ARGB coloring, outline rendering, and text to map label transformation.
- **Relationship Joins:** Automatic join linking for Netcad `@TAB` database tables.
- PlanX-matching premium plugin icon integrated.
