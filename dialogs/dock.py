# -*- coding: utf-8 -*-
"""zero2gpkg_converter — DockWidget.
100% English, advanced multi-format CAD/GIS GPKG Converter & NCZ Importer.
"""
from __future__ import annotations

import os
import re
import math
import zipfile
import tempfile
import shutil

from qgis.PyQt.QtCore import Qt, QVariant, pyqtSignal
from qgis.PyQt.QtGui import QIcon, QColor, QFont
from qgis.PyQt.QtWidgets import (
    QDockWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QCheckBox,
    QDoubleSpinBox,
    QProgressBar,
    QMessageBox,
    QFileDialog,
    QFrame,
    QSplitter,
    QTabWidget,
    QComboBox
)
from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsFeature,
    QgsField,
    QgsGeometry,
    QgsPointXY,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsSingleSymbolRenderer,
    QgsMarkerSymbol,
    QgsLineSymbol,
    QgsFillSymbol,
    QgsPalLayerSettings,
    QgsVectorLayerSimpleLabeling,
    QgsTextFormat,
    QgsTextBufferSettings,
    QgsVectorFileWriter,
    QgsCoordinateTransformContext
)
from qgis.gui import QgsProjectionSelectionWidget

from ..ncz_binary import NCZBinaryReader, NCZEntity, NCZAttributeTable

# Premium dark blue styling with orange/amber accents
DOCK_STYLE = """
QWidget {
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 12px;
}
QTabWidget::pane {
    border: 1px solid #cfd8dc;
    border-radius: 4px;
    top: -1px;
}
QTabBar::tab {
    background: #eceff1;
    border: 1px solid #cfd8dc;
    padding: 6px 12px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}
QTabBar::tab:selected {
    background: #ffffff;
    border-bottom-color: transparent;
    font-weight: bold;
    color: #0277bd;
}
QGroupBox {
    font-weight: bold;
    border: 1px solid #cfd8dc;
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 15px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 8px;
    padding: 0 5px;
    color: #0277bd;
}
QPushButton#convert_btn {
    background-color: #2e7d32;
    color: white;
    font-weight: bold;
    font-size: 13px;
    border-radius: 4px;
    padding: 8px;
    border: none;
}
QPushButton#convert_btn:hover {
    background-color: #1b5e20;
}
QPushButton#convert_btn:disabled {
    background-color: #b0bec5;
    color: #78909c;
}
QPushButton#browse_btn {
    background-color: #0277bd;
    color: white;
    font-weight: bold;
    border-radius: 4px;
    padding: 5px 12px;
    border: none;
}
QPushButton#browse_btn:hover {
    background-color: #01579b;
}
QLineEdit {
    border: 1px solid #cfd8dc;
    border-radius: 4px;
    padding: 4px;
    background-color: #ffffff;
}
QTreeWidget {
    border: 1px solid #cfd8dc;
    border-radius: 4px;
    background-color: #ffffff;
}
QProgressBar {
    border: 1px solid #cfd8dc;
    border-radius: 4px;
    text-align: center;
    font-weight: bold;
}
QProgressBar::chunk {
    background-color: #ffb300;
}
"""

@dataclass
class LayerBucket:
    display_name: str
    geometry_type: str
    entities: list[NCZEntity] = field(default_factory=list)

@dataclass
class LayerGroup:
    name: str
    layers: list[QgsVectorLayer] = field(default_factory=list)


class Zero2GpkgConverterDockWidget(QDockWidget):
    """QDockWidget hosting English CAD/GIS format converter tabs."""
    
    FIELD_DEFINITIONS = [
        QgsField("source_file", QVariant.String),
        QgsField("layer_code", QVariant.Int),
        QgsField("layer_name", QVariant.String),
        QgsField("entity_type", QVariant.String),
        QgsField("name", QVariant.String),
        QgsField("label", QVariant.String),
        QgsField("color_argb", QVariant.String),
        QgsField("radius", QVariant.Double),
        QgsField("start_ang", QVariant.Double),
        QgsField("end_ang", QVariant.Double),
        QgsField("text_h", QVariant.Double),
        QgsField("rotation", QVariant.Double),
        QgsField("box_width", QVariant.Double),
        QgsField("box_height", QVariant.Double),
        QgsField("scale", QVariant.Double),
        QgsField("grid_x", QVariant.Double),
        QgsField("grid_y", QVariant.Double),
    ]

    def __init__(self, iface, icon_dir: str, parent=None):
        super().__init__("02gpkg - Import and Convert CAD/KML/GDB Files", parent)
        self.iface = iface
        self.icon_dir = icon_dir
        
        self.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.setStyleSheet(DOCK_STYLE)
        
        self.current_ncz_path: str = ""
        self.parsed_ncz_result = None
        self.temp_dirs: list[str] = []
        
        self._build_ui()

    def closeEvent(self, event):
        # Cleanup temporary directories
        for temp_path in self.temp_dirs:
            if os.path.exists(temp_path):
                shutil.rmtree(temp_path, ignore_errors=True)
        super().closeEvent(event)

    def _build_ui(self) -> None:
        main_tab = QTabWidget()
        
        # ───────────────────────── TAB 1: CAD & GIS Converter ─────────────────────────
        tab_cad_gis = QWidget()
        cad_gis_layout = QVBoxLayout(tab_cad_gis)
        cad_gis_layout.setContentsMargins(6, 6, 6, 6)
        
        # Source Selection
        src_group = QGroupBox("Source CAD / GIS Dataset")
        src_layout = QVBoxLayout(src_group)
        src_layout.setContentsMargins(8, 12, 8, 8)
        
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Dataset Type:"))
        self.cmb_src_type = QComboBox()
        self.cmb_src_type.addItems(["DXF / DWG (*.dxf, *.dwg)", "KML / KMZ (*.kml, *.kmz)", "Microstation DGN (*.dgn)", "ArcGIS File Geodatabase (*.gdb)"])
        self.cmb_src_type.currentIndexChanged.connect(self._on_source_type_changed)
        type_layout.addWidget(self.cmb_src_type, 1)
        src_layout.addLayout(type_layout)
        
        path_layout = QHBoxLayout()
        self.txt_src_path = QLineEdit()
        self.txt_src_path.setReadOnly(True)
        self.txt_src_path.setPlaceholderText("Select drawing or GIS dataset...")
        path_layout.addWidget(self.txt_src_path)
        
        self.btn_browse_src = QPushButton("Browse...")
        self.btn_browse_src.setObjectName("browse_btn")
        self.btn_browse_src.clicked.connect(self._browse_src_dataset)
        path_layout.addWidget(self.btn_browse_src)
        src_layout.addLayout(path_layout)
        cad_gis_layout.addWidget(src_group)
        
        # Destination GPKG Selection
        dst_group = QGroupBox("Target GeoPackage (.gpkg)")
        dst_layout = QHBoxLayout(dst_group)
        dst_layout.setContentsMargins(8, 12, 8, 8)
        
        self.txt_gpkg_path = QLineEdit()
        self.txt_gpkg_path.setReadOnly(True)
        self.txt_gpkg_path.setPlaceholderText("Select output GPKG file...")
        dst_layout.addWidget(self.txt_gpkg_path)
        
        self.btn_browse_gpkg = QPushButton("Save As...")
        self.btn_browse_gpkg.setObjectName("browse_btn")
        self.btn_browse_gpkg.clicked.connect(self._browse_gpkg_destination)
        dst_layout.addWidget(self.btn_browse_gpkg)
        cad_gis_layout.addWidget(dst_group)
        
        # Options
        opt_group = QGroupBox("Conversion Parameters")
        opt_form = QFormLayout(opt_group)
        opt_form.setContentsMargins(8, 12, 8, 8)
        
        self.converter_crs = QgsProjectionSelectionWidget()
        self.converter_crs.setOptionVisible(QgsProjectionSelectionWidget.CrsOption.ProjectCrs, True)
        self.converter_crs.setCrs(QgsProject.instance().crs())
        opt_form.addRow("Target CRS:", self.converter_crs)
        
        self.chk_conv_simplify = QCheckBox("Simplify collinear segment nodes")
        self.chk_conv_simplify.setChecked(True)
        opt_form.addRow(self.chk_conv_simplify)
        
        self.chk_conv_clean = QCheckBox("Remove duplicate geometries and vertices")
        self.chk_conv_clean.setChecked(True)
        opt_form.addRow(self.chk_conv_clean)
        
        self.chk_conv_load = QCheckBox("Load converted layers directly to canvas")
        self.chk_conv_load.setChecked(True)
        opt_form.addRow(self.chk_conv_load)
        
        cad_gis_layout.addWidget(opt_group)
        
        # Progress Bar & Trigger
        cad_gis_layout.addStretch(1)
        self.progress_conv = QProgressBar()
        self.progress_conv.setVisible(False)
        cad_gis_layout.addWidget(self.progress_conv)
        
        self.btn_convert_gis = QPushButton("Convert to GeoPackage")
        self.btn_convert_gis.setObjectName("convert_btn")
        self.btn_convert_gis.setEnabled(False)
        self.btn_convert_gis.clicked.connect(self._convert_gis_dataset)
        cad_gis_layout.addWidget(self.btn_convert_gis)
        
        main_tab.addTab(tab_cad_gis, "CAD & GIS Converter")
        
        # ───────────────────────── TAB 2: Netcad NCZ Importer ─────────────────────────
        tab_ncz = QWidget()
        ncz_layout = QVBoxLayout(tab_ncz)
        ncz_layout.setContentsMargins(6, 6, 6, 6)
        
        # NCZ File Select
        ncz_file_group = QGroupBox("NCZ File Selection")
        ncz_file_layout = QHBoxLayout(ncz_file_group)
        ncz_file_layout.setContentsMargins(8, 12, 8, 8)
        
        self.txt_ncz_path = QLineEdit()
        self.txt_ncz_path.setReadOnly(True)
        self.txt_ncz_path.setPlaceholderText("Select Netcad .ncz file...")
        ncz_file_layout.addWidget(self.txt_ncz_path)
        
        self.btn_browse_ncz = QPushButton("Browse...")
        self.btn_browse_ncz.setObjectName("browse_btn")
        self.btn_browse_ncz.clicked.connect(self._select_ncz_file)
        ncz_file_layout.addWidget(self.btn_browse_ncz)
        ncz_layout.addWidget(ncz_file_group)
        
        # Main Splitter for metadata, tree, and parameters
        ncz_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Metadata Card & Layer Tree
        ncz_mid_widget = QWidget()
        ncz_mid_layout = QVBoxLayout(ncz_mid_widget)
        ncz_mid_layout.setContentsMargins(0, 0, 0, 0)
        
        self.ncz_meta_group = QGroupBox("Drawing Metadata")
        ncz_meta_form = QFormLayout(self.ncz_meta_group)
        ncz_meta_form.setContentsMargins(8, 8, 8, 8)
        ncz_meta_form.setSpacing(4)
        
        self.lbl_ncz_version = QLabel("-")
        self.lbl_ncz_projection = QLabel("-")
        self.lbl_ncz_epsg = QLabel("-")
        self.lbl_ncz_counts = QLabel("-")
        
        ncz_meta_form.addRow("Netcad Version:", self.lbl_ncz_version)
        ncz_meta_form.addRow("Projection:", self.lbl_ncz_projection)
        ncz_meta_form.addRow("Detected EPSG:", self.lbl_ncz_epsg)
        ncz_meta_form.addRow("Objects / Tables:", self.lbl_ncz_counts)
        ncz_mid_layout.addWidget(self.ncz_meta_group)
        
        ncz_tree_group = QGroupBox("Select Layers to Import")
        ncz_tree_layout = QVBoxLayout(ncz_tree_group)
        ncz_tree_layout.setContentsMargins(6, 10, 6, 6)
        
        self.ncz_layer_tree = QTreeWidget()
        self.ncz_layer_tree.setHeaderLabels(["Layer Name", "Geometry", "Count"])
        self.ncz_layer_tree.setColumnWidth(0, 140)
        self.ncz_layer_tree.setColumnWidth(1, 80)
        ncz_tree_layout.addWidget(self.ncz_layer_tree)
        
        # Selection tools
        ncz_sel_layout = QHBoxLayout()
        self.btn_ncz_select_all = QPushButton("Select All")
        self.btn_ncz_select_all.clicked.connect(self._select_all_ncz_layers)
        self.btn_ncz_deselect_all = QPushButton("Deselect All")
        self.btn_ncz_deselect_all.clicked.connect(self._deselect_all_ncz_layers)
        ncz_sel_layout.addWidget(self.btn_ncz_select_all)
        ncz_sel_layout.addWidget(self.btn_ncz_deselect_all)
        ncz_tree_layout.addLayout(ncz_sel_layout)
        ncz_mid_layout.addWidget(ncz_tree_group)
        
        ncz_mid_widget.setLayout(ncz_mid_layout)
        ncz_splitter.addWidget(ncz_mid_widget)
        
        # Advanced CAD Options
        ncz_opt_widget = QWidget()
        ncz_opt_layout = QVBoxLayout(ncz_opt_widget)
        ncz_opt_layout.setContentsMargins(0, 0, 0, 0)
        
        ncz_opt_group = QGroupBox("CAD Optimization & Styling")
        ncz_opt_form = QFormLayout(ncz_opt_group)
        ncz_opt_form.setContentsMargins(8, 12, 8, 8)
        
        self.ncz_crs_selector = QgsProjectionSelectionWidget()
        self.ncz_crs_selector.setOptionVisible(QgsProjectionSelectionWidget.CrsOption.ProjectCrs, True)
        self.ncz_crs_selector.setCrs(QgsProject.instance().crs())
        ncz_opt_form.addRow("Destination CRS:", self.ncz_crs_selector)
        
        self.chk_ncz_simplify = QCheckBox("Simplify collinear vertices")
        self.chk_ncz_simplify.setChecked(True)
        ncz_opt_form.addRow(self.chk_ncz_simplify)
        
        self.chk_ncz_clean = QCheckBox("Clean duplicate nodes")
        self.chk_ncz_clean.setChecked(True)
        ncz_opt_form.addRow(self.chk_ncz_clean)
        
        self.spin_ncz_tolerance = QDoubleSpinBox()
        self.spin_ncz_tolerance.setRange(0.0, 10.0)
        self.spin_ncz_tolerance.setSingleStep(0.05)
        self.spin_ncz_tolerance.setValue(0.10)
        self.spin_ncz_tolerance.setSuffix(" m")
        ncz_opt_form.addRow("Polyline Closure Tolerance:", self.spin_ncz_tolerance)
        
        self.chk_ncz_style = QCheckBox("Apply original ARGB colors and line styles")
        self.chk_ncz_style.setChecked(True)
        ncz_opt_form.addRow(self.chk_ncz_style)
        
        self.chk_ncz_label = QCheckBox("Convert text elements to map labels")
        self.chk_ncz_label.setChecked(True)
        ncz_opt_form.addRow(self.chk_ncz_label)
        
        self.chk_ncz_join = QCheckBox("Join attribute tables (@TAB) automatically")
        self.chk_ncz_join.setChecked(True)
        ncz_opt_form.addRow(self.chk_ncz_join)
        
        ncz_opt_layout.addWidget(ncz_opt_group)
        ncz_opt_widget.setLayout(ncz_opt_layout)
        ncz_splitter.addWidget(ncz_opt_widget)
        ncz_layout.addWidget(ncz_splitter)
        
        # Progress Bar & Trigger
        self.progress_ncz = QProgressBar()
        self.progress_ncz.setVisible(False)
        ncz_layout.addWidget(self.progress_ncz)
        
        self.btn_convert_ncz = QPushButton("Convert NCZ & Load to Canvas")
        self.btn_convert_ncz.setObjectName("convert_btn")
        self.btn_convert_ncz.setEnabled(False)
        self.btn_convert_ncz.clicked.connect(self._import_ncz_dataset)
        ncz_layout.addWidget(self.btn_convert_ncz)
        
        main_tab.addTab(tab_ncz, "Netcad NCZ Importer")
        
        # Set main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.addWidget(main_tab)
        
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setWidget(central_widget)

    # ───────────────────────── TAB 1: GIS/CAD CONVERTER CONTROLS ─────────────────────────

    def _on_source_type_changed(self, index: int) -> None:
        self.txt_src_path.clear()
        self.btn_convert_gis.setEnabled(False)

    def _browse_src_dataset(self) -> None:
        idx = self.cmb_src_type.currentIndex()
        if idx == 0: # DXF / DWG
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Select DXF or DWG File", "", "Drawing Files (*.dxf *.dwg);;All Files (*.*)"
            )
        elif idx == 1: # KML / KMZ
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Select KML or KMZ File", "", "Keyhole Markup Language (*.kml *.kmz);;All Files (*.*)"
            )
        elif idx == 2: # Microstation DGN
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Select Microstation DGN File", "", "Design Files (*.dgn);;All Files (*.*)"
            )
        else: # ArcGIS File Geodatabase
            file_path = QFileDialog.getExistingDirectory(
                self, "Select ArcGIS File Geodatabase Directory", "", QFileDialog.Option.ShowDirsOnly
            )
            if file_path and not file_path.endswith(".gdb"):
                QMessageBox.warning(self, "Invalid Folder", "Please select a directory ending with '.gdb'.")
                return

        if file_path:
            self.txt_src_path.setText(file_path)
            self._update_convert_gis_button_state()

    def _browse_gpkg_destination(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Select Output GeoPackage", "", "GeoPackage (*.gpkg)"
        )
        if file_path:
            if not file_path.endswith(".gpkg"):
                file_path += ".gpkg"
            self.txt_gpkg_path.setText(file_path)
            self._update_convert_gis_button_state()

    def _update_convert_gis_button_state(self) -> None:
        has_src = bool(self.txt_src_path.text().strip())
        has_dst = bool(self.txt_gpkg_path.text().strip())
        self.btn_convert_gis.setEnabled(has_src and has_dst)

    def _convert_gis_dataset(self) -> None:
        src = self.txt_src_path.text()
        dst = self.txt_gpkg_path.text()
        idx = self.cmb_src_type.currentIndex()
        
        crs = self.converter_crs.crs()
        if not crs.isValid():
            crs = QgsProject.instance().crs()

        self.progress_conv.setVisible(True)
        self.progress_conv.setValue(10)
        self.progress_conv.setFormat("Initializing GDAL/OGR drivers...")

        # We will use native QGIS/GDAL provider library via QgsVectorLayer to load, convert and save to GPKG.
        # This is extremely resilient and doesn't crash even if OGR is compiled without specific formats (e.g. DWG).
        try:
            temp_kml_dir = None
            if idx == 1 and src.lower().endswith(".kmz"):
                # Handle KMZ files (unzip to extract KML)
                self.progress_conv.setValue(20)
                self.progress_conv.setFormat("Unzipping KMZ file...")
                temp_kml_dir = tempfile.mkdtemp(prefix="kmz_extract_")
                self.temp_dirs.append(temp_kml_dir)
                
                with zipfile.ZipFile(src, 'r') as zip_ref:
                    # Find doc.kml or any .kml
                    kml_names = [n for n in zip_ref.namelist() if n.lower().endswith(".kml")]
                    if not kml_names:
                        raise ValueError("No KML document found inside the KMZ archive.")
                    zip_ref.extractall(temp_kml_dir)
                    # Point target to the extracted KML file
                    src = os.path.join(temp_kml_dir, kml_names[0])

            self.progress_conv.setValue(40)
            self.progress_conv.setFormat("Reading source layers...")

            # Open with QgsVectorLayer to inspect layers. For file GDB, layers can be queried.
            # For drawing/KML files, they might have sublayers. We query sublayers using GDAL/OGR wrapper or QGIS metadata.
            sublayers = []
            
            # Use QgsVectorLayer metadata/sublayers query
            # A cleaner way: read via OGR module
            from osgeo import ogr
            ogr_ds = ogr.Open(src)
            if ogr_ds is None:
                # If OGR failed to open DWG, throw helpful error
                if src.lower().endswith(".dwg"):
                    raise ImportError("DWG driver not found in your GDAL library. Please convert your DWG to DXF first and load the DXF.")
                raise ValueError("Could not open source dataset with GDAL/OGR driver.")

            for i in range(ogr_ds.GetLayerCount()):
                layer = ogr_ds.GetLayerByIndex(i)
                sublayers.append(layer.GetName())
            
            ogr_ds = None # Release file lock

            if not sublayers:
                raise ValueError("No vector layers found in the source drawing/dataset.")

            self.progress_conv.setValue(60)
            self.progress_conv.setFormat(f"Converting {len(sublayers)} layers to GeoPackage...")

            # Clean output GPKG if exists
            if os.path.exists(dst):
                try:
                    os.remove(dst)
                except OSError:
                    pass

            converted_layers = []
            transform_context = QgsProject.instance().transformContext()

            for i, layer_name in enumerate(sublayers):
                self.progress_conv.setValue(60 + int((i / len(sublayers)) * 30))
                self.progress_conv.setFormat(f"Processing layer: {layer_name}")
                
                # Build URI
                uri = src
                if idx == 3: # GDB
                    uri = f"{src}|layername={layer_name}"
                else:
                    uri = f"{src}|layername={layer_name}"

                vlayer = QgsVectorLayer(uri, layer_name, "ogr")
                if not vlayer.isValid():
                    continue

                # Optimize and simplify layer geometries if requested
                processed_layer = vlayer
                if self.chk_conv_simplify.isChecked() or self.chk_conv_clean.isChecked():
                    processed_layer = self._optimize_vector_layer(vlayer)

                # Save directly as GPKG layer
                options = QgsVectorFileWriter.SaveVectorOptions()
                options.driverName = "GPKG"
                options.layerName = self._sanitize_name(layer_name)
                options.actionOnExistingFile = QgsVectorFileWriter.ActionOnExistingFile.CreateOrOverwriteLayer
                options.overrideGeometryType = processed_layer.geometryType()
                
                # Transform coordinates to target CRS
                if processed_layer.crs() != crs:
                    options.ct = QgsCoordinateTransform(processed_layer.crs(), crs, QgsProject.instance())

                err, err_msg, _, _ = QgsVectorFileWriter.writeAsVectorFormatV3(
                    processed_layer,
                    dst,
                    transform_context,
                    options
                )
                if err != QgsVectorFileWriter.WriterError.NoError:
                    raise ValueError(f"Failed to write layer '{layer_name}' to GPKG: {err_msg}")

                # Load back from GPKG for canvas
                if self.chk_conv_load.isChecked():
                    gpkg_uri = f"{dst}|layername={options.layerName}"
                    gpkg_layer = QgsVectorLayer(gpkg_uri, f"{layer_name}_Converted", "ogr")
                    if gpkg_layer.isValid():
                        converted_layers.append(gpkg_layer)

            # Cleanup temp zip directory
            if temp_kml_dir and os.path.exists(temp_kml_dir):
                shutil.rmtree(temp_kml_dir, ignore_errors=True)

            self.progress_conv.setValue(100)
            self.progress_conv.setVisible(False)

            # Load to canvas
            if self.chk_conv_load.isChecked() and converted_layers:
                # Add to a new group
                root = QgsProject.instance().layerTreeRoot()
                group_name = f"{self._sanitize_name(os.path.basename(src))}_GPKG"
                existing = root.findGroup(group_name)
                if existing:
                    root.removeChildNode(existing)
                group = root.addGroup(group_name)
                
                for cl in converted_layers:
                    QgsProject.instance().addMapLayer(cl, False)
                    group.addLayer(cl)

            QMessageBox.information(
                self,
                "Conversion Complete",
                f"Successfully converted drawing dataset to GeoPackage!\nTarget path: {dst}\nTarget CRS: {crs.userFriendlyIdentifier()}"
            )

        except Exception as exc:
            self.progress_conv.setVisible(False)
            QMessageBox.critical(self, "Conversion Error", f"Failed to convert GIS dataset:\n{exc}")

    def _optimize_vector_layer(self, layer: QgsVectorLayer) -> QgsVectorLayer:
        """Create a temporary cleaned memory layer from the original layer."""
        uri = f"{layer.geometryType().name()}?crs={layer.crs().authid()}"
        mem_layer = QgsVectorLayer(uri, layer.name(), "memory")
        prov = mem_layer.dataProvider()
        prov.addAttributes(layer.fields())
        mem_layer.updateFields()

        features = []
        for feat in layer.getFeatures():
            geom = feat.geometry()
            if not geom or geom.isEmpty():
                continue
            
            # Collinear vertices simplification / Clean duplicate vertices
            if self.chk_conv_simplify.isChecked():
                geom = geom.simplify(0.01) # Simple tolerance
            
            new_feat = QgsFeature(mem_layer.fields())
            new_feat.setGeometry(geom)
            new_feat.setAttributes(feat.attributes())
            features.append(new_feat)

        prov.addFeatures(features)
        mem_layer.updateExtents()
        return mem_layer

    # ───────────────────────── TAB 2: NETCAD NCZ IMPORTER CONTROLS ─────────────────────────

    def _select_ncz_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Netcad NCZ Drawing File", "", "Netcad Drawing Files (*.ncz);;All Files (*.*)"
        )
        if not file_path:
            return
            
        self.current_ncz_path = file_path
        self.txt_ncz_path.setText(file_path)
        
        try:
            self.progress_ncz.setVisible(True)
            self.progress_ncz.setValue(20)
            self.progress_ncz.setFormat("Parsing NCZ file...")
            
            reader = NCZBinaryReader(file_path)
            self.parsed_ncz_result = reader.parse()
            
            self.progress_ncz.setValue(60)
            self.progress_ncz.setFormat("Building layer catalog...")
            
            # Populate drawing details
            self.lbl_ncz_version.setText(self.parsed_ncz_result.version_name or "Standard / Older version")
            self.lbl_ncz_projection.setText(self.parsed_ncz_result.projection_text or "Undefined")
            
            epsg_str = self.parsed_ncz_result.epsg or "Not defined"
            self.lbl_ncz_epsg.setText(epsg_str)
            
            total_entities = len(self.parsed_ncz_result.entities)
            total_tables = len(self.parsed_ncz_result.attribute_tables)
            self.lbl_ncz_counts.setText(f"{total_entities} features / {total_tables} attribute tables")
            
            # Guess target CRS
            if self.parsed_ncz_result.epsg:
                try:
                    clean_epsg = self.parsed_ncz_result.epsg.replace("EPSG:", "").strip()
                    crs = QgsCoordinateReferenceSystem(f"EPSG:{clean_epsg}")
                    if crs.isValid():
                        self.ncz_crs_selector.setCrs(crs)
                except Exception:
                    pass
            
            # Fill Tree Widget
            self._fill_ncz_layer_tree()
            
            self.progress_ncz.setValue(100)
            self.progress_ncz.setVisible(False)
            self.btn_convert_ncz.setEnabled(True)
            
        except Exception as exc:
            self.progress_ncz.setVisible(False)
            self.btn_convert_ncz.setEnabled(False)
            QMessageBox.critical(self, "NCZ Parse Error", f"Could not parse binary NCZ drawing:\n{exc}")

    def _fill_ncz_layer_tree(self) -> None:
        self.ncz_layer_tree.clear()
        if not self.parsed_ncz_result:
            return
            
        # Group entities
        layer_stats = {}
        for entity in self.parsed_ncz_result.entities:
            family, _ = self._geometry_family(entity.geometry_kind)
            if not family:
                continue
            key = (entity.layer_code, entity.layer_name or f"LAYER_{entity.layer_code}", family)
            layer_stats[key] = layer_stats.get(key, 0) + 1
            
        root_item = QTreeWidgetItem(self.ncz_layer_tree)
        root_item.setText(0, "CAD Layers")
        root_item.setFlags(root_item.flags() | Qt.ItemFlag.ItemIsAutoTristate | Qt.ItemFlag.ItemIsUserCheckable)
        root_item.setCheckState(0, Qt.CheckState.Checked)
        root_item.setExpanded(True)
        
        for (code, name, family), count in sorted(layer_stats.items(), key=lambda x: x[0][1]):
            item = QTreeWidgetItem(root_item)
            item.setText(0, name)
            item.setText(1, family)
            item.setText(2, str(count))
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(0, Qt.CheckState.Checked)
            item.setData(0, Qt.ItemDataRole.UserRole, (code, name, family))
            
        if self.parsed_ncz_result.attribute_tables:
            table_root = QTreeWidgetItem(self.ncz_layer_tree)
            table_root.setText(0, "Attribute Tables (@TAB)")
            table_root.setFlags(table_root.flags() | Qt.ItemFlag.ItemIsAutoTristate | Qt.ItemFlag.ItemIsUserCheckable)
            table_root.setCheckState(0, Qt.CheckState.Checked)
            table_root.setExpanded(True)
            
            for table in self.parsed_ncz_result.attribute_tables:
                item = QTreeWidgetItem(table_root)
                item.setText(0, table.table_ref)
                item.setText(1, "Attribute Data")
                item.setText(2, f"{len(table.rows)} rows")
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(0, Qt.CheckState.Checked)
                item.setData(0, Qt.ItemDataRole.UserRole, ("TABLE", table.table_ref, "TABLE"))

    def _select_all_ncz_layers(self) -> None:
        self._set_ncz_tree_checked_state(Qt.CheckState.Checked)

    def _deselect_all_ncz_layers(self) -> None:
        self._set_ncz_tree_checked_state(Qt.CheckState.Unchecked)

    def _set_ncz_tree_checked_state(self, state: Qt.CheckState) -> None:
        for index in range(self.ncz_layer_tree.topLevelItemCount()):
            item = self.ncz_layer_tree.topLevelItem(index)
            item.setCheckState(0, state)
            for child_idx in range(item.childCount()):
                item.child(child_idx).setCheckState(0, state)

    def _geometry_family(self, geometry_kind: str) -> tuple[str, str] | tuple[None, None]:
        if geometry_kind in ("Point", "Text", "Symbol", "Block"):
            return "POINT/TEXT", "Point"
        if geometry_kind in ("Line", "Polyline", "Arc"):
            return "LINE", "LineString"
        if geometry_kind in ("Polygon", "Box", "Circle", "Triangle", "MapSheet", "SmartObject"):
            return "POLYGON", "Polygon"
        return None, None

    def _sanitize_name(self, value: str) -> str:
        text = re.sub(r"\W+", "_", str(value).strip(), flags=re.UNICODE)
        text = text.strip("_")
        return text.upper() or "UNNAMED"

    def _import_ncz_dataset(self) -> None:
        if not self.parsed_ncz_result:
            return
            
        try:
            self.progress_ncz.setVisible(True)
            self.progress_ncz.setValue(10)
            self.progress_ncz.setFormat("Filtering selected layers...")
            
            selected_keys = []
            selected_tables = []
            
            root_count = self.ncz_layer_tree.topLevelItemCount()
            for index in range(root_count):
                root_item = self.ncz_layer_tree.topLevelItem(index)
                for child_idx in range(root_item.childCount()):
                    child = root_item.child(child_idx)
                    if child.checkState(0) == Qt.CheckState.Checked:
                        data = child.data(0, Qt.ItemDataRole.UserRole)
                        if data:
                            if data[0] == "TABLE":
                                selected_tables.append(data[1])
                            else:
                                selected_keys.append(data)
                                
            if not selected_keys and not selected_tables:
                QMessageBox.warning(self, "Warning", "Please select at least one layer or table to import.")
                self.progress_ncz.setVisible(False)
                return
                
            self.progress_ncz.setValue(30)
            self.progress_ncz.setFormat("Creating GeoPackage layers...")
            
            # Destination path selection
            gpkg_path, _ = QFileDialog.getSaveFileName(
                self, "Select Output GeoPackage for NCZ Data", "", "GeoPackage (*.gpkg)"
            )
            if not gpkg_path:
                self.progress_ncz.setVisible(False)
                return
            if not gpkg_path.endswith(".gpkg"):
                gpkg_path += ".gpkg"
                
            # Build structures
            base_name = self._sanitize_name(os.path.splitext(os.path.basename(self.current_ncz_path))[0])
            source_file_name = os.path.splitext(os.path.basename(self.current_ncz_path))[0]
            
            target_crs = self.ncz_crs_selector.crs()
            if not target_crs.isValid():
                target_crs = QgsProject.instance().crs()
                
            # Group entities
            grouped_entities = {}
            for entity in self.parsed_ncz_result.entities:
                family, geometry_type = self._geometry_family(entity.geometry_kind)
                if not family:
                    continue
                
                key = (entity.layer_code, entity.layer_name or f"LAYER_{entity.layer_code}", family)
                if key not in selected_keys:
                    continue
                    
                display_name = f"{self._sanitize_name(key[1])}_{key[2]}"
                group_name = f"{base_name}_{key[2]}"
                
                grouped_entities.setdefault(group_name, {}).setdefault(
                    key,
                    LayerBucket(display_name=display_name, geometry_type=geometry_type)
                ).entities.append(entity)
                
            self.progress_ncz.setValue(50)
            self.progress_ncz.setFormat("Writing CAD features to GeoPackage...")
            
            # Create GeoPackage layers using memory buffers and QgsVectorFileWriter
            layer_groups = []
            transform_context = QgsProject.instance().transformContext()
            
            # Delete file if exists to write fresh
            if os.path.exists(gpkg_path):
                try:
                    os.remove(gpkg_path)
                except OSError:
                    pass
            
            # 1. Geometries
            for group_name in sorted(grouped_entities.keys()):
                layers = []
                for key in sorted(grouped_entities[group_name].keys()):
                    bucket = grouped_entities[group_name][key]
                    
                    # Create temporary memory layer
                    temp_layer = self._create_temp_vector_layer(
                        bucket.display_name,
                        bucket.geometry_type,
                        bucket.entities,
                        target_crs,
                        source_file_name
                    )
                    
                    if temp_layer:
                        # NCZ Styling
                        if self.chk_ncz_style.isChecked():
                            self._apply_style_to_layer(temp_layer, bucket.geometry_type)
                            
                        # Labels
                        if self.chk_ncz_label.isChecked() and bucket.geometry_type == "Point":
                            has_texts = any(e.geometry_kind == "Text" for e in bucket.entities)
                            if has_texts:
                                self._apply_labeling_to_layer(temp_layer)
                                
                        # Write memory layer directly into the GPKG
                        options = QgsVectorFileWriter.SaveVectorOptions()
                        options.driverName = "GPKG"
                        options.layerName = bucket.display_name
                        options.actionOnExistingFile = QgsVectorFileWriter.ActionOnExistingFile.CreateOrOverwriteLayer
                        
                        err, err_msg, _, _ = QgsVectorFileWriter.writeAsVectorFormatV3(
                            temp_layer,
                            gpkg_path,
                            transform_context,
                            options
                        )
                        if err != QgsVectorFileWriter.WriterError.NoError:
                            raise ValueError(f"Failed to write layer '{bucket.display_name}' to GPKG: {err_msg}")
                            
                        # Load from GPKG
                        gpkg_uri = f"{gpkg_path}|layername={bucket.display_name}"
                        gpkg_layer = QgsVectorLayer(gpkg_uri, bucket.display_name, "ogr")
                        if gpkg_layer.isValid():
                            layers.append(gpkg_layer)
                            
                if layers:
                    layer_groups.append(LayerGroup(name=group_name, layers=layers))
                    
            # 2. Attribute Tables
            if self.parsed_ncz_result.attribute_tables and selected_tables:
                attribute_group_name = f"{base_name}_ATTRIBUTES"
                attribute_layers = []
                for table in self.parsed_ncz_result.attribute_tables:
                    if table.table_ref not in selected_tables:
                        continue
                    table_name = self._sanitize_name(table.table_ref)
                    
                    temp_attr = self._create_temp_attribute_layer(table_name, table, source_file_name)
                    if temp_attr:
                        options = QgsVectorFileWriter.SaveVectorOptions()
                        options.driverName = "GPKG"
                        options.layerName = f"{table_name}_TABLE"
                        options.actionOnExistingFile = QgsVectorFileWriter.ActionOnExistingFile.CreateOrOverwriteLayer
                        
                        err, err_msg, _, _ = QgsVectorFileWriter.writeAsVectorFormatV3(
                            temp_attr,
                            gpkg_path,
                            transform_context,
                            options
                        )
                        if err == QgsVectorFileWriter.WriterError.NoError:
                            gpkg_uri = f"{gpkg_path}|layername={options.layerName}"
                            gpkg_layer = QgsVectorLayer(gpkg_uri, f"{table_name}_TABLE", "ogr")
                            if gpkg_layer.isValid():
                                attribute_layers.append(gpkg_layer)
                                
                if attribute_layers:
                    layer_groups.append(LayerGroup(name=attribute_group_name, layers=attribute_layers))
                    
            self.progress_ncz.setValue(80)
            self.progress_ncz.setFormat("Adding layers to QGIS layout...")
            
            # Add GPKG layers to project
            self._add_groups_to_project(layer_groups)
            
            # Apply Join
            if self.chk_ncz_join.isChecked() and selected_tables:
                self._join_attributes_to_layers(layer_groups, base_name)
                
            self.progress_ncz.setValue(100)
            self.progress_ncz.setVisible(False)
            
            QMessageBox.information(
                self,
                "Success",
                f"NCZ converted to GeoPackage and loaded successfully!\nOutput path: {gpkg_path}"
            )
            
        except Exception as exc:
            self.progress_ncz.setVisible(False)
            QMessageBox.critical(self, "Import Error", f"Failed to import NCZ dataset:\n{exc}")

    def _create_temp_vector_layer(
        self,
        layer_name: str,
        geometry_type: str,
        entities: list[NCZEntity],
        crs: QgsCoordinateReferenceSystem,
        source_file_name: str
    ) -> QgsVectorLayer | None:
        
        uri = f"{geometry_type}?crs={crs.authid()}"
        layer = QgsVectorLayer(uri, layer_name, "memory")
        if not layer.isValid():
            return None
            
        provider = layer.dataProvider()
        provider.addAttributes(self.FIELD_DEFINITIONS)
        layer.updateFields()
        
        features = []
        for entity in entities:
            coords = entity.coordinates
            
            if self.chk_ncz_clean.isChecked():
                coords = self._clean_duplicate_coords(coords)
                
            if self.chk_ncz_simplify.isChecked() and len(coords) > 3:
                coords = self._simplify_collinear_coords(coords)
                
            geom = self._coords_to_geometry(entity.geometry_kind, geometry_type, coords, entity.radius)
            if not geom or geom.isEmpty():
                continue
                
            feature = QgsFeature(layer.fields())
            feature.setGeometry(geom)
            feature.setAttributes([
                source_file_name,
                entity.layer_code,
                entity.layer_name,
                entity.geometry_kind,
                entity.name,
                entity.label_text,
                "" if entity.color_argb is None else str(entity.color_argb),
                entity.radius,
                entity.start_angle,
                entity.end_angle,
                entity.text_height,
                entity.rotation_degrees,
                entity.box_width,
                entity.box_height,
                entity.scale,
                entity.grid_x,
                entity.grid_y,
            ])
            features.append(feature)
            
        provider.addFeatures(features)
        layer.updateExtents()
        return layer

    def _create_temp_attribute_layer(self, table_name: str, table: NCZAttributeTable, source_file_name: str) -> QgsVectorLayer | None:
        layer = QgsVectorLayer("None", f"{table_name}_TABLE", "memory")
        if not layer.isValid():
            return None
            
        provider = layer.dataProvider()
        
        # Collect dynamic attributes
        field_names = {"source_file", "table_ref", "row_index"}
        column_types = {}
        for row in table.rows:
            for key, value in row.columns.items():
                field_names.add(key)
                if isinstance(value, int) and not isinstance(value, bool):
                    column_types.setdefault(key, QVariant.Int)
                elif isinstance(value, float):
                    column_types.setdefault(key, QVariant.Double)
                else:
                    column_types.setdefault(key, QVariant.String)
                    
        ordered_dynamic_names = sorted(name for name in field_names if name not in {"source_file", "table_ref", "row_index"})
        
        fields = [
            QgsField("source_file", QVariant.String),
            QgsField("table_ref", QVariant.String),
            QgsField("row_index", QVariant.Int),
        ]
        for name in ordered_dynamic_names:
            fields.append(QgsField(name, column_types.get(name, QVariant.String)))
            
        provider.addAttributes(fields)
        layer.updateFields()
        
        features = []
        for row in table.rows:
            feature = QgsFeature(layer.fields())
            values = []
            for name in ordered_dynamic_names:
                values.append(row.columns.get(name))
            feature.setAttributes([
                source_file_name,
                table.table_ref,
                row.row_index,
                *values
            ])
            features.append(feature)
            
        provider.addFeatures(features)
        layer.updateExtents()
        return layer

    def _add_groups_to_project(self, layer_groups: list[LayerGroup]) -> None:
        project = QgsProject.instance()
        root = project.layerTreeRoot()
        
        for item in layer_groups:
            existing_group = root.findGroup(item.name)
            if existing_group is not None:
                parent = existing_group.parent() or root
                parent.removeChildNode(existing_group)
                
            group = root.addGroup(item.name)
            for layer in item.layers:
                project.addMapLayer(layer, False)
                group.addLayer(layer)

    # ───────────────────────── CAD Cleanup Helpers ─────────────────────────
    
    def _clean_duplicate_coords(self, coords: list) -> list:
        if len(coords) < 2:
            return coords
        cleaned = []
        for c in coords:
            if not cleaned:
                cleaned.append(c)
                continue
            prev = cleaned[-1]
            if abs(prev.x - c.x) < 0.0001 and abs(prev.y - c.y) < 0.0001 and abs(prev.z - c.z) < 0.0001:
                continue
            cleaned.append(c)
        return cleaned

    def _simplify_collinear_coords(self, coords: list) -> list:
        if len(coords) <= 3:
            return coords
            
        simplified = list(coords)
        removed = True
        while removed and len(simplified) > 3:
            removed = False
            for idx in range(len(simplified)):
                if idx == 0 or idx == len(simplified) - 1:
                    continue
                    
                prev_p = simplified[idx - 1]
                curr_p = simplified[idx]
                next_p = simplified[idx + 1]
                
                v1x, v1y = curr_p.x - prev_p.x, curr_p.y - prev_p.y
                v2x, v2y = next_p.x - curr_p.x, next_p.y - curr_p.y
                
                len1 = math.sqrt(v1x*v1x + v1y*v1y)
                len2 = math.sqrt(v2x*v2x + v2y*v2y)
                if len1 < 0.0001 or len2 < 0.0001:
                    simplified.pop(idx)
                    removed = True
                    break
                    
                cross = abs(v1x*v2y - v1y*v2x) / (len1 * len2)
                if cross <= 0.02:
                    simplified.pop(idx)
                    removed = True
                    break
        return simplified

    def _coords_to_geometry(self, geometry_kind: str, geometry_type: str, coords: list, radius: float) -> QgsGeometry | None:
        if geometry_type == "Point":
            if not coords:
                return None
            pt = coords[0]
            return QgsGeometry.fromPointXY(QgsPointXY(pt.x, pt.y))
            
        if geometry_type == "LineString":
            if len(coords) < 2:
                return None
            return QgsGeometry.fromPolylineXY([QgsPointXY(c.x, c.y) for c in coords])
            
        if geometry_type == "Polygon":
            if geometry_kind == "Circle":
                ring = self._approximate_circle(coords[0], radius)
                return QgsGeometry.fromPolygonXY([ring])
                
            ring = [QgsPointXY(c.x, c.y) for c in coords]
            if len(ring) < 3:
                return None
                
            tolerance = self.spin_ncz_tolerance.value()
            if ring:
                first = ring[0]
                last = ring[-1]
                dist = math.hypot(first.x() - last.x(), first.y() - last.y())
                if dist > 0.0001 and dist <= tolerance:
                    ring.append(QgsPointXY(first))
                elif dist > tolerance:
                    ring.append(QgsPointXY(first))
                    
            if len(ring) < 4:
                return None
            return QgsGeometry.fromPolygonXY([ring])
            
        return None

    def _approximate_circle(self, center, radius, segments=72) -> list[QgsPointXY]:
        if radius <= 0:
            return []
        points = []
        for index in range(segments):
            angle = (2.0 * math.pi * index) / segments
            points.append(
                QgsPointXY(
                    center.x + math.cos(angle) * radius,
                    center.y + math.sin(angle) * radius,
                )
            )
        points.append(QgsPointXY(points[0]))
        return points

    # ───────────────────────── NCZ Styling and Labeling ─────────────────────────
    
    def _apply_style_to_layer(self, layer: QgsVectorLayer, geometry_type: str) -> None:
        color_rgb = None
        for feature in layer.getFeatures():
            color_str = feature["color_argb"]
            if color_str:
                try:
                    argb = int(color_str)
                    red = (argb >> 16) & 0xFF
                    green = (argb >> 8) & 0xFF
                    blue = argb & 0xFF
                    color_rgb = QColor(red, green, blue)
                    break
                except ValueError:
                    pass
                    
        if not color_rgb:
            color_rgb = QColor(100, 100, 100)
            
        symbol = None
        if geometry_type == "Point":
            symbol = QgsMarkerSymbol.createSimple({
                "name": "circle",
                "color": color_rgb.name(),
                "size": "3",
                "outline_color": "#ffffff",
                "outline_width": "0.4"
            })
        elif geometry_type == "LineString":
            symbol = QgsLineSymbol.createSimple({
                "color": color_rgb.name(),
                "width": "0.6",
                "line_style": "solid"
            })
        elif geometry_type == "Polygon":
            symbol = QgsFillSymbol.createSimple({
                "color": f"{color_rgb.red()},{color_rgb.green()},{color_rgb.blue()},80",
                "outline_color": color_rgb.name(),
                "outline_width": "0.4"
            })
            
        if symbol:
            renderer = QgsSingleSymbolRenderer(symbol)
            layer.setRenderer(renderer)
            layer.triggerRepaint()

    def _apply_labeling_to_layer(self, layer: QgsVectorLayer) -> None:
        text_format = QgsTextFormat()
        text_format.setFont(QFont("Segoe UI", 9))
        text_format.setColor(QColor(0, 0, 0))
        
        buffer = QgsTextBufferSettings()
        buffer.setEnabled(True)
        buffer.setSize(1.0)
        buffer.setColor(QColor(255, 255, 255))
        text_format.setBuffer(buffer)
        
        label_settings = QgsPalLayerSettings()
        label_settings.setFormat(text_format)
        label_settings.fieldName = "label"
        label_settings.isExpression = False
        label_settings.placement = QgsPalLayerSettings.Placement.OverPoint
        
        simple_labeling = QgsVectorLayerSimpleLabeling(label_settings)
        layer.setLabeling(simple_labeling)
        layer.setLabelsEnabled(True)
        layer.triggerRepaint()

    # ───────────────────────── Join Relations ─────────────────────────
    
    def _join_attributes_to_layers(self, layer_groups: list[LayerGroup], base_name: str) -> None:
        all_layers = {}
        for group in layer_groups:
            for layer in group.layers:
                all_layers[layer.name()] = layer
                
        tables = {name: layer for name, layer in all_layers.items() if "_TABLE" in name}
        geom_layers = {name: layer for name, layer in all_layers.items() if "_TABLE" not in name}
        
        for tab_name, tab_layer in tables.items():
            ref_name = tab_name.replace("_TABLE", "").replace(f"{base_name}_", "")
            
            for geom_name, geom_layer in geom_layers.items():
                from qgis.core import QgsVectorLayerJoinInfo
                
                join_info = QgsVectorLayerJoinInfo()
                join_info.setJoinLayerId(tab_layer.id())
                
                tab_fields = [f.name() for f in tab_layer.fields()]
                geom_fields = [f.name() for f in geom_layer.fields()]
                
                join_field = None
                target_field = None
                
                if "label" in tab_fields:
                    join_field = "label"
                elif "name" in tab_fields:
                    join_field = "name"
                elif tab_fields:
                    dynamic = [f for f in tab_fields if f not in ("source_file", "table_ref", "row_index")]
                    if dynamic:
                        join_field = dynamic[0]
                        
                if "label" in geom_fields:
                    target_field = "label"
                elif "name" in geom_fields:
                    target_field = "name"
                    
                if join_field and target_field:
                    join_info.setJoinFieldName(join_field)
                    join_info.setTargetFieldName(target_field)
                    join_info.setUsingMemoryCache(True)
                    join_info.setPrefix(f"{ref_name}_")
                    
                    geom_layer.addJoin(join_info)
                    geom_layer.triggerRepaint()
