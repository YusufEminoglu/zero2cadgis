# -*- coding: utf-8 -*-
"""zero2cadgis — Tabbed DockWidget Controller.
100% English, fully integrated with core CAD/GIS engines.
Includes dynamic Exporter module and GroundOverlay extraction.
"""
from __future__ import annotations

import os
import re
import math
from dataclasses import dataclass, field

from qgis.PyQt.QtCore import Qt, QVariant, QSettings
from qgis.PyQt.QtGui import QIcon
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
    QSplitter,
    QTabWidget,
    QComboBox,
    QDialog,
    QTextBrowser,
    QDialogButtonBox,
    QScrollArea,
)
from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsFeature,
    QgsField,
    QgsGeometry,
    QgsPointXY,
    QgsCoordinateReferenceSystem,
    QgsVectorFileWriter
)
from qgis.gui import QgsProjectionSelectionWidget

# Core services imports
from ..core.netcad_parser import NetcadBinaryReader, NetcadEntity, NetcadAttributeTable
from ..core.gis_engine import GisConverterEngine
from ..core.cad_engine import CadCleanupEngine, CadStylingEngine, CadFeatureAugmenter, CadExportEngine
from ..core.path_utils import ensure_extension, has_extension
from ..core.qgis_compat import add_features_or_raise

# ──────────────────────────────────────────────────────────────────────────────
# Dock stylesheet — every text colour, background and border is *pinned* so
# the panel reads identically under QGIS 3 (Qt5 / light host palette) and
# QGIS 4 (Qt6 / often-dark host palette).  Without pinning, combo-box popups
# render solid-black and labels vanish against the white cards on dark themes.
# This follows the same remedy applied in the zero2viz studio.
# ──────────────────────────────────────────────────────────────────────────────
DOCK_STYLE = """
/* ── root & font ── */
QWidget {
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 12px;
    color: #263238;
    background: transparent;
}

/* ── tabs ── */
QTabWidget::pane {
    border: 1px solid #cfd8dc;
    border-radius: 4px;
    top: -1px;
    background: #ffffff;
}
QTabBar::tab {
    background: #eceff1;
    color: #546e7a;
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
QTabBar::tab:hover {
    color: #01579b;
}

/* ── group boxes ── */
QGroupBox {
    font-weight: bold;
    color: #37474f;
    background: #ffffff;
    border: 1px solid #cfd8dc;
    border-radius: 6px;
    margin-top: 6px;
    padding-top: 12px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 8px;
    padding: 0 4px;
    color: #0277bd;
}

/* ── scroll area ── */
QScrollArea {
    border: none;
    background: transparent;
}
QScrollArea > QWidget > QWidget {
    background: transparent;
}

/* ── labels: pinned dark so they never inherit a host-palette light/dark
      colour and become invisible on white cards ── */
QLabel {
    color: #37474f;
    background: transparent;
}
QLabel#dock_title {
    color: #263238;
    font-size: 15px;
    font-weight: bold;
}
QLabel#dock_subtitle {
    color: #607d8b;
    font-size: 11px;
}

/* ── checkboxes ── */
QCheckBox {
    color: #37474f;
    background: transparent;
    spacing: 6px;
}
QCheckBox::indicator {
    width: 14px;
    height: 14px;
    border: 1px solid #546e7a;
    border-radius: 2px;
    background: #ffffff;
}
QCheckBox::indicator:hover {
    border-color: #0277bd;
}
QCheckBox::indicator:checked {
    background: #0277bd;
    border-color: #0277bd;
    image: url(__CHECKBOX_CHECKED_ICON__);
}
QCheckBox::indicator:checked:hover {
    background: #01579b;
    border-color: #01579b;
}
QCheckBox::indicator:disabled {
    border-color: #b0bec5;
}
QCheckBox::indicator:checked:disabled {
    background: #b0bec5;
    border-color: #b0bec5;
}
QCheckBox:disabled {
    color: #90a4ae;
}

/* ── inputs: white field, dark text, teal selection — independent of the
      host palette so the dropdown popup is never black ── */
QLineEdit {
    border: 1px solid #cfd8dc;
    border-radius: 4px;
    padding: 4px;
    background-color: #ffffff;
    color: #263238;
    selection-background-color: #0277bd;
    selection-color: #ffffff;
}
QLineEdit:focus {
    border: 1px solid #0277bd;
}
QLineEdit:disabled {
    background: #eceff1;
    color: #90a4ae;
    border-color: #dde2e6;
}

QComboBox {
    background: #ffffff;
    color: #263238;
    border: 1px solid #cfd8dc;
    border-radius: 4px;
    padding: 4px 6px;
    selection-background-color: #0277bd;
    selection-color: #ffffff;
}
QComboBox:focus {
    border: 1px solid #0277bd;
}
QComboBox:disabled {
    background: #eceff1;
    color: #90a4ae;
    border-color: #dde2e6;
}
/* the drop-down list popup — without pinning this was solid black on
   dark-themed QGIS 4 */
QComboBox QAbstractItemView {
    background: #ffffff;
    color: #263238;
    border: 1px solid #cfd8dc;
    selection-background-color: #0277bd;
    selection-color: #ffffff;
    outline: 0;
}
QComboBox QAbstractItemView::item {
    min-height: 22px;
    padding: 2px 4px;
}

QDoubleSpinBox, QSpinBox {
    background: #ffffff;
    color: #263238;
    border: 1px solid #cfd8dc;
    border-radius: 4px;
    padding: 3px 6px;
    selection-background-color: #0277bd;
    selection-color: #ffffff;
}
QDoubleSpinBox:focus, QSpinBox:focus {
    border: 1px solid #0277bd;
}
QDoubleSpinBox:disabled, QSpinBox:disabled {
    background: #eceff1;
    color: #90a4ae;
    border-color: #dde2e6;
}

/* ── tree widget ── */
QTreeWidget {
    border: 1px solid #cfd8dc;
    border-radius: 4px;
    background-color: #ffffff;
    color: #263238;
}
QTreeWidget::item {
    color: #263238;
}
QTreeWidget::item:selected {
    background: #0277bd;
    color: #ffffff;
}
QHeaderView::section {
    background: #eceff1;
    color: #37474f;
    border: 1px solid #cfd8dc;
    padding: 4px;
    font-weight: bold;
}

/* ── primary action buttons ── */
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

/* ── browse / save-as buttons ── */
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

/* ── secondary / generic buttons (Select All, Deselect All, etc.) ── */
QPushButton {
    background: #eceff1;
    color: #263238;
    border: 1px solid #cfd8dc;
    border-radius: 4px;
    padding: 5px 10px;
}
QPushButton:hover {
    background: #e0e4e8;
}
QPushButton:disabled {
    background: #f5f5f5;
    color: #90a4ae;
    border-color: #e0e4e8;
}

/* ── progress bar ── */
QProgressBar {
    border: 1px solid #cfd8dc;
    border-radius: 4px;
    text-align: center;
    font-weight: bold;
    background: #ffffff;
    color: #263238;
}
QProgressBar::chunk {
    background-color: #ffb300;
}

/* ── dock header card ── */
QWidget#dock_header {
    background: #f8fafc;
    border: 1px solid #d7e0e7;
    border-radius: 6px;
}

/* ── guide button & body ── */
QPushButton#guide_btn {
    background-color: #263238;
    color: #ffffff;
    border: none;
    border-radius: 4px;
    padding: 5px 12px;
    font-weight: bold;
}
QPushButton#guide_btn:hover {
    background-color: #111827;
}
QTextBrowser#guide_body {
    border: 1px solid #d7e0e7;
    border-radius: 6px;
    background: #ffffff;
    color: #263238;
    padding: 8px;
}

/* ── tooltips ── */
QToolTip {
    background: #263238;
    color: #ffffff;
    border: 1px solid #263238;
    padding: 4px 6px;
}

/* ── splitter handle ── */
QSplitter::handle {
    background: #cfd8dc;
}
QSplitter::handle:hover {
    background: #0277bd;
}
"""


@dataclass
class LayerBucket:
    display_name: str
    geometry_type: str
    entities: list[NetcadEntity] = field(default_factory=list)
    source_files: dict[int, str] = field(default_factory=dict)


@dataclass
class LayerGroup:
    name: str
    layers: list[QgsVectorLayer] = field(default_factory=list)


class Zero2CadGisDockWidget(QDockWidget):
    """100% English controller managing GIS/CAD converter, exporter, and NCZ imports."""

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
        super().__init__("02CadGis - Universal CAD/GIS Importer", parent)
        self.iface = iface
        self.icon_dir = icon_dir

        self.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        checkbox_icon = os.path.join(
            self.icon_dir, "checkbox_checked.png").replace("\\", "/")
        self.setStyleSheet(
            DOCK_STYLE.replace("__CHECKBOX_CHECKED_ICON__", checkbox_icon))

        self.current_netcad_paths: list[str] = []
        self.parsed_netcad_results = {}
        self.gis_converter = None

        self._build_ui()

    def closeEvent(self, event):
        if self.gis_converter:
            self.gis_converter.cleanup()
        super().closeEvent(event)

    def _build_ui(self) -> None:
        main_tab = QTabWidget()

        # ───────────────────────── TAB 1: CAD & GIS Converter ────────────────
        tab1_inner = QWidget()
        cad_gis_layout = QVBoxLayout(tab1_inner)
        cad_gis_layout.setContentsMargins(4, 4, 4, 4)
        cad_gis_layout.setSpacing(2)

        # Source Selection
        src_group = QGroupBox("Source CAD / GIS Dataset")
        src_layout = QVBoxLayout(src_group)
        src_layout.setContentsMargins(6, 10, 6, 6)
        src_layout.setSpacing(3)

        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Dataset Type:"))
        self.cmb_src_type = QComboBox()
        self.cmb_src_type.addItems(["DXF (*.dxf)",
                                    "KML / KMZ (*.kml, *.kmz)",
                                    "Microstation DGN (*.dgn)",
                                    "ArcGIS File Geodatabase (*.gdb)",
                                    "ArcGIS Personal Geodatabase (*.mdb)"])
        self.cmb_src_type.insertSeparator(5)
        self.cmb_src_type.addItem(
            "Future enhancement: DWG (*.dwg)")
        future_dwg_index = self.cmb_src_type.count() - 1
        future_dwg_item = self.cmb_src_type.model().item(future_dwg_index)
        if future_dwg_item is not None:
            future_dwg_item.setEnabled(False)
        self.cmb_src_type.setItemData(
            future_dwg_index,
            "Current QGIS/GDAL builds only read limited DWG versions via libopencad. Convert DWG to DXF first.",
            Qt.ItemDataRole.ToolTipRole)
        self.cmb_src_type.currentIndexChanged.connect(
            self._on_source_type_changed)
        type_layout.addWidget(self.cmb_src_type, 1)
        src_layout.addLayout(type_layout)

        path_layout = QHBoxLayout()
        self.txt_src_path = QLineEdit()
        self.txt_src_path.setReadOnly(True)
        self.txt_src_path.setPlaceholderText(
            "Select drawing or GIS dataset...")
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
        dst_layout.setContentsMargins(6, 10, 6, 6)

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
        opt_form.setContentsMargins(6, 10, 6, 6)
        opt_form.setSpacing(3)

        self.converter_crs = QgsProjectionSelectionWidget()
        self.converter_crs.setOptionVisible(
            QgsProjectionSelectionWidget.CrsOption.ProjectCrs, True)
        self.converter_crs.setCrs(QgsProject.instance().crs())
        opt_form.addRow("Target CRS:", self.converter_crs)

        self.chk_conv_simplify = QCheckBox("Simplify collinear segment nodes")
        self.chk_conv_simplify.setChecked(True)
        opt_form.addRow(self.chk_conv_simplify)

        self.chk_conv_clean = QCheckBox(
            "Remove duplicate geometries and vertices")
        self.chk_conv_clean.setChecked(True)
        opt_form.addRow(self.chk_conv_clean)

        self.chk_conv_kml_expand = QCheckBox(
            "Expand KML HTML balloon tables (kmltools feyz)")
        self.chk_conv_kml_expand.setChecked(True)
        opt_form.addRow(self.chk_conv_kml_expand)

        self.chk_conv_raster = QCheckBox(
            "Extract KML GroundOverlays to GeoTiff")
        self.chk_conv_raster.setChecked(True)
        opt_form.addRow(self.chk_conv_raster)

        self.chk_conv_load = QCheckBox(
            "Load converted layers directly to canvas")
        self.chk_conv_load.setChecked(True)
        opt_form.addRow(self.chk_conv_load)

        self.chk_conv_temporary = QCheckBox(
            "Import directly as temporary scratch layers (no GPKG)")
        self.chk_conv_temporary.stateChanged.connect(
            self._on_conv_temporary_changed)
        opt_form.addRow(self.chk_conv_temporary)

        cad_gis_layout.addWidget(opt_group)

        # Progress Bar & Trigger
        self.progress_conv = QProgressBar()
        self.progress_conv.setVisible(False)
        cad_gis_layout.addWidget(self.progress_conv)

        self.btn_convert_gis = QPushButton("Convert to GeoPackage")
        self.btn_convert_gis.setObjectName("convert_btn")
        self.btn_convert_gis.setEnabled(False)
        self.btn_convert_gis.clicked.connect(self._convert_gis_dataset)
        cad_gis_layout.addWidget(self.btn_convert_gis)

        self._on_source_type_changed(self.cmb_src_type.currentIndex())

        tab_cad_gis = self._make_scroll_tab(tab1_inner)
        main_tab.addTab(
            tab_cad_gis,
            QIcon(
                os.path.join(
                    self.icon_dir,
                    "icon_cad.png")),
            "CAD & GIS Converter")

        # ───────────────────────── TAB 2: Netcad NCZ Importer ────────────────
        tab2_inner = QWidget()
        ncz_layout = QVBoxLayout(tab2_inner)
        ncz_layout.setContentsMargins(4, 4, 4, 4)
        ncz_layout.setSpacing(2)

        # NCZ File Select
        ncz_file_group = QGroupBox("NCZ File Selection")
        ncz_file_layout = QHBoxLayout(ncz_file_group)
        ncz_file_layout.setContentsMargins(6, 10, 6, 6)

        self.txt_ncz_path = QLineEdit()
        self.txt_ncz_path.setReadOnly(True)
        self.txt_ncz_path.setPlaceholderText(
            "Select Netcad .ncz or .nca file...")
        ncz_file_layout.addWidget(self.txt_ncz_path)

        self.btn_browse_ncz = QPushButton("Browse...")
        self.btn_browse_ncz.setObjectName("browse_btn")
        self.btn_browse_ncz.clicked.connect(self._select_ncz_file)
        ncz_file_layout.addWidget(self.btn_browse_ncz)
        ncz_layout.addWidget(ncz_file_group)

        # Metadata Card
        self.ncz_meta_group = QGroupBox("Drawing Metadata")
        ncz_meta_form = QFormLayout(self.ncz_meta_group)
        ncz_meta_form.setContentsMargins(6, 8, 6, 4)
        ncz_meta_form.setSpacing(2)

        self.lbl_ncz_version = QLabel("-")
        self.lbl_ncz_projection = QLabel("-")
        self.lbl_ncz_epsg = QLabel("-")
        self.lbl_ncz_counts = QLabel("-")

        ncz_meta_form.addRow("Netcad Version:", self.lbl_ncz_version)
        ncz_meta_form.addRow("Projection:", self.lbl_ncz_projection)
        ncz_meta_form.addRow("Detected EPSG:", self.lbl_ncz_epsg)
        ncz_meta_form.addRow("Objects / Tables:", self.lbl_ncz_counts)
        ncz_layout.addWidget(self.ncz_meta_group)

        # Layer Tree
        ncz_tree_group = QGroupBox("Select Layers to Import")
        ncz_tree_layout = QVBoxLayout(ncz_tree_group)
        ncz_tree_layout.setContentsMargins(4, 8, 4, 4)
        ncz_tree_layout.setSpacing(2)

        self.ncz_layer_tree = QTreeWidget()
        self.ncz_layer_tree.setHeaderLabels(
            ["Layer Name", "Geometry", "Count"])
        self.ncz_layer_tree.setColumnWidth(0, 140)
        self.ncz_layer_tree.setColumnWidth(1, 80)
        ncz_tree_layout.addWidget(self.ncz_layer_tree)

        # Selection tools
        ncz_sel_layout = QHBoxLayout()
        ncz_sel_layout.setSpacing(4)
        self.btn_ncz_select_all = QPushButton("Select All")
        self.btn_ncz_select_all.clicked.connect(self._select_all_ncz_layers)
        self.btn_ncz_deselect_all = QPushButton("Deselect All")
        self.btn_ncz_deselect_all.clicked.connect(
            self._deselect_all_ncz_layers)
        ncz_sel_layout.addWidget(self.btn_ncz_select_all)
        ncz_sel_layout.addWidget(self.btn_ncz_deselect_all)
        ncz_tree_layout.addLayout(ncz_sel_layout)
        ncz_layout.addWidget(ncz_tree_group)

        # Advanced CAD Options
        ncz_opt_group = QGroupBox("CAD Optimization & Styling")
        ncz_opt_form = QFormLayout(ncz_opt_group)
        ncz_opt_form.setContentsMargins(6, 10, 6, 6)
        ncz_opt_form.setSpacing(3)

        self.ncz_crs_selector = QgsProjectionSelectionWidget()
        self.ncz_crs_selector.setOptionVisible(
            QgsProjectionSelectionWidget.CrsOption.ProjectCrs, True)
        self.ncz_crs_selector.setCrs(QgsProject.instance().crs())
        ncz_opt_form.addRow("Destination CRS:", self.ncz_crs_selector)

        self.chk_ncz_simplify = QCheckBox("Simplify collinear vertices")
        self.chk_ncz_simplify.setChecked(True)
        ncz_opt_form.addRow(self.chk_ncz_simplify)

        self.chk_ncz_clean = QCheckBox("Clean duplicate nodes")
        self.chk_ncz_clean.setChecked(True)
        ncz_opt_form.addRow(self.chk_ncz_clean)

        self.chk_ncz_augment = QCheckBox(
            "Calculate geometry metadata (Area, Length)")
        self.chk_ncz_augment.setChecked(True)
        ncz_opt_form.addRow(self.chk_ncz_augment)

        self.spin_ncz_tolerance = QDoubleSpinBox()
        self.spin_ncz_tolerance.setRange(0.0, 10.0)
        self.spin_ncz_tolerance.setSingleStep(0.05)
        self.spin_ncz_tolerance.setValue(0.10)
        self.spin_ncz_tolerance.setSuffix(" m")
        ncz_opt_form.addRow(
            "Polyline Closure Tolerance:",
            self.spin_ncz_tolerance)

        self.chk_ncz_style = QCheckBox(
            "Apply original ARGB colors and line styles")
        self.chk_ncz_style.setChecked(True)
        ncz_opt_form.addRow(self.chk_ncz_style)

        self.chk_ncz_label = QCheckBox("Convert text elements to map labels")
        self.chk_ncz_label.setChecked(True)
        ncz_opt_form.addRow(self.chk_ncz_label)

        self.chk_ncz_join = QCheckBox(
            "Join attribute tables (@TAB) automatically")
        self.chk_ncz_join.setChecked(True)
        ncz_opt_form.addRow(self.chk_ncz_join)

        self.chk_ncz_merge_geometry = QCheckBox(
            "Merge geometry types across selected files")
        self.chk_ncz_merge_geometry.setToolTip(
            "Batch NCZ import: group outputs by geometry type and merge "
            "layers with the same geometry type and CAD layer name.")
        self.chk_ncz_merge_geometry.setEnabled(False)
        ncz_opt_form.addRow(self.chk_ncz_merge_geometry)

        self.chk_ncz_temporary = QCheckBox(
            "Import directly as temporary scratch layers (no GPKG)")
        ncz_opt_form.addRow(self.chk_ncz_temporary)

        ncz_layout.addWidget(ncz_opt_group)

        # Progress Bar & Trigger
        self.progress_ncz = QProgressBar()
        self.progress_ncz.setVisible(False)
        ncz_layout.addWidget(self.progress_ncz)

        self.btn_convert_ncz = QPushButton("Convert Netcad & Load to Canvas")
        self.btn_convert_ncz.setObjectName("convert_btn")
        self.btn_convert_ncz.setEnabled(False)
        self.btn_convert_ncz.clicked.connect(self._import_netcad_dataset)
        ncz_layout.addWidget(self.btn_convert_ncz)

        tab_ncz = self._make_scroll_tab(tab2_inner)
        main_tab.addTab(
            tab_ncz,
            QIcon(
                os.path.join(
                    self.icon_dir,
                    "icon_ncz.png")),
            "Netcad NCZ/NCA Importer")

        # ───────────────────────── TAB 3: CAD & GIS Exporter ─────────────────
        tab3_inner = QWidget()
        exp_layout = QVBoxLayout(tab3_inner)
        exp_layout.setContentsMargins(4, 4, 4, 4)
        exp_layout.setSpacing(2)

        exp_group = QGroupBox("Export Active QGIS Layers")
        exp_form = QFormLayout(exp_group)
        exp_form.setContentsMargins(6, 10, 6, 6)
        exp_form.setSpacing(3)

        self.cmb_exp_layer = QComboBox()
        exp_form.addRow("Select Source Layer:", self.cmb_exp_layer)

        self.cmb_exp_format = QComboBox()
        self.cmb_exp_format.addItems(
            ["AutoCAD DXF (*.dxf)", "Google Earth KML (*.kml)", "Google Earth KMZ (*.kmz)"])
        self.cmb_exp_format.currentIndexChanged.connect(
            self._on_export_format_changed)
        exp_form.addRow("Target Export Format:", self.cmb_exp_format)

        self.txt_exp_path = QLineEdit()
        self.txt_exp_path.setReadOnly(True)
        self.txt_exp_path.setPlaceholderText(
            "Select destination export file...")

        self.btn_browse_exp = QPushButton("Save As...")
        self.btn_browse_exp.setObjectName("browse_btn")
        self.btn_browse_exp.clicked.connect(self._browse_export_destination)

        browse_layout = QHBoxLayout()
        browse_layout.addWidget(self.txt_exp_path)
        browse_layout.addWidget(self.btn_browse_exp)
        exp_form.addRow("Save Location:", browse_layout)

        exp_layout.addWidget(exp_group)

        self.btn_run_export = QPushButton("Export Dataset")
        self.btn_run_export.setObjectName("convert_btn")
        self.btn_run_export.setEnabled(False)
        self.btn_run_export.clicked.connect(self._run_export_layer)
        exp_layout.addWidget(self.btn_run_export)
        exp_layout.addStretch(1)

        tab_exp = self._make_scroll_tab(tab3_inner)
        main_tab.addTab(
            tab_exp,
            QIcon(
                os.path.join(
                    self.icon_dir,
                    "icon_gis.png")),
            "CAD & GIS Exporter")

        # Set main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(3, 3, 3, 3)
        main_layout.setSpacing(3)
        main_layout.addWidget(self._build_header())
        main_layout.addWidget(main_tab, 1)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setWidget(central_widget)

        # Populate layers after UI elements are fully constructed
        self._populate_layers_combo()

    @staticmethod
    def _make_scroll_tab(inner_widget: QWidget) -> QScrollArea:
        """Wrap *inner_widget* in a QScrollArea so the tab content scrolls."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setWidget(inner_widget)
        return scroll

    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setObjectName("dock_header")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(8, 5, 8, 5)
        layout.setSpacing(6)

        title_box = QWidget()
        title_layout = QVBoxLayout(title_box)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(0)

        title = QLabel("02CadGis")
        title.setObjectName("dock_title")
        subtitle = QLabel("CAD, KML, DGN and GDB conversion studio")
        subtitle.setObjectName("dock_subtitle")
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)

        self.btn_guide = QPushButton("Guide")
        self.btn_guide.setObjectName("guide_btn")
        self.btn_guide.clicked.connect(self._show_guide)

        layout.addWidget(title_box, 1)
        layout.addWidget(self.btn_guide, 0)
        return header

    def _show_guide(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("02CadGis Guide")
        dialog.resize(560, 520)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        guide = QTextBrowser(dialog)
        guide.setObjectName("guide_body")
        guide.setOpenExternalLinks(True)
        guide.setHtml("""
        <h2>02CadGis Quick Start</h2>
        <p>Use 02CadGis when you need QGIS-ready GeoPackage layers from CAD, KML/KMZ, DGN, GDB, or Netcad drawing data.</p>

        <h3>1. Convert CAD or GIS to GeoPackage</h3>
        <ol>
          <li>Choose the source family: DXF, KML/KMZ, DGN, or FileGDB. DWG is listed as a future enhancement because current QGIS/GDAL builds only read limited DWG versions.</li>
          <li>Select the source file or `.gdb` folder.</li>
          <li>Choose a target `.gpkg`, or enable temporary scratch layers when you only want to inspect the result.</li>
          <li>Confirm the target CRS. The project CRS is used when the selector is not changed.</li>
          <li>Keep cleanup enabled for typical CAD drawings; disable it only when auditing raw geometry.</li>
          <li>For KML/KMZ, enable balloon expansion for structured attributes and GroundOverlay extraction for raster overlays.</li>
          <li>Run <b>Convert to GeoPackage</b>.</li>
        </ol>

        <h3>2. Netcad NCZ/NCA Importer</h3>
        <p>The Netcad importer is designed for municipal drawing packages where geometry, CAD layers, colors, text, and attribute tables arrive together.</p>
        <ol>
          <li>Select one or more `.ncz` or compatible `.nca` drawing files. Batch import keeps files separate by default; enable <b>Merge geometry types</b> to group by geometry type and merge matching layer names across files.</li>
          <li>Check the metadata card before importing. Version, projection text, detected EPSG, feature count, and table count help you catch wrong files early.</li>
          <li>Use the layer tree to import only the CAD layers and `@TAB` tables you need. Parent checkboxes select or clear whole groups.</li>
          <li>Set the destination CRS. If an EPSG code is detected, 02CadGis preselects it; otherwise it falls back to the project CRS.</li>
          <li>Use <b>Simplify collinear vertices</b> to reduce heavy CAD linework while preserving shape.</li>
          <li>Use <b>Clean duplicate nodes</b> to remove repeated adjacent vertices that can break topology tools.</li>
          <li>Set <b>Polyline Closure Tolerance</b> for small endpoint gaps. Keep it low for cadastral work; increase only when the source drawing has known snap gaps.</li>
          <li>Enable <b>Calculate geometry metadata</b> to add length, area, and centroid fields for QA and reporting.</li>
          <li>Enable <b>Apply original ARGB colors</b> when CAD layer colors are meaningful for review.</li>
          <li>Enable <b>Convert text elements to map labels</b> to preserve readable Netcad annotations as QGIS labels.</li>
          <li>Enable <b>Join attribute tables</b> when the file contains `@TAB` records that should be linked back to geometry by name or label.</li>
          <li>Use temporary scratch layers for quick inspection; use GeoPackage output when the conversion is a deliverable.</li>
          <li>Run <b>Convert Netcad &amp; Load to Canvas</b>.</li>
        </ol>
        <p><b>Netcad QA tip:</b> If expected layers are missing, retry with cleanup disabled and a smaller closure tolerance, then compare the raw and optimized outputs.</p>

        <h3>3. Export QGIS Layers</h3>
        <ol>
          <li>Select an active vector layer from the current QGIS project.</li>
          <li>Choose DXF, KML, or KMZ.</li>
          <li>Pick the save path and run <b>Export Dataset</b>.</li>
        </ol>
        <p><b>Best practice:</b> Use scratch layers for exploration and GeoPackage output for archiving, sharing, and Plugin Hub release examples.</p>
        """)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(guide, 1)
        layout.addWidget(buttons)
        dialog.exec()

    # ───────────────────────── TAB 1: GIS/CAD CONVERTER CONTROLS ────────────

    def _on_source_type_changed(self, index: int) -> None:
        self.txt_src_path.clear()
        self.btn_convert_gis.setEnabled(False)
        is_kml = index == 1
        self.chk_conv_kml_expand.setEnabled(is_kml)
        self.chk_conv_raster.setEnabled(is_kml)

    def _browse_src_dataset(self) -> None:
        idx = self.cmb_src_type.currentIndex()
        start_dir = self._last_import_dir()
        if idx == 0:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Select DXF File", start_dir, "AutoCAD DXF (*.dxf)")
            if file_path and not has_extension(file_path, ".dxf"):
                QMessageBox.warning(
                    self,
                    "Unsupported Drawing Version",
                    "DWG import is a future enhancement in this QGIS/GDAL build. Convert DWG to DXF first, then import the DXF file.")
                return
        elif idx == 1:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Select KML or KMZ File", start_dir, "Keyhole Markup Language (*.kml *.kmz)")
        elif idx == 2:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Select Microstation DGN File", start_dir, "Design Files (*.dgn)")
        elif idx == 3:
            file_path = QFileDialog.getExistingDirectory(
                self,
                "Select ArcGIS File Geodatabase Directory",
                start_dir,
                QFileDialog.Option.ShowDirsOnly)
            if file_path and not has_extension(file_path, ".gdb"):
                QMessageBox.warning(
                    self,
                    "Invalid Folder",
                    "Please select a directory ending with '.gdb'.")
                return
        elif idx == 4:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Select ArcGIS Personal Geodatabase File", start_dir, "ArcGIS Personal Geodatabase (*.mdb)")
        else:
            QMessageBox.information(
                self,
                "Future Enhancement",
                "DWG import needs broader CAD reader support than the current QGIS/GDAL libopencad driver provides. Convert DWG to DXF first.")
            return

        if file_path:
            self.txt_src_path.setText(file_path)
            self._remember_import_dir(file_path)
            self._update_convert_gis_button_state()

    def _browse_gpkg_destination(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Select Output GeoPackage", "", "GeoPackage (*.gpkg)"
        )
        if file_path:
            file_path = ensure_extension(file_path, ".gpkg")
            self.txt_gpkg_path.setText(file_path)
            self._update_convert_gis_button_state()

    def _on_conv_temporary_changed(self, state: int) -> None:
        is_temp = self.chk_conv_temporary.isChecked()
        self.txt_gpkg_path.setEnabled(not is_temp)
        self.btn_browse_gpkg.setEnabled(not is_temp)
        if is_temp:
            self.txt_gpkg_path.clear()
            self.chk_conv_load.setChecked(True)
        self.chk_conv_load.setEnabled(not is_temp)
        self._update_convert_gis_button_state()

    def _update_convert_gis_button_state(self) -> None:
        has_src = bool(self.txt_src_path.text().strip())
        is_temp = self.chk_conv_temporary.isChecked()
        has_dst = bool(self.txt_gpkg_path.text().strip())
        self.btn_convert_gis.setEnabled(has_src and (is_temp or has_dst))

    def _convert_gis_dataset(self) -> None:
        src = self.txt_src_path.text()
        dst = self.txt_gpkg_path.text()
        idx = self.cmb_src_type.currentIndex()
        if idx == self.cmb_src_type.count() - 1:
            QMessageBox.information(
                self,
                "Future Enhancement",
                "DWG import is planned for a future enhancement. Convert DWG to DXF first.")
            return

        crs = self.converter_crs.crs()
        if not crs.isValid():
            crs = QgsProject.instance().crs()

        self.progress_conv.setVisible(True)
        self.progress_conv.setValue(10)
        self.progress_conv.setFormat("Initializing GIS Converter...")

        try:
            is_kmz = idx == 1 and has_extension(src, ".kmz")
            is_temp = self.chk_conv_temporary.isChecked()

            # Initialize GisConverterEngine
            self.gis_converter = GisConverterEngine(src, dst, crs)

            self.progress_conv.setValue(40)
            if is_temp:
                self.progress_conv.setFormat(
                    "Creating temporary scratch layers...")
                loaded_layers = self.gis_converter.convert_to_memory(
                    is_kmz=is_kmz,
                    html_expansion=self.chk_conv_kml_expand.isChecked()
                )
            else:
                self.progress_conv.setFormat(
                    "Converting vector layers to GeoPackage...")
                loaded_layers = self.gis_converter.convert(
                    is_kmz=is_kmz,
                    html_expansion=self.chk_conv_kml_expand.isChecked()
                )

            # GroundOverlay Extraction
            if self.chk_conv_raster.isChecked() and idx == 1:
                self.progress_conv.setValue(60)
                self.progress_conv.setFormat(
                    "Extracting KML GroundOverlays (kmltools feyz)...")
                raster_layers = self.gis_converter.extract_ground_overlays(
                    is_kmz=is_kmz)
                for rl in raster_layers:
                    QgsProject.instance().addMapLayer(rl)

            self.progress_conv.setValue(80)
            self.progress_conv.setFormat("Adding vector layers to canvas...")

            if self.chk_conv_load.isChecked() and loaded_layers:
                root = QgsProject.instance().layerTreeRoot()
                suffix = "TEMP" if self.chk_conv_temporary.isChecked() else "GPKG"
                group_name = f"{
                    self._sanitize_name(
                        os.path.basename(src))}_{suffix}"

                existing = root.findGroup(group_name)
                if existing:
                    root.removeChildNode(existing)

                group = root.addGroup(group_name)
                for cl in loaded_layers:
                    QgsProject.instance().addMapLayer(cl, False)
                    group.addLayer(cl)

            self.progress_conv.setValue(100)
            self.progress_conv.setVisible(False)

            # Refresh exporter layer combo list
            self._populate_layers_combo()

            message = "Conversion completed successfully!"
            if is_temp:
                message += "\nOutput: temporary scratch layers loaded in the current QGIS project."
            else:
                message += f"\nTarget path: {dst}"

            notes = getattr(self.gis_converter, "last_warnings", [])
            if notes:
                message += "\n\nNotes:\n- " + "\n- ".join(notes)

            QMessageBox.information(self, "Success", message)

        except Exception as exc:
            self.progress_conv.setVisible(False)
            QMessageBox.critical(
                self,
                "Conversion Error",
                f"Failed to execute GIS engine conversion:\n{exc}")

    # ───────────────────────── TAB 2: NETCAD NCZ IMPORTER CONTROLS ──────────

    def _select_ncz_file(self) -> None:
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "Select Netcad NCZ/NCA Drawing File(s)", self._last_import_dir(),
            "Netcad Drawing Files (*.ncz *.nca);;All Files (*.*)")
        if not file_paths:
            return

        self._remember_import_dir(file_paths[0])
        self.current_netcad_paths = file_paths
        if len(file_paths) == 1:
            self.txt_ncz_path.setText(file_paths[0])
        else:
            self.txt_ncz_path.setText(f"{len(file_paths)} files selected")

        is_batch_import = len(file_paths) > 1
        self.chk_ncz_merge_geometry.setEnabled(is_batch_import)
        if not is_batch_import:
            self.chk_ncz_merge_geometry.setChecked(False)

        self.parsed_netcad_results = {}
        total_entities = 0
        total_tables = 0
        versions = set()
        projections = set()
        epsg_codes = set()

        self.progress_ncz.setVisible(True)
        self.progress_ncz.setValue(10)
        self.progress_ncz.setFormat("Parsing selected Netcad drawings...")

        try:
            for idx, file_path in enumerate(file_paths):
                self.progress_ncz.setValue(
                    10 + int((idx / len(file_paths)) * 50))
                self.progress_ncz.setFormat(
                    f"Parsing {os.path.basename(file_path)}...")

                reader = NetcadBinaryReader(file_path)
                res = reader.parse()
                self.parsed_netcad_results[file_path] = res

                total_entities += len(res.entities)
                total_tables += len(res.attribute_tables)
                if res.version_name:
                    versions.add(res.version_name)
                if res.projection_text:
                    projections.add(res.projection_text)
                if res.epsg:
                    epsg_codes.add(res.epsg)

            self.progress_ncz.setValue(60)
            self.progress_ncz.setFormat("Building layer catalog...")

            # Guess target CRS from first valid EPSG found
            for epsg in epsg_codes:
                clean_epsg = epsg.replace("EPSG:", "").strip()
                crs = QgsCoordinateReferenceSystem(f"EPSG:{clean_epsg}")
                if crs.isValid():
                    self.ncz_crs_selector.setCrs(crs)
                    break

            # Populate card
            self.lbl_ncz_version.setText(
                ", ".join(versions) or "Standard / Older version")
            self.lbl_ncz_projection.setText(
                ", ".join(projections) or "Undefined")
            self.lbl_ncz_epsg.setText(", ".join(epsg_codes) or "Not defined")
            self.lbl_ncz_counts.setText(
                f"{total_entities} features / {total_tables} attribute tables across {len(file_paths)} files")

            # Fill Tree Widget
            self._fill_ncz_layer_tree()

            self.progress_ncz.setValue(100)
            self.progress_ncz.setVisible(False)
            self.btn_convert_ncz.setEnabled(True)

        except Exception as exc:
            self.progress_ncz.setVisible(False)
            self.btn_convert_ncz.setEnabled(False)
            QMessageBox.critical(
                self,
                "Netcad Parse Error",
                f"Could not parse binary Netcad drawings:\n{exc}")

    def _fill_ncz_layer_tree(self) -> None:
        self.ncz_layer_tree.clear()
        if not self.parsed_netcad_results:
            return

        for file_path, parsed in sorted(self.parsed_netcad_results.items()):
            file_name = os.path.basename(file_path)

            # 1. File Root Item
            file_item = QTreeWidgetItem(self.ncz_layer_tree)
            file_item.setText(0, file_name)
            file_item.setData(0, Qt.ItemDataRole.UserRole, file_path)
            file_item.setFlags(file_item.flags(
            ) | Qt.ItemFlag.ItemIsAutoTristate | Qt.ItemFlag.ItemIsUserCheckable)
            file_item.setCheckState(0, Qt.CheckState.Checked)
            file_item.setExpanded(True)

            # Group entities
            layer_stats = {}
            for entity in parsed.entities:
                family, _ = self._geometry_family(entity.geometry_kind)
                if not family:
                    continue
                key = (
                    entity.layer_code,
                    entity.layer_name or f"LAYER_{
                        entity.layer_code}",
                    family)
                layer_stats[key] = layer_stats.get(key, 0) + 1

            # CAD Layers subroot
            if layer_stats:
                cad_root = QTreeWidgetItem(file_item)
                cad_root.setText(0, "CAD Layers")
                cad_root.setFlags(
                    cad_root.flags() | Qt.ItemFlag.ItemIsAutoTristate | Qt.ItemFlag.ItemIsUserCheckable)
                cad_root.setCheckState(0, Qt.CheckState.Checked)
                cad_root.setExpanded(True)

                for (code, name, family), count in sorted(
                        layer_stats.items(), key=lambda x: x[0][1]):
                    item = QTreeWidgetItem(cad_root)
                    item.setText(0, name)
                    item.setText(1, family)
                    item.setText(2, str(count))
                    item.setFlags(
                        item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                    item.setCheckState(0, Qt.CheckState.Checked)
                    item.setData(
                        0, Qt.ItemDataRole.UserRole, (code, name, family))

            # Attribute Tables subroot
            if parsed.attribute_tables:
                table_root = QTreeWidgetItem(file_item)
                table_root.setText(0, "Attribute Tables (@TAB)")
                table_root.setFlags(table_root.flags(
                ) | Qt.ItemFlag.ItemIsAutoTristate | Qt.ItemFlag.ItemIsUserCheckable)
                table_root.setCheckState(0, Qt.CheckState.Checked)
                table_root.setExpanded(True)

                for table in parsed.attribute_tables:
                    item = QTreeWidgetItem(table_root)
                    item.setText(0, table.table_ref)
                    item.setText(1, "Attribute Data")
                    item.setText(2, f"{len(table.rows)} rows")
                    item.setFlags(
                        item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                    item.setCheckState(0, Qt.CheckState.Checked)
                    item.setData(0, Qt.ItemDataRole.UserRole,
                                 ("TABLE", table.table_ref, "TABLE"))

    def _select_all_ncz_layers(self) -> None:
        self._set_ncz_tree_checked_state(Qt.CheckState.Checked)

    def _deselect_all_ncz_layers(self) -> None:
        self._set_ncz_tree_checked_state(Qt.CheckState.Unchecked)

    def _set_ncz_tree_checked_state(self, state: Qt.CheckState) -> None:
        for index in range(self.ncz_layer_tree.topLevelItemCount()):
            item = self.ncz_layer_tree.topLevelItem(index)
            item.setCheckState(0, state)
            for child_idx in range(item.childCount()):
                sub = item.child(child_idx)
                sub.setCheckState(0, state)
                for g_child_idx in range(sub.childCount()):
                    sub.child(g_child_idx).setCheckState(0, state)

    def _geometry_family(
            self, geometry_kind: str) -> tuple[str, str] | tuple[None, None]:
        if geometry_kind in ("Point", "Text", "Symbol", "Block"):
            return "POINT/TEXT", "Point"
        if geometry_kind in ("Line", "Polyline", "Arc"):
            return "LINE", "LineString"
        if geometry_kind in (
            "Polygon",
            "Box",
            "Circle",
            "Triangle",
            "MapSheet",
                "SmartObject"):
            return "POLYGON", "Polygon"
        return None, None

    def _sanitize_name(self, value: str) -> str:
        text = re.sub(r"\W+", "_", str(value).strip(), flags=re.UNICODE)
        return text.strip("_").upper() or "LAYER"

    def _import_netcad_dataset(self) -> None:
        if not self.parsed_netcad_results:
            return

        try:
            self.progress_ncz.setVisible(True)
            self.progress_ncz.setValue(10)
            self.progress_ncz.setFormat("Filtering selected layers...")

            selected_by_file = {}
            root_count = self.ncz_layer_tree.topLevelItemCount()
            for idx_file in range(root_count):
                file_item = self.ncz_layer_tree.topLevelItem(idx_file)
                file_path = file_item.data(0, Qt.ItemDataRole.UserRole)
                if not file_path:
                    continue

                selected_by_file[file_path] = {"layers": [], "tables": []}
                for idx_sub in range(file_item.childCount()):
                    sub_item = file_item.child(idx_sub)
                    for idx_child in range(sub_item.childCount()):
                        child = sub_item.child(idx_child)
                        if child.checkState(0) == Qt.CheckState.Checked:
                            data = child.data(0, Qt.ItemDataRole.UserRole)
                            if data:
                                if data[0] == "TABLE":
                                    selected_by_file[file_path]["tables"].append(
                                        data[1])
                                else:
                                    selected_by_file[file_path]["layers"].append(
                                        data)

            has_selection = any(len(v["layers"]) > 0 or len(
                v["tables"]) > 0 for v in selected_by_file.values())
            if not has_selection:
                QMessageBox.warning(
                    self, "Warning", "Please select at least one layer or table to import.")
                self.progress_ncz.setVisible(False)
                return

            self.progress_ncz.setValue(30)
            self.progress_ncz.setFormat("Preparing Netcad layers...")

            gpkg_path = ""
            is_temp = self.chk_ncz_temporary.isChecked()
            first_file = os.path.splitext(os.path.basename(
                list(self.parsed_netcad_results.keys())[0]))[0]
            base_name = self._sanitize_name(f"{first_file}_BATCH") if len(
                self.parsed_netcad_results) > 1 else self._sanitize_name(first_file)

            if is_temp:
                gpkg_path = ""
            else:
                gpkg_path, _ = QFileDialog.getSaveFileName(
                    self, "Select Output GeoPackage for Netcad Data", "", "GeoPackage (*.gpkg)")
                if not gpkg_path:
                    self.progress_ncz.setVisible(False)
                    return
                gpkg_path = ensure_extension(gpkg_path, ".gpkg")

            target_crs = self.ncz_crs_selector.crs()
            if not target_crs.isValid():
                target_crs = QgsProject.instance().crs()

            merge_geometry_types = (
                self.chk_ncz_merge_geometry.isChecked()
                and len(self.parsed_netcad_results) > 1
            )
            layer_groups = []
            merged_entity_groups = {}
            transform_context = QgsProject.instance().transformContext()

            for file_path, selection in selected_by_file.items():
                selected_keys = set(selection["layers"])
                selected_tables = selection["tables"]
                if not selected_keys and not selected_tables:
                    continue

                parsed = self.parsed_netcad_results[file_path]
                source_file_name = os.path.splitext(
                    os.path.basename(file_path))[0]
                file_base_name = self._sanitize_name(source_file_name)

                grouped_entities = (
                    merged_entity_groups if merge_geometry_types else {})

                for entity in parsed.entities:
                    family, geometry_type = self._geometry_family(
                        entity.geometry_kind)
                    if not family:
                        continue

                    layer_name = entity.layer_name or f"LAYER_{entity.layer_code}"
                    selection_key = (entity.layer_code, layer_name, family)
                    if selection_key not in selected_keys:
                        continue

                    if merge_geometry_types:
                        family_token = self._sanitize_name(family)
                        layer_token = self._sanitize_name(layer_name)
                        display_name = f"{base_name}_{layer_token}_{family_token}"
                        group_name = f"{base_name}_{family_token}"
                        bucket_key = (layer_token, family, geometry_type)
                    else:
                        display_name = f"{file_base_name}_{self._sanitize_name(layer_name)}_{family}"
                        group_name = f"{file_base_name}_{family}"
                        bucket_key = selection_key

                    bucket = grouped_entities.setdefault(
                        group_name,
                        {}).setdefault(
                        bucket_key,
                        LayerBucket(
                            display_name=display_name,
                            geometry_type=geometry_type))
                    bucket.entities.append(entity)
                    bucket.source_files[id(entity)] = source_file_name

                if not merge_geometry_types:
                    layer_groups.extend(
                        self._build_layer_groups_from_buckets(
                            grouped_entities, target_crs))

                # 2. Attribute Tables
                if parsed.attribute_tables and selected_tables:
                    attribute_group_name = f"{file_base_name}_ATTRIBUTES"
                    attribute_layers = []
                    for table in parsed.attribute_tables:
                        if table.table_ref not in selected_tables:
                            continue
                        table_name = self._sanitize_name(table.table_ref)

                        temp_attr = self._create_temp_attribute_layer(
                            table_name, table, source_file_name)
                        if temp_attr:
                            temp_attr.setName(
                                f"{file_base_name}_{table_name}_TABLE")
                            attribute_layers.append(temp_attr)

                    if attribute_layers:
                        layer_groups.append(
                            LayerGroup(
                                name=attribute_group_name,
                                layers=attribute_layers))

            if merge_geometry_types:
                layer_groups.extend(
                    self._build_layer_groups_from_buckets(
                        merged_entity_groups, target_crs))

            if not layer_groups:
                raise ValueError(
                    "Selected Netcad data did not produce any valid layers.")

            if not is_temp:
                # Write each layer to a separate temp GPKG file, then merge, to
                # avoid SQLite update locks.
                import tempfile
                temp_gpkg_files = []
                try:
                    for group in layer_groups:
                        for layer in group.layers:
                            fd, temp_gpkg = tempfile.mkstemp(
                                suffix=".gpkg", prefix=f"ncz_l_{self._sanitize_name(layer.name())}_")
                            os.close(fd)
                            try:
                                os.remove(temp_gpkg)
                            except OSError:
                                pass

                            options = QgsVectorFileWriter.SaveVectorOptions()
                            options.driverName = "GPKG"
                            options.layerName = layer.name()
                            options.actionOnExistingFile = QgsVectorFileWriter.ActionOnExistingFile.CreateOrOverwriteFile

                            err, err_msg, _, _ = QgsVectorFileWriter.writeAsVectorFormatV3(
                                layer, temp_gpkg, transform_context, options)
                            if err != QgsVectorFileWriter.WriterError.NoError:
                                raise ValueError(
                                    f"Failed to write layer '{layer.name()}' to GPKG: {err_msg}")

                            temp_gpkg_files.append(temp_gpkg)

                    if not temp_gpkg_files:
                        raise ValueError(
                            "No temporary GeoPackage layers were created.")

                    if os.path.exists(gpkg_path):
                        try:
                            os.remove(gpkg_path)
                        except OSError:
                            pass

                    from osgeo import gdal
                    first = True
                    for temp_gpkg in temp_gpkg_files:
                        mode = "overwrite" if first else "update"
                        result = gdal.VectorTranslate(
                            gpkg_path, temp_gpkg, format="GPKG", accessMode=mode)
                        if result is None:
                            raise ValueError(
                                f"GDAL could not merge temporary layer {os.path.basename(temp_gpkg)}.")
                        result = None
                        first = False
                finally:
                    for temp_gpkg in temp_gpkg_files:
                        try:
                            os.remove(temp_gpkg)
                        except OSError:
                            pass

                final_layer_groups = []
                for group in layer_groups:
                    gpkg_layers = []
                    for layer in group.layers:
                        gpkg_uri = f"{gpkg_path}|layername={layer.name()}"
                        gpkg_layer = QgsVectorLayer(
                            gpkg_uri, layer.name(), "ogr")
                        if gpkg_layer.isValid():
                            gpkg_layers.append(gpkg_layer)
                    if gpkg_layers:
                        final_layer_groups.append(LayerGroup(
                            name=group.name, layers=gpkg_layers))
                layer_groups = final_layer_groups

            self.progress_ncz.setValue(80)
            self.progress_ncz.setFormat("Adding layers to QGIS layout...")

            # Add GPKG layers to project
            self._add_groups_to_project(layer_groups)

            # Apply Join
            any_tables = any(v["tables"] for v in selected_by_file.values())
            if self.chk_ncz_join.isChecked() and any_tables:
                self._join_attributes_to_layers(layer_groups, base_name)

            self.progress_ncz.setValue(100)
            self.progress_ncz.setVisible(False)

            # Refresh exporter layer combo list
            self._populate_layers_combo()

            if is_temp:
                message = "Netcad drawing imported as temporary scratch layers and loaded successfully."
            else:
                message = f"Netcad drawing converted to GeoPackage and loaded successfully!\nOutput path: {gpkg_path}"
            QMessageBox.information(self, "Success", message)

        except Exception as exc:
            self.progress_ncz.setVisible(False)
            QMessageBox.critical(
                self,
                "Import Error",
                f"Failed to import Netcad dataset:\n{exc}")

    def _build_layer_groups_from_buckets(
            self,
            grouped_entities: dict,
            target_crs: QgsCoordinateReferenceSystem) -> list[LayerGroup]:
        layer_groups = []
        for group_name in sorted(grouped_entities.keys()):
            layers = []
            for key in sorted(grouped_entities[group_name].keys()):
                bucket = grouped_entities[group_name][key]
                source_file_name = next(iter(bucket.source_files.values()), "")

                temp_layer = self._create_temp_vector_layer(
                    bucket.display_name,
                    bucket.geometry_type,
                    bucket.entities,
                    target_crs,
                    source_file_name,
                    bucket.source_files,
                )

                if temp_layer:
                    processed_layer = temp_layer
                    if self.chk_ncz_augment.isChecked():
                        try:
                            augmented_layer = CadFeatureAugmenter.augment_layer(
                                temp_layer)
                            if augmented_layer.featureCount() == temp_layer.featureCount():
                                processed_layer = augmented_layer
                        except Exception:
                            processed_layer = temp_layer

                    if self.chk_ncz_style.isChecked():
                        try:
                            CadStylingEngine.apply_argb_renderer(
                                processed_layer, bucket.geometry_type)
                        except Exception:
                            pass

                    if self.chk_ncz_label.isChecked() and bucket.geometry_type == "Point":
                        has_texts = any(
                            e.geometry_kind == "Text" for e in bucket.entities)
                        if has_texts:
                            try:
                                CadStylingEngine.apply_buffered_labels(
                                    processed_layer)
                            except Exception:
                                pass

                    layers.append(processed_layer)

            if layers:
                layer_groups.append(
                    LayerGroup(
                        name=group_name,
                        layers=layers))

        return layer_groups

    def _create_temp_vector_layer(
        self,
        layer_name: str,
        geometry_type: str,
        entities: list[NetcadEntity],
        crs: QgsCoordinateReferenceSystem,
        source_file_name: str,
        entity_source_files: dict[int, str] | None = None
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
                coords = CadCleanupEngine.clean_duplicates(coords)

            if self.chk_ncz_simplify.isChecked() and len(coords) > 3:
                coords = CadCleanupEngine.simplify_collinear(coords)

            geom = self._coords_to_geometry(
                entity.geometry_kind,
                geometry_type,
                coords,
                entity.radius,
                entity.start_angle,
                entity.end_angle,
                entity.is_closed,
            )
            if not geom or geom.isEmpty():
                continue

            source_value = source_file_name
            if entity_source_files:
                source_value = entity_source_files.get(
                    id(entity), source_file_name)

            feature = QgsFeature(layer.fields())
            feature.setGeometry(geom)
            feature.setAttributes([
                source_value,
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

        add_features_or_raise(
            layer, features, f"NCZ geometry layer {layer_name}")
        return layer

    def _create_temp_attribute_layer(
            self,
            table_name: str,
            table: NetcadAttributeTable,
            source_file_name: str) -> QgsVectorLayer | None:
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

        ordered_dynamic_names = sorted(
            name for name in field_names if name not in {
                "source_file", "table_ref", "row_index"})

        fields = [
            QgsField("source_file", QVariant.String),
            QgsField("table_ref", QVariant.String),
            QgsField("row_index", QVariant.Int),
        ]
        for name in ordered_dynamic_names:
            fields.append(
                QgsField(
                    name,
                    column_types.get(
                        name,
                        QVariant.String)))

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

        add_features_or_raise(
            layer, features, f"NCZ attribute table {table_name}")
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

    def _coords_to_geometry(
        self,
        geometry_kind: str,
        geometry_type: str,
        coords: list,
        radius: float,
        start_angle: float,
        end_angle: float,
        is_closed: bool,
    ) -> QgsGeometry | None:
        if geometry_type == "Point":
            if not coords:
                return None
            pt = coords[0]
            return QgsGeometry.fromPointXY(QgsPointXY(pt.x, pt.y))

        if geometry_type == "LineString":
            if geometry_kind == "Arc":
                if not coords:
                    return None
                arc_points = self._approximate_arc(
                    coords[0], radius, start_angle, end_angle)
                if len(arc_points) < 2:
                    return None
                return QgsGeometry.fromPolylineXY(arc_points)
            if len(coords) < 2:
                return None
            return QgsGeometry.fromPolylineXY(
                [QgsPointXY(c.x, c.y) for c in coords])

        if geometry_type == "Polygon":
            if geometry_kind == "Circle":
                if not coords:
                    return None
                ring = self._approximate_circle(coords[0], radius)
                return QgsGeometry.fromPolygonXY([ring])

            ring = [QgsPointXY(c.x, c.y) for c in coords]
            if len(ring) < 3:
                return None

            force_close = is_closed or geometry_kind in {
                "Box", "Triangle", "MapSheet", "SmartObject"}
            ring = CadCleanupEngine.close_polyline(
                ring,
                self.spin_ncz_tolerance.value(),
                force=force_close,
            )

            if len(ring) < 4:
                return None
            return QgsGeometry.fromPolygonXY([ring])

        return None

    def _approximate_circle(
            self,
            center,
            radius,
            segments=72) -> list[QgsPointXY]:
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

    def _approximate_arc(
            self,
            center,
            radius,
            start_angle,
            end_angle) -> list[QgsPointXY]:
        if radius <= 0:
            return []

        start = self._angle_to_radians(start_angle)
        end = self._angle_to_radians(end_angle)
        if abs(end - start) <= 1e-9:
            end = start + (2.0 * math.pi)
        while end < start:
            end += 2.0 * math.pi

        span = end - start
        segments = max(8, min(96, int(abs(span) / (math.pi / 24.0)) + 1))
        return [
            QgsPointXY(
                center.x + math.cos(start + (span * index / segments)) * radius,
                center.y + math.sin(start + (span * index / segments)) * radius,
            )
            for index in range(segments + 1)
        ]

    def _angle_to_radians(self, angle: float) -> float:
        if abs(angle) <= (2.0 * math.pi) + 1e-6:
            return float(angle)
        return math.radians(angle)

    # ───────────────────────── Join Relations ─────────────────────────

    def _join_attributes_to_layers(
            self,
            layer_groups: list[LayerGroup],
            base_name: str) -> None:
        all_layers = {}
        for group in layer_groups:
            for layer in group.layers:
                all_layers[layer.name()] = layer

        tables = {
            name: layer for name,
            layer in all_layers.items() if "_TABLE" in name}
        geom_layers = {
            name: layer for name,
            layer in all_layers.items() if "_TABLE" not in name}

        for tab_name, tab_layer in tables.items():
            ref_name = tab_name.replace(
                "_TABLE", "").replace(
                f"{base_name}_", "")

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
                    dynamic = [
                        f for f in tab_fields if f not in (
                            "source_file", "table_ref", "row_index")]
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

    # ───────────────────────── TAB 3: EXPORTER CONTROLS ─────────────────────

    def _populate_layers_combo(self) -> None:
        """Fills vector layers into exporter combobox."""
        self.cmb_exp_layer.clear()
        layers = QgsProject.instance().mapLayers().values()
        for layer in layers:
            if isinstance(layer, QgsVectorLayer) and layer.isValid():
                self.cmb_exp_layer.addItem(layer.name(), layer.id())
        self._update_export_button_state()

    def _on_export_format_changed(self, index: int) -> None:
        self.txt_exp_path.clear()
        self._update_export_button_state()

    def _last_export_dir(self) -> str:
        """Return the last export folder, falling back to the user home."""
        value = QSettings().value("zero2cadgis/last_export_dir", "")
        return value if isinstance(value, str) and os.path.isdir(value) else os.path.expanduser("~")

    def _last_import_dir(self) -> str:
        """Return the last import (source dataset) folder, falling back to the user home."""
        value = QSettings().value("zero2cadgis/last_import_dir", "")
        return value if isinstance(value, str) and os.path.isdir(value) else os.path.expanduser("~")

    def _remember_import_dir(self, file_path: str) -> None:
        folder = file_path if os.path.isdir(file_path) else os.path.dirname(file_path)
        if folder and os.path.isdir(folder):
            QSettings().setValue("zero2cadgis/last_import_dir", folder)

    def _browse_export_destination(self) -> None:
        idx = self.cmb_exp_format.currentIndex()
        if idx == 0:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export to DXF Drawing", self._last_export_dir(), "AutoCAD DXF (*.dxf)"
            )
            file_path = ensure_extension(file_path, ".dxf")
        elif idx == 1:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export to KML File", self._last_export_dir(), "Google Earth KML (*.kml)"
            )
            file_path = ensure_extension(file_path, ".kml")
        else:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export to KMZ Package", self._last_export_dir(), "Google Earth KMZ (*.kmz)"
            )
            file_path = ensure_extension(file_path, ".kmz")

        if file_path:
            self.txt_exp_path.setText(file_path)
            QSettings().setValue("zero2cadgis/last_export_dir", os.path.dirname(file_path))
            self._update_export_button_state()

    def _update_export_button_state(self) -> None:
        has_layer = self.cmb_exp_layer.currentIndex() >= 0
        has_path = bool(self.txt_exp_path.text().strip())
        self.btn_run_export.setEnabled(has_layer and has_path)

    def _run_export_layer(self) -> None:
        layer_id = self.cmb_exp_layer.currentData()
        output_path = self.txt_exp_path.text()
        format_idx = self.cmb_exp_format.currentIndex()

        layer = QgsProject.instance().mapLayer(layer_id)
        if not layer or not isinstance(layer, QgsVectorLayer):
            QMessageBox.warning(
                self,
                "Export Warning",
                "Source layer is no longer valid.")
            return

        try:
            success = False
            if format_idx == 0:  # DXF
                success = CadExportEngine.export_layer_to_dxf(
                    layer, output_path)
            elif format_idx == 1:  # KML
                success = GisConverterEngine.export_layer_to_gis(
                    layer, output_path, "KML")
            else:  # KMZ
                success = GisConverterEngine.export_layer_to_gis(
                    layer, output_path, "KMZ")

            if success:
                QMessageBox.information(
                    self,
                    "Success",
                    f"Successfully exported layer to drawing format!\nPath: {output_path}"
                )
            else:
                raise ValueError(
                    "Engine reported export failure (check coordinate compatibility).")

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed exporting QGIS layer:\n{exc}")
