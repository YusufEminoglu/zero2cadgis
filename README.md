# 02gpkg: Multi-Format CAD & GIS to GeoPackage Converter

<p align="center">
  <img src="icon.png" width="160" height="160" alt="02gpkg Logo">
</p>

An advanced, high-performance QGIS plugin designed to convert, optimize, and import multiple CAD and GIS drawing formats directly into structured OGC GeoPackage (`.gpkg`) databases. 100% English interface, fully integrated with the PlanX ecosystem.

---

## 🌟 Key Features

* **Multi-Format Processing:** Handles AutoCAD (`.dxf`, `.dwg`), Netcad (`.ncz`), Microstation (`.dgn`), Google Earth (`.kml`, `.kmz`), and ArcGIS File Geodatabase (`.gdb`) formats.
* **Direct GeoPackage Output:** Writes data straight to local sqlite-based `.gpkg` tables, avoiding unstable memory layers and slow disk reads.
* **Collinear Node Simplification:** Automatic thinning algorithm that strips unnecessary points along straight segments to reduce file weight.
* **Closed Loop Topology Builder:** Automatically closes gaps at the ends of open polylines within a customizable distance threshold to create clean polygon rings.
* **Dynamic Styling & Annotation:** Translates original CAD ARGB color matrices into QGIS outline and fill styles, and converts text symbols into buffered, readable map labels.
* **Automatic Database Joins:** Auto-detects table relations and links `@TAB` attribute databases back to geometric drawings.

---

## 🔄 Conversion Workflow

```mermaid
flowchart TD
    A["Source File (.dxf, .dwg, .ncz, .kml, .kmz, .dgn, .gdb)"] --> B{"File Type?"}
    
    B -->|KMZ Archive| C["Unzip to Temp KML"]
    C --> D["OGR Vector Layer Provider"]
    B -->|Other Formats| D
    
    D --> E["CAD Optimization Filters"]
    E --> F["Collinear Simplification"]
    E --> G["Clean Duplicate Nodes"]
    E --> H["Boundary Closure Tool"]
    
    F & G & H --> I["QgsVectorFileWriter Engine"]
    I --> J["Target GeoPackage (.gpkg)"]
    J --> K["Load Layers into QGIS Group Canvas"]
    
    style A fill:#e1f5fe,stroke:#0288d1,stroke-width:2px
    style J fill:#e8f5e9,stroke:#388e3c,stroke-width:2px
    style K fill:#fff8e1,stroke:#f57f17,stroke-width:2px
```

---

## 📊 Supported Formats Comparison

| Format | Extension | Driver Engine | CAD Optimizations | Styling & Labels |
| :--- | :---: | :---: | :---: | :---: |
| **AutoCAD DXF** | `.dxf` | GDAL/OGR DXF | Yes | Colors & Layer Groups |
| **AutoCAD DWG** | `.dwg` | GDAL/OGR (requires dwg2dxf) | Yes | Colors & Layer Groups |
| **Netcad NCZ** | `.ncz` | Custom Binary Parser | Yes | ARGB Colors + Labels + Joins |
| **Google Earth KML**| `.kml` | GDAL/OGR KML | Yes | Default KML Labels |
| **Google Earth KMZ**| `.kmz` | Zip Extractor + OGR KML | Yes | Default KML Labels |
| **Microstation DGN**| `.dgn` | GDAL/OGR DGN | Yes | Layer Styling |
| **ArcGIS Database** | `.gdb` | GDAL/OGR OpenFileGDB | Yes | Full Attributes |

---

## 🛠️ Interface Walkthrough

The interface is accessible via the **02gpkg** toolbar button or under **PlanX > 02gpkg - CAD & GIS Converter**.

### 1. CAD & GIS Converter Tab
Designed for bulk conversions:
1. Select the **Dataset Type** from the dropdown menu.
2. Browse to select your drawing file or GDB directory.
3. Click **Save As...** to define the output `.gpkg` destination path.
4. Set the **Target CRS** (automatically defaults to project projection).
5. Tick conversion rules (simplification, loading to canvas).
6. Press **Convert to GeoPackage**.

### 2. Netcad NCZ Importer Tab
Designed for custom Netcad integration:
1. Browse to select the `.ncz` binary drawing.
2. View drawing metadata (version, native projection, total features).
3. Toggle checkable items in the **CAD Layers** tree to import only selected layers.
4. Define closure tolerance in meters (spinbox).
5. Enable automated labeling and `@TAB` joins.
6. Press **Convert NCZ & Load to Canvas**.

---

## 📂 Installation

### Production Directory Setup
Clone or extract the repository directly to your QGIS plugin pathway:
```bash
# Path target
C:\Users\YE\PyCharmMiscProject\qgis_plugins\zero2gpkg_converter
```
Restart QGIS. Enable the plugin via **Plugins > Manage and Install Plugins...**

---

## ✍️ Ownership and License

* **Developer:** Yusuf Eminoğlu
* **Email:** yusufeminoglu@planx.com
* **Repository:** [YusufEminoglu/zero2gpkg_converter](https://github.com/YusufEminoglu/zero2gpkg_converter)
* **License:** GNU General Public License v2.0 or later (GPL-2.0-or-later)
