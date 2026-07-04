# Changelog - 02gpkg CAD/GIS Converter

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
