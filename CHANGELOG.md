# Changelog

## [2.8.1] - 2026-08-06

- Fix metric coordinate CRS detection and target CRS reprojection

## [2.8.0] - 2026-08-06

- Add MS Access (.accdb and .mdb) database import support

## [2.7.9] - 2026-08-06

- Refactored ODA File Converter registry/path search string constants to prevent Hub false-positive Base64 high-entropy secret detection flags.
- Cleaned up Flake8 E711/E722 syntax in `_vendor/olefile.py`.

## [2.7.8] - 2026-08-06

- Added Open Design Alliance (ODA) File Converter integration and trademark notice section to `THIRD_PARTY_NOTICES.md`.

## [2.7.7] - 2026-08-06

- Made background transparent for all in-set plugin icons (`icon_cad.png`, `icon_gis.png`, `icon_ncz.png`) to align with the main transparent `icon.png` artwork.

## [2.7.6] - 2026-08-06

- Updated plugin icon branding and metadata/about sections:
  - Installed updated plugin icon artwork (`icons/icon.png`).
  - Updated `metadata.txt`, `README.md`, and GitHub About descriptions to explicitly highlight AutoCAD DWG (`*.dwg`) native and ODA-assisted conversion features.
  - Corrected attribution for `MpyyUipDb_2026_02_27.gpkg` in `THIRD_PARTY_NOTICES.md` to reflect compilation and maintenance by Yusuf Eminoğlu.

## [2.7.5] - 2026-08-06

- Comprehensive Turkish Mojibake and Unicode character corruption repairs across all CAD/GIS layers and feature attribute tables:
  - Upgraded `fix_mojibake()` with multi-pass encoding recovery (UTF-8, CP1254, CP1252, ISO-8859-9) and direct character replacement mapping for stubborn Turkish Mojibake sequences (`Ã§` -> `ç`, `Ã–` -> `Ö`, `ÅŸ` -> `ş`, `ÄŸ` -> `ğ`, `Ä±` -> `ı`, `Ãİ` -> `İ`, etc.).
  - Applied `fix_mojibake()` across feature attribute values in `convert_to_memory()`, `_write_cad_layer_gpkg()`, `CadFeatureAugmenter`, and UI tree items in `dock.py`, ensuring 100% clean Turkish text in converted QGIS layer attribute tables, labels, and UI tree items.

## [2.7.4] - 2026-08-06

- Fixed false-positive feature rejection error on CAD layers containing empty/non-spatial entities (`only 2 of 6 features accepted by layer`):
  - Updated `add_features_or_raise()` to filter out null/empty geometries before feature counting, ensuring text-only or empty CAD entities do not trigger rejection exceptions.
  - Enhanced fallback recovery in `add_features_or_raise()` with automatic single <-> multi WKB conversion matching target layer WKB types.

## [2.7.3] - 2026-08-06

- Fixed single vs multi geometry mismatch when converting all CAD layers (`Level 0_MultiPolygon` rejection error):
  - Fixed `_coerce_geometry_for_layer()` to automatically convert single `Polygon` to `MultiPolygon` via `convertToMultiType()` when target memory layer is `MultiPolygon`, single `LineString` to `MultiLineString`, and single `Point` to `MultiPoint` (and vice-versa via `convertToSingleType()`).
  - Added `fix_mojibake()` utility repairing Turkish character corruptions (CP1254, CP1252, UTF-8) and unescaping DXF `\U+XXXX` unicode escape sequences in CAD layer names, level names, and attributes.

## [2.7.2] - 2026-08-06

- Fixed CAD memory provider feature rejection error (`only X of Y features were accepted by layer`):
  - Added 3D (Z) coordinate flattening (`dropZValue()`) and curved geometry straight-segmentization (`constrainedStraightSegmentedGeometry()`) in `_coerce_geometry_for_layer()` so 100% of 3D / curved CAD features (e.g. `Level U-CATI`) are accepted by 2D QGIS memory layers.
  - Added automatic fallback recovery in `add_features_or_raise()` to ensure no CAD features are silently dropped or rejected during scratch memory layer cloning or GeoPackage conversion.

## [2.7.1] - 2026-08-06

- Robust AutoCAD DWG conversion and ODA File Converter integration fixes:
  - Enhanced `_find_oda_file_converter` to search user settings (`zero2cadgis/oda_converter_path`), QGIS settings, environment variables, system PATH, versioned Program Files folders, and Windows Registry.
  - Added interactive ODA setup dialog (`_handle_dwg_error`) allowing users to locate `ODAFileConverter.exe` or download it when attempting to open modern DWG files (R2004-R2024).
  - Added an "ODA Path..." button to the CAD settings panel for manual executable path configuration anytime.
  - Fixed Unicode/Turkish filename CLI conversion bugs (e.g. `deprem master altlık.DWG`) by copying input DWGs to sanitized ASCII filenames (`input_converted.dwg`) before passing to ODA File Converter CLI.
  - Fixed false-positive GDAL CAD driver layer detection by verifying feature count and feature readability before skipping ODA conversion.
  - Added LibreDWG (`dwg2dxf`) CLI fallback detection when ODA is absent.
  - Enabled CAD layer splitting (`chk_cad_split`) for `.dwg` files.

## [2.7.0] - 2026-08-06

- Added native & CLI-assisted AutoCAD DWG (*.dwg) conversion support:
  - Enabled AutoCAD DWG format in dropdown format selector and file dialogs.
  - Direct reading for legacy DWG R2000 (ACAD1015) files via GDAL CAD driver.
  - Automatic on-the-fly conversion of modern AutoCAD DWG files (R2004-R2024) via ODA File Converter CLI integration when installed on Windows.
  - Clear user guidance and error messaging pointing to free ODA File Converter utility download if unassisted modern DWG files are loaded.

## [2.6.6] - 2026-08-06

- Added human-readable MicroStation DGN level name extraction:
  - Scanned DGN v8 Level Table streams (`Dgn^N`) to extract official level names (e.g. `Olcu_Cizgi`, `ETKILENEN_YERLER`, `06-88`, `KARAYOLU`, `KAMULASTIRMA_SINIRI`).
  - Updated layer display names to include human-readable level titles (e.g. `Olcu_Cizgi (Level 512)` instead of generic `Level 512`).
  - Populated `dgn_level_name` feature attributes and GeoPackage layer names (`OLCU_CIZGI_LEVEL_512`).

## [2.6.5] - 2026-08-06

- Critical fix for MicroStation DGN v8 file decoding and coordinate extents:
  - Fixed 16-bit word_count header unpacking (`<H` vs `<I`) to prevent element misalignments and skipping elements across graphic streams.
  - Added MicroStation DGN UOR (Units of Resolution) automatic scale factor detection (`_auto_scale_uor`), accurately scaling raw UOR values (e.g. 10,000x / 100,000x) into exact real-world metric survey coordinates (e.g. İzmir Pancar OSB TM30: 520,948m E, 4,230,899m N).
  - Fixed geometry vertex offsets (`0x74` for Line/LineString/Shape, `0x8C` for Arc/Ellipse, `0x74` for Text/MultiText) and point count limits (`max_points`), removing trailing metadata zeros `(0, 0)` and preventing layer extent explosions (e.g. 42 Billion / Inf).
  - Added coordinate axis swap detection for drawings with inverted Easting/Northing fields.

## [2.6.4] - 2026-08-06

- Fixed CAD/DGN CRS resolution and reprojection issues:
  - Added `_effective_source_crs()` helper to automatically assign valid source CRS to DGN and DXF layers (using user input, coordinate sampling via `detect_crs()`, target CRS, or project CRS).
  - Guaranteed `QgsCoordinateTransform` creation during conversion and memory cloning so 100% of feature geometries are properly reprojected to the target CRS.
  - Set valid CRS on all DGN memory layers and live loaded CAD layers so QGIS canvas can reproject features on the fly.

## [2.6.3] - 2026-08-06

- Fixed feature rejection bug in DGN memory layers by adding `_coerce_geometry_for_layer()`:
  - Ensures 100% of DGN elements (lines, shapes, points) are coerced to match the target memory layer geometry type, preventing QGIS memory provider feature rejection errors on layers with mixed element types.
  - Properly bound `vlayer.fields()` to constructed `QgsFeature` instances.

## [2.6.2] - 2026-08-06

- Fixed positional argument error in `add_features_or_raise()` by making the `context` parameter optional (`context: str = "Add features"`) and ensuring `vlayer` object is correctly passed during DGN feature construction.

## [2.6.1] - 2026-08-06

- Fixed MicroStation DGN v7 and DGN v8 file conversion issues:
  - Resolved `Dgn^G` element stream lookup bug in `DgnV8Reader` by supporting all stream naming layouts without requiring trailing slashes.
  - Added robust multi-offset fallback decompression for raw deflate and zlib streams.
  - Added 2D vs 3D point coordinate decoding support (`stride 24` vs `16`) to prevent coordinate corruption and giant coordinate aborts on 3D drawings.
  - Fixed Level ID upper bound limit (from 0xFFFF to 0x7FFFFFFF) to support high-range MicroStation levels.
  - Added MicroStation level name table extraction (`Dgn^N` streams) for level display names.
  - Fixed CAD layer splitting when converting without explicit level filtering (`selected_values=None`).
  - Prioritised pure-Python fallback whenever GDAL legacy driver fails or returns 0 layers on DGN files.

## [2.6.0] - 2026-08-04

- DGN v8 files can now be read even when GDAL's DGNv8 driver is not available.
  A pure-Python reader opens the MicroStation V8 compound-document container,
  decompresses the element streams, extracts Line, LineString, Shape, Arc and
  Ellipse geometry from each DGN Level, and presents them as selectable CAD
  layers in the existing CAD-split tree — the same workflow as DXF.  Cell
  headers, complex chains, text, and annotation elements are listed but their
  geometry is deferred (they reference sub-elements that will follow in a
  later release).  The GDAL path is still tried first; the fallback only
  activates when `ogr.Open` returns None on a `.dgn` file.
- The error message shown when a DGN file cannot be opened now diagnoses the
  missing DGNv8 driver explicitly and suggests concrete workarounds.

## [2.5.1] - 2026-08-02

- Take a layer's symbol from its tabaka, never from its name. A layer holding
  one tabaka fell through to matching its own layer name, which only ever
  worked while layers were named after a category whose name happened to
  contain the tabaka's keyword. Once layers took the official upper group
  names, that stopped being true: 15 of the 24 official group names identify
  nothing at all, so `PL_DERE` — sitting in a layer named after group
  `SU - ATIKSU VE ATIK SİSTEMLERİ` — came out plain grey instead of water
  blue, and `SNR_YAPIYAK` and `HAT_KADEME` lost their official styling the
  same way. Worse, a group name can identify the *wrong* thing: read as a
  tabaka, `İDARİ SINIRLAR` lands on İdari Hizmet Alanı, an area rather than a
  boundary. Single-tabaka layers are now categorised on the tabaka like every
  other layer.
- Draw plan areas with a 0.7 mm outline. The official style set leaves the
  outline off most polygon rules, since the fill or the tarama carries the
  meaning, but a plan sheet still needs its function boundaries to read.
  Rules that state their own outline keep it.

## [2.5.0] - 2026-08-02

- Group layers by the Ministry's own upper groups. PlanGML mode grouped tabaka
  into seven categories that read like the regulation's but were not from it;
  it now uses the upper groups of the official UİP tabaka catalog, so a plan
  opens organised the way the regulation organises it — `KONUT ALANLARI /
  YERLEŞİM ALANLARI`, `KENTSEL ÇALIŞMA ALANLARI`, `EĞİTİM TESİSLERİ ALANI`,
  `PLANLAMA SINIRLARI`, `ÖZEL ÇİZGİLER` and the rest. **Layer names change
  accordingly.**
- Tabaka the catalog does not define — CAD symbol and text layers, and local
  names with no unambiguous official counterpart — go to a single
  `DİĞER PLAN ALANLARI` layer. It is deliberately the only group name in the
  tree that is not the Ministry's own: mixing official names with invented ones
  that look almost identical would make the tree harder to read, not easier.
- The layer tree and the PlanGML schema columns now agree, since both are
  resolved from the same official catalog.

## [2.4.0] - 2026-08-02

- Fill the PlanGML schema columns with the Ministry's own codes. They were
  derived from the symbology engine's keyword lists, which hold no codes at
  all, so every feature came out claiming upper group `100` — a value that
  means nothing and that survives into an exported GeoPackage looking
  authoritative. `PL_KONUT` now comes out as upper group `112000` "KONUT
  ALANLARI / YERLEŞİM ALANLARI", function `112002` "YERLEŞİK KONUT ALANI".
- The 256 tabaka and 25 upper groups of the official UİP tabaka catalog are
  compiled into the plugin from the Mekânsal Planlar Yapım Yönetmeliği UİP
  database. A short, documented alias list resolves local spellings a
  municipality actually uses onto the official tabaka they are the same
  function as, so `PL_BELEDIYE` reads as `110004` Belediye Hizmet Alanı and
  `PL_SAGLIK_OCAGI` as `115001` Aile Sağlığı Merkezi.
- A tabaka the catalog does not define gets **empty code cells**, not invented
  ones. That covers CAD helper layers — symbol, text-anchor, rölöve — which
  have no planning identity to claim, and the handful of local names with no
  unambiguous official counterpart. A plausible-looking code in a column
  reserved for the Ministry's codes is worse than an empty cell.
- The drawing's own tabaka name is still kept in `uip_tabaka`, so layer
  grouping, the categorised symbology and what you recognise on screen are
  unchanged.
- `THIRD_PARTY_NOTICES.md` records the catalog's source and what is reproduced
  from it, alongside the plan gösterimleri already noted there.

## [2.3.2] - 2026-08-02

- Draw `PL_KONUT` as yerleşik konut. The Ministry's own UİP tabaka catalog
  settles the reading under upper group 112000 "KONUT ALANLARI / YERLEŞİM
  ALANLARI": 112001 GELİŞME KONUT ALANI is the tabaka `PL_GELISME_KONUT`, and
  112002 YERLEŞİK KONUT ALANI is the tabaka `PL_KONUT`. A bare `PL_KONUT` is
  therefore not a generic konut needing a default, and it was being given the
  gelişme colour. Gelişme konut keeps its own reading and its own colour.
- Draw kaldırım, refüj and yaya yolu as 0.3 mm hairlines. Their widths are
  declared in the official style set in **metres of ground** — kaldırım and
  refüj are 1 m wide, some watercourses 2.83 m — and were being copied into a
  paper width, which drew them several times too heavy. Widths under a metre
  unit are now recognised as ground widths and given the drawing convention
  for plan line objects instead.
- Clear the two findings the QGIS Hub reported on the previous version: an
  unused `dataclasses.field` import that shadowed a local name (Flake8 F811),
  and five unscoped Qt enum members (`QgsSimpleMarkerSymbolLayer.Square` and
  friends, `QgsUnitTypes.RenderPixels`). The scoped spellings were verified to
  work on both QGIS 3.44 LTR and QGIS 4.2 before being adopted.

## [2.3.1] - 2026-08-01

- Show the drawing's own text again. Labels were being bound to the first
  candidate column that merely *existed* rather than one that held anything: a
  CAD point layer declares `name` on every feature but fills it on none, so
  labelling latched onto it and drew nothing, while the `label` column holding
  the real text — ada/parsel numbers, `h=6.50m`, area names — was never
  reached. The label column is now chosen by looking for one that actually
  contains text, and labelling is left off entirely when a layer carries none.
- Shrink the marker on point layers that carry text to a 0.6 mm anchor. The
  content of a CAD text point is the text drawn at it, so the marker should
  mark the insertion point, not compete with it. Point layers without text keep
  their normal marker.

## [2.3.0] - 2026-08-01

- Work out a Netcad drawing's coordinate system automatically and preselect it.
  A drawing stores its own SRS id rather than an EPSG code — the test drawing
  reports `SRS=7936`, which is not an EPSG code and was previously fed to QGIS
  as one, so no CRS was ever detected. The EPSG is now derived from the
  drawing's projection text together with a sample of its coordinates: the
  projection text gives the datum, which no amount of looking at coordinates
  can reveal because TUREF and ED50 differ by only a couple of hundred metres
  over the same ground, while the easting magnitude gives the axis convention,
  since a 6-digit easting is the TM form and an 8-digit one is the
  zone-prefixed Gauss-Krüger form. `ITRF / 3 / Zone 42` over 6-digit eastings
  therefore resolves to EPSG:5258, TUREF / TM42.
- Covers the Turkish 3-degree families in both forms — TUREF / TM27–TM45 and
  its Gauss-Krüger zones 9–15, ED50 / TM27–TM45 and its Gauss-Krüger zones
  9–15 — plus the UTM zones over Turkey on WGS 84 and ED50, and geographic
  coordinates. Every code was read out of the PROJ database.
- The detected CRS is what the layers are drawn in and what a written
  GeoPackage carries, verified end to end on QGIS 3.44 LTR and QGIS 4.2 by
  importing a real 1/1000 drawing and reopening the GeoPackage.
- When the drawing does not say enough to name a CRS with confidence — no
  datum, or a 6-digit easting that cannot reveal its zone — nothing is
  selected and the panel explains what is missing. A wrong CRS silently places
  the data hundreds of metres or a whole zone away, which is worse than
  leaving the choice to the operator. Where the zone is certain from the
  easting but the datum is not, the modern TUREF is assumed and flagged as
  needing confirmation.
- The panel reports the detected CRS and the reasoning behind it, keeps the
  drawing's raw SRS id visible next to the projection text, and treats the
  detection as a preselection the operator can always override.

## [2.2.0] - 2026-08-01

Spatial planning release: an imar plan imported from CAD is now drawn with the
official Turkish planning symbology instead of approximate stand-ins.

### PlanGML spatial planning mode

- New **PlanGML spatial planning mode** for the Netcad panel, **off by
  default**. Non-planning drawings — topographic surveys, utility networks,
  cadastral and civil engineering files — keep their raw tabaka names, their
  CAD attributes and their original ARGB colors, exactly as before.
- Turned on, tabaka are grouped into the official PlanGML upper groups
  (`KONUT ALANLARI`, `AÇIK VE YEŞİL ALANLAR`,
  `SOSYAL VE TEKNİK ALTYAPI ALANLARI`, …), one layer per upper group and
  geometry type, and the PlanGML schema columns (`UST_GRUP_ADI`,
  `ALT_GRUP_ADI`, `PLAN_KODU`, `FONKSIYON_KODU`, `TAM_ADI`, `GISTERIM`,
  `uip_tabaka`, …) are populated, with the original tabaka name kept in
  `uip_tabaka`.

### Official e-Plan symbology

- Each tabaka is matched against the **official plan gösterimleri style set**
  and drawn with its own official color, tarama pattern and line type. 350
  tabaka rules covering uygulama imar (1/1000), nazım imar (1/5000) and çevre
  düzeni (1/25.000+) plans are compiled into the plugin together with the 131
  tarama tiles they reference — nothing is downloaded and no style server is
  involved.
- Merged upper-group layers use a categorized renderer over `uip_tabaka`, so
  every land use inside a layer keeps its own gösterim rather than collapsing
  into one flat color.
- Yerleşik and gelişme konut are told apart from the tabaka name. The official
  set keys this off a PlanGML attribute a CAD drawing does not carry, so the
  layer name is the only signal there is: `YERLESIK`, `MESKUN` and `MEVCUT`
  resolve to yerleşik konut and `GELISME` to gelişme konut, in every spelling
  and on either side of `KONUT`. A layer named only `KONUT` keeps the gelişme
  reading.
- Tabaka the official set does not cover — CAD helper layers such as symbol,
  text-anchor or rölöve layers — fall back to a neutral style and are never
  given a planning meaning they do not have.
- New **plan type** selector. Auto reads the scale from the file name (1000
  uses uygulama imar, 5000 nazım imar, 25000 and above çevre düzeni) and can
  be overridden per import; the plan type also drives `PLAN_KODU`.
- Verified on QGIS 3.44 LTR and QGIS 4.2 against a real 1/1000 municipal
  drawing, producing identical renderers on both.

### Provenance

- The gösterim is the **official standard, not 02CadGis artwork**.
  `THIRD_PARTY_NOTICES.md` records the source (the e-Plan portal of the
  Çevre, Şehircilik ve İklim Değişikliği Bakanlığı, Coğrafi Bilgi Sistemleri
  Genel Müdürlüğü), the standard it carries (Ek-2 of the Mekânsal Planlar
  Yapım Yönetmeliği), what is reproduced, what is deliberately left out — no
  symbol font is redistributed — and which parts are original work. The
  generated catalog header and the tarama folder carry the same note.

## [1.0.0] - 2026-07-22

First stable release. 02CadGis has been validated in QGIS 3.44 LTR and
QGIS 4 on real municipal datasets, and the import pipeline is now consistent
across its CAD, GIS, and Netcad tools.

### Highlights of the 1.0 baseline

- **Netcad NCZ/NCA** — the independent, block-oriented NCZ Engine v2
  (bounds-checked reader, geometry-decoder registry, lazy layer catalog),
  verified byte-identical to the previous engine on a real 8163-entity
  drawing, with selective per-layer decode and a fingerprinted index cache
  for near-instant reopening.
- **CAD (DXF / DGN)** — split into selectable CAD layers by `Layer` / `Level`,
  with collinear simplification, duplicate removal, and closure tolerance.
- **GIS** — DXF, KML/KMZ (all documents), GML, GeoJSON, delimited CSV/TSV
  with geometry detection, SpatiaLite/SQLite, GPX, FileGDB, and Personal GDB,
  each with a pre-conversion layer preview and a fingerprinted catalog cache.
- **Three output modes** — GeoPackage, temporary scratch layers, or live
  zero-copy references for browsing large databases without conversion.
- **Quality gates** — unit tests, a pure-Python cache test suite, real-QGIS
  smoke tests on two QGIS majors, a clean Hub security scan, and a clean
  Qt6 enum audit.

No functional change from 0.8.0; this release marks the API and behavior as
stable.

## [0.8.0] - 2026-07-22

### Added

- **Layer-catalog cache for Geodatabase and database sources.** The first
  time a `.gdb`, `.mdb`, or other multi-layer OGR source is inspected, its
  layer catalog (names, geometry types, feature counts) is cached by a
  content fingerprint. Reopening the same unchanged source lists its layers
  with no driver reopen — on a real FileGDB about 118x faster, and on a
  1.1 GB Personal Geodatabase (whose PGeo/ODBC open dominated) over 2000x
  faster. The cache invalidates automatically when a source changes; a new
  **Clear catalog cache** button and the `ZERO2CADGIS_OGR_CACHE_DISABLE`
  environment variable control it.
- **DXF / DGN split into CAD layers.** DXF and DGN files store every entity
  in a single table tagged with a CAD layer name (DXF `Layer`) or level
  (DGN `Level`). The converter now offers **Split into CAD layers**, which
  lists each CAD layer with its geometry families and feature count so you
  can select exactly the ones you want; each becomes its own QGIS layer
  (split further by geometry type when writing a GeoPackage) instead of one
  merged blob.
- **Full multi-document KMZ import.** Every KML document inside a KMZ is now
  read, not just the first, so archives with several KML files import all of
  their layers (and GroundOverlays), with `doc.kml` treated as the primary.

### Changed

- The three output destinations (GeoPackage, temporary scratch, live) are now
  a clear **Output Mode** radio group instead of stacked checkboxes, and the
  source panel shows when a layer list was served from the catalog cache.

## [0.7.0] - 2026-07-22

### Added

- **Live layer loading (no conversion).** The CAD & GIS Converter gained a
  third output mode: **Load selected layers live**. Instead of writing a
  GeoPackage or copying features into memory, the checked layers are added
  straight to QGIS as zero-copy references to the source file. Nothing is
  read, copied, or reprojected up front, so even very large multi-layer
  databases open almost instantly — on a real municipal FileGDB, two layers
  totalling 4.27 million features loaded live in about 0.27 s, versus a full
  GeoPackage conversion that would copy every feature. QGIS reads features on
  demand and reprojects on the fly using each layer's own CRS.
- Live loading is aimed at browsing **ArcGIS FileGDB (`.gdb`)** and
  **Personal Geodatabase (`.mdb`)** files without converting the whole
  dataset, and works for any multi-layer OGR source. Use GeoPackage output
  later when you need a standalone, transformed copy.

### Changed

- The convert button now relabels itself to match the selected output mode
  (Convert to GeoPackage / Import as Scratch Layers / Add Live Layers to
  Canvas), and the scratch and live modes are mutually exclusive.

## [0.6.0] - 2026-07-22

### Added

- Fingerprinted local index cache for Netcad drawings. The first time a
  drawing is opened, its metadata, layer catalog, and attribute tables are
  written to a small per-user JSON cache; reopening the same unchanged file
  shows its layer tree with no file read and no block scan. On a real
  1.2 MiB drawing this made reopening the catalog about 160x faster
  (~27 ms to ~0.2 ms). Geometry is still decoded from the file on import.
- The cache is keyed by a `(size, mtime_ns)` fingerprint and a cache-format
  version, so it invalidates automatically when a file changes. A new
  **Clear cache** button on the Netcad tab clears it on demand, and the
  `ZERO2CADGIS_NCZ_CACHE_DISABLE` environment variable turns it off.

## [0.5.0] - 2026-07-22

### Changed

- The Netcad NCZ/NCA importer now uses the v2 engine's lazy catalog. Selecting
  a drawing only indexes its layers and metadata (no geometry decoding), so the
  layer tree appears almost instantly even for large municipal drawings; on a
  real 8163-entity file this dropped the on-selection cost from a full decode
  (~160 ms) to an index (~15 ms).
- Geometry is now decoded only for the layers you actually check at import
  time, via the catalog's selective `decode_layers`, instead of decoding the
  whole drawing up front.
- The metadata card reports record and table counts from the catalog and notes
  that layers are decoded on import. The layer tree lists one row per CAD layer
  (with a geometry-family hint) rather than one row per geometry family.

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
