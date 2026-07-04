# 02gpkg - Import and Convert CAD/KML/GDB Files

A premium, 100% English QGIS plugin for the PlanX ecosystem to seamlessly convert and import multiple CAD and GIS drawing formats into optimized local GeoPackage (`.gpkg`) layers.

## 🚀 Key Features

* **Multi-Format GIS & CAD Support:**
  * **CAD Drawings:** Auto-detects and imports Netcad `.ncz`, AutoCAD `.dxf` / `.dwg`, and Microstation `.dgn` files.
  * **GIS Data:** Handles `.kml` and `.kmz` (auto-unzips and extracts internal KML datasets), and ArcGIS File Geodatabase `.gdb` directories.
* **Geopackage Optimization:** Converts all drawing layers directly into physical GPKG tables, providing massive performance boosts compared to standard memory layers.
* **CAD Cleanup Tools:**
  * **Collinear Node Simplification:** Deletes redundant vertices along straight lines to optimize data size.
  * **Duplicate Geometry Cleanup:** Cleans overlapping vertices and duplicate features.
  * **Auto-Closure Tolerance:** Automatically closes polyline boundaries to valid polygons using a customizable distance threshold.
* **CRS Reprojection:** Integrates native QGIS coordinate reference system selectors to transform incoming drawing coordinates to the target map CRS on the fly.
* **Sembology & Styling:**
  * Imports original ARGB color codes and applies styled outline and fill renderers.
  * Dynamically enables labeling with buffered formats for drawing text features.
* **Database Join:** Automatically matches and joins internal database tables (`@TAB`) back to imported geometric features.

## 📂 Project Structure

```text
zero2gpkg_converter/
  __init__.py            # QGIS class factory entry
  metadata.txt           # QGIS Plugin Hub metadata
  main_plugin.py         # Toolbar and menu hooks
  ncz_binary.py          # NCZ reader wrapper
  ncz_pure.py            # NCZ binary format parser
  icon.png               # PlanX brand matching logo
  README.md              # Documentation (this file)
  CHANGELOG.md           # Version release log
  LICENSE                # GPL-2.0-or-later license
  dialogs/
    __init__.py
    dock.py              # 100% English multi-tab Converter GUI & logic
  icons/
    icon.png
```

## 🛠️ Usage

1. Open QGIS and activate **02gpkg - Import and Convert CAD/KML/GDB Files** from the plugin manager.
2. Click the icon on the toolbar or select **PlanX > 02gpkg - CAD & GIS Converter** in the main menu.
3. Choose the appropriate tab:
   * **CAD & GIS Converter:** Select DXF, DWG, KML, KMZ, DGN, or GDB files, choose target GPKG and parameters, and run conversion.
   * **Netcad NCZ Importer:** Load an NCZ drawing, review sublayers, set tolerances, and load features.

## ✍️ Ownership and License

* **Author:** Yusuf Eminoğlu
* **Email:** yusufeminoglu@planx.com
* **License:** GPL-2.0-or-later
