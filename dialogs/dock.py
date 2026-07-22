# -*- coding: utf-8 -*-
# NCZ-specific layer-building and geometry-conversion portions of this file
# are derived from Jeomatik NCZ Reader.
# Copyright (C) 2026 Erdinç Örsan ÜNAL
# Original source: https://github.com/erdincunal/Jeomatik-NCZ-Reader
#
# Modified and extended for 02CadGis beginning 2026-07-04.
# Modifications Copyright (C) 2026 Yusuf Eminoğlu
# See THIRD_PARTY_NOTICES.md and LICENSE for details.
# SPDX-License-Identifier: GPL-2.0-or-later
"""zero2cadgis — Tabbed DockWidget Controller.
100% English, fully integrated with core CAD/GIS engines.
Includes dynamic Exporter module and GroundOverlay extraction.
"""
from __future__ import annotations

import os
import re
import math
from contextlib import suppress
from dataclasses import dataclass, field

from qgis.PyQt.QtCore import QMetaType, Qt, QSettings
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import (
    QApplication,
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
    QTabWidget,
    QComboBox,
    QDialog,
    QTextBrowser,
    QDialogButtonBox,
    QScrollArea,
)
from qgis.core import (
    Qgis,
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
from ..core.netcad_parser import (
    NetcadAttributeTable,
    NetcadEntity,
    NetcadLazyReader,
)
from ..core.gis_engine import GisConverterEngine
from ..core.csv_sniffer import (
    CsvGeometryProfile,
    sniff_delimited_dataset,
)
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


@dataclass(frozen=True)
class SourceFormat:
    """One selectable source dataset family in the converter tab."""
    key: str
    label: str
    dialog_title: str
    file_filter: str
    extensions: tuple[str, ...]
    is_dir: bool = False


SOURCE_FORMATS: list[SourceFormat] = [
    SourceFormat("dxf", "DXF (*.dxf)", "Select DXF File",
                 "AutoCAD DXF (*.dxf)", (".dxf",)),
    SourceFormat("kml", "KML / KMZ (*.kml, *.kmz)", "Select KML or KMZ File",
                 "Keyhole Markup Language (*.kml *.kmz)", (".kml", ".kmz")),
    SourceFormat("gml", "GML (*.gml)", "Select GML File",
                 "Geography Markup Language (*.gml)", (".gml",)),
    SourceFormat("geojson", "GeoJSON (*.geojson, *.json)",
                 "Select GeoJSON File",
                 "GeoJSON (*.geojson *.json)", (".geojson", ".json")),
    SourceFormat("csv", "Delimited Text / CSV (*.csv, *.tsv, *.txt)",
                 "Select Delimited Text File",
                 "Delimited Text (*.csv *.tsv *.txt)",
                 (".csv", ".tsv", ".txt")),
    SourceFormat("sqlite", "SpatiaLite / SQLite (*.sqlite, *.db)",
                 "Select SpatiaLite or SQLite Database",
                 "SpatiaLite / SQLite (*.sqlite *.db)", (".sqlite", ".db")),
    SourceFormat("gpx", "GPS Exchange GPX (*.gpx)", "Select GPX File",
                 "GPS Exchange Format (*.gpx)", (".gpx",)),
    SourceFormat("dgn", "Microstation DGN (*.dgn)",
                 "Select Microstation DGN File",
                 "Design Files (*.dgn)", (".dgn",)),
    SourceFormat("gdb", "ArcGIS File Geodatabase (*.gdb)",
                 "Select ArcGIS File Geodatabase Directory",
                 "", (".gdb",), is_dir=True),
    SourceFormat("mdb", "ArcGIS Personal Geodatabase (*.mdb)",
                 "Select ArcGIS Personal Geodatabase File",
                 "ArcGIS Personal Geodatabase (*.mdb)", (".mdb",)),
]

NCZ_EXTENSIONS = (".ncz", ".nca")


def format_for_path(path: str) -> SourceFormat | None:
    """Return the SourceFormat matching *path*'s extension, if any."""
    lower = path.lower().rstrip("\\/")
    for fmt in SOURCE_FORMATS:
        if any(lower.endswith(ext) for ext in fmt.extensions):
            return fmt
    return None


def all_supported_filter() -> str:
    exts = " ".join(
        f"*{ext}" for fmt in SOURCE_FORMATS if not fmt.is_dir
        for ext in fmt.extensions)
    return f"All supported ({exts})"


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
        QgsField("source_file", QMetaType.Type.QString),
        QgsField("layer_code", QMetaType.Type.Int),
        QgsField("layer_name", QMetaType.Type.QString),
        QgsField("entity_type", QMetaType.Type.QString),
        QgsField("name", QMetaType.Type.QString),
        QgsField("label", QMetaType.Type.QString),
        QgsField("color_argb", QMetaType.Type.QString),
        QgsField("radius", QMetaType.Type.Double),
        QgsField("start_ang", QMetaType.Type.Double),
        QgsField("end_ang", QMetaType.Type.Double),
        QgsField("text_h", QMetaType.Type.Double),
        QgsField("rotation", QMetaType.Type.Double),
        QgsField("box_width", QMetaType.Type.Double),
        QgsField("box_height", QMetaType.Type.Double),
        QgsField("scale", QMetaType.Type.Double),
        QgsField("grid_x", QMetaType.Type.Double),
        QgsField("grid_y", QMetaType.Type.Double),
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
        self.ncz_readers: dict[str, NetcadLazyReader] = {}
        self.gis_converter = None
        self.src_csv_profile: CsvGeometryProfile | None = None

        self._build_ui()
        self._restore_persistent_options()
        self.setAcceptDrops(True)

        project = QgsProject.instance()
        with suppress(Exception):
            project.layersAdded.connect(self._populate_layers_combo)
            project.layersRemoved.connect(self._populate_layers_combo)

    def closeEvent(self, event):
        if self.gis_converter:
            self.gis_converter.cleanup()
        super().closeEvent(event)

    # ───────────────────────── Drag & drop ─────────────────────────

    def dragEnterEvent(self, event):
        if self._droppable_paths(event):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        paths = self._droppable_paths(event)
        if not paths:
            event.ignore()
            return
        event.acceptProposedAction()

        ncz_paths = [p for p in paths
                     if p.lower().endswith(NCZ_EXTENSIONS)]
        if ncz_paths:
            self.main_tab.setCurrentIndex(1)
            self._load_ncz_paths(ncz_paths)
            return

        fmt = format_for_path(paths[0])
        if fmt is None:
            return
        self.main_tab.setCurrentIndex(0)
        self._apply_source_path(paths[0], fmt)

    def _droppable_paths(self, event) -> list[str]:
        mime = event.mimeData()
        if not mime.hasUrls():
            return []
        paths = []
        for url in mime.urls():
            local = url.toLocalFile()
            if not local:
                continue
            if local.lower().endswith(NCZ_EXTENSIONS) \
                    or format_for_path(local) is not None:
                paths.append(local)
        return paths

    # ───────────────────────── Option persistence ─────────────────────────

    _PERSISTENT_CHECKBOXES = (
        "chk_conv_simplify", "chk_conv_clean", "chk_conv_kml_expand",
        "chk_conv_raster", "chk_conv_load", "chk_ncz_simplify",
        "chk_ncz_clean", "chk_ncz_augment", "chk_ncz_style",
        "chk_ncz_label", "chk_ncz_join",
    )

    def _restore_persistent_options(self) -> None:
        settings = QSettings()
        for name in self._PERSISTENT_CHECKBOXES:
            widget = getattr(self, name, None)
            if widget is None:
                continue
            stored = settings.value(f"zero2cadgis/opts/{name}")
            if stored is not None:
                widget.setChecked(str(stored).lower() in ("true", "1"))
            widget.toggled.connect(
                lambda checked, key=name: QSettings().setValue(
                    f"zero2cadgis/opts/{key}", checked))
        stored_tol = settings.value("zero2cadgis/opts/ncz_tolerance")
        if stored_tol is not None:
            with suppress(TypeError, ValueError):
                self.spin_ncz_tolerance.setValue(float(stored_tol))
        self.spin_ncz_tolerance.valueChanged.connect(
            lambda value: QSettings().setValue(
                "zero2cadgis/opts/ncz_tolerance", value))

    def _build_ui(self) -> None:
        self.main_tab = main_tab = QTabWidget()

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
        for fmt in SOURCE_FORMATS:
            self.cmb_src_type.addItem(fmt.label, fmt.key)
        self.cmb_src_type.insertSeparator(self.cmb_src_type.count())
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
            "Select or drop a drawing / GIS dataset...")
        path_layout.addWidget(self.txt_src_path)

        self.btn_browse_src = QPushButton("Browse...")
        self.btn_browse_src.setObjectName("browse_btn")
        self.btn_browse_src.clicked.connect(self._browse_src_dataset)
        path_layout.addWidget(self.btn_browse_src)
        src_layout.addLayout(path_layout)

        self.lbl_src_status = QLabel(
            "Tip: drag && drop any supported file onto this panel.")
        self.lbl_src_status.setObjectName("dock_subtitle")
        self.lbl_src_status.setWordWrap(True)
        src_layout.addWidget(self.lbl_src_status)
        cad_gis_layout.addWidget(src_group)

        # Delimited text geometry (visible only for CSV/TSV/TXT sources)
        self.csv_group = QGroupBox("Delimited Text Geometry")
        csv_form = QFormLayout(self.csv_group)
        csv_form.setContentsMargins(6, 10, 6, 6)
        csv_form.setSpacing(3)

        self.lbl_csv_summary = QLabel("-")
        self.lbl_csv_summary.setWordWrap(True)
        csv_form.addRow("Detected:", self.lbl_csv_summary)

        self.cmb_csv_x = QComboBox()
        csv_form.addRow("X / Longitude Field:", self.cmb_csv_x)
        self.cmb_csv_y = QComboBox()
        csv_form.addRow("Y / Latitude Field:", self.cmb_csv_y)
        self.cmb_csv_wkt = QComboBox()
        self.cmb_csv_wkt.setToolTip(
            "When a WKT column is chosen it overrides the X/Y fields.")
        csv_form.addRow("WKT Geometry Field:", self.cmb_csv_wkt)

        self.csv_src_crs = QgsProjectionSelectionWidget()
        self.csv_src_crs.setOptionVisible(
            QgsProjectionSelectionWidget.CrsOption.ProjectCrs, True)
        csv_form.addRow("Source CRS:", self.csv_src_crs)

        self.csv_group.setVisible(False)
        cad_gis_layout.addWidget(self.csv_group)

        # Source layer preview (populated after a dataset is chosen)
        self.src_preview_group = QGroupBox("Layers Found in Source")
        src_preview_layout = QVBoxLayout(self.src_preview_group)
        src_preview_layout.setContentsMargins(4, 8, 4, 4)
        src_preview_layout.setSpacing(2)

        self.src_layer_tree = QTreeWidget()
        self.src_layer_tree.setHeaderLabels(
            ["Layer Name", "Geometry", "Features"])
        self.src_layer_tree.setColumnWidth(0, 150)
        self.src_layer_tree.setColumnWidth(1, 90)
        self.src_layer_tree.setRootIsDecorated(False)
        self.src_layer_tree.setMinimumHeight(90)
        src_preview_layout.addWidget(self.src_layer_tree)

        src_sel_layout = QHBoxLayout()
        src_sel_layout.setSpacing(4)
        btn_src_all = QPushButton("Select All")
        btn_src_all.clicked.connect(
            lambda: self._set_src_tree_checked(Qt.CheckState.Checked))
        btn_src_none = QPushButton("Deselect All")
        btn_src_none.clicked.connect(
            lambda: self._set_src_tree_checked(Qt.CheckState.Unchecked))
        src_sel_layout.addWidget(btn_src_all)
        src_sel_layout.addWidget(btn_src_none)
        src_preview_layout.addLayout(src_sel_layout)

        self.src_preview_group.setVisible(False)
        cad_gis_layout.addWidget(self.src_preview_group)

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
        subtitle = QLabel("CAD, KML, GML, CSV, DGN and GDB conversion studio")
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
        <p>Use 02CadGis when you need QGIS-ready GeoPackage layers from CAD, KML/KMZ, GML, GeoJSON, CSV, SpatiaLite, GPX, DGN, GDB, or Netcad drawing data.</p>
        <p><b>Fastest path:</b> drag &amp; drop any supported file onto the dock. The dataset type is detected from the extension, source layers are listed for review, and Netcad files jump straight to the NCZ tab.</p>

        <h3>1. Convert CAD or GIS to GeoPackage</h3>
        <ol>
          <li>Choose the source family: DXF, KML/KMZ, GML, GeoJSON, CSV/TSV, SpatiaLite/SQLite, GPX, DGN, FileGDB, or Personal GDB. DWG is listed as a future enhancement because current QGIS/GDAL builds only read limited DWG versions.</li>
          <li>Select the source file or `.gdb` folder — or just drop the file on the panel.</li>
          <li>Review <b>Layers Found in Source</b> and uncheck anything you do not need.</li>
          <li>For delimited text, check the <b>Delimited Text Geometry</b> card: the delimiter and X/Y or WKT columns are auto-detected and can be overridden, and the source CRS defaults to EPSG:4326 for lon/lat columns.</li>
          <li>Choose a target `.gpkg` (a name is pre-suggested from the source), or enable temporary scratch layers when you only want to inspect the result.</li>
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

    def _current_source_format(self) -> SourceFormat | None:
        key = self.cmb_src_type.currentData()
        for fmt in SOURCE_FORMATS:
            if fmt.key == key:
                return fmt
        return None

    def _on_source_type_changed(self, index: int) -> None:
        self.txt_src_path.clear()
        self.btn_convert_gis.setEnabled(False)
        fmt = self._current_source_format()
        is_kml = fmt is not None and fmt.key == "kml"
        self.chk_conv_kml_expand.setEnabled(is_kml)
        self.chk_conv_raster.setEnabled(is_kml)
        self.csv_group.setVisible(fmt is not None and fmt.key == "csv")
        self.src_layer_tree.clear()
        self.src_preview_group.setVisible(False)
        self.src_csv_profile = None
        self.lbl_src_status.setText(
            "Tip: drag && drop any supported file onto this panel.")

    def _browse_src_dataset(self) -> None:
        fmt = self._current_source_format()
        start_dir = self._last_import_dir()
        if fmt is None:
            QMessageBox.information(
                self,
                "Future Enhancement",
                "DWG import needs broader CAD reader support than the current QGIS/GDAL libopencad driver provides. Convert DWG to DXF first.")
            return

        if fmt.is_dir:
            file_path = QFileDialog.getExistingDirectory(
                self, fmt.dialog_title, start_dir,
                QFileDialog.Option.ShowDirsOnly)
            if file_path and not has_extension(file_path, ".gdb"):
                QMessageBox.warning(
                    self,
                    "Invalid Folder",
                    "Please select a directory ending with '.gdb'.")
                return
        else:
            dialog_filter = (
                f"{fmt.file_filter};;{all_supported_filter()};;All Files (*.*)")
            file_path, _ = QFileDialog.getOpenFileName(
                self, fmt.dialog_title, start_dir, dialog_filter)
            if file_path and format_for_path(file_path) is None:
                if file_path.lower().endswith(".dwg"):
                    QMessageBox.warning(
                        self,
                        "Unsupported Drawing Version",
                        "DWG import is a future enhancement in this QGIS/GDAL build. Convert DWG to DXF first, then import the DXF file.")
                    return

        if not file_path:
            return
        detected = format_for_path(file_path) or fmt
        self._apply_source_path(file_path, detected)

    def _apply_source_path(self, file_path: str, fmt: SourceFormat) -> None:
        """Set the source path/type and refresh the layer preview."""
        target_index = self.cmb_src_type.findData(fmt.key)
        if target_index >= 0 and target_index != self.cmb_src_type.currentIndex():
            self.cmb_src_type.blockSignals(True)
            self.cmb_src_type.setCurrentIndex(target_index)
            self.cmb_src_type.blockSignals(False)
            is_kml = fmt.key == "kml"
            self.chk_conv_kml_expand.setEnabled(is_kml)
            self.chk_conv_raster.setEnabled(is_kml)
            self.csv_group.setVisible(fmt.key == "csv")

        self.txt_src_path.setText(file_path)
        self._remember_import_dir(file_path)
        self._suggest_gpkg_destination(file_path)
        self._refresh_source_preview(file_path, fmt)
        self._update_convert_gis_button_state()

    def _suggest_gpkg_destination(self, source_path: str) -> None:
        """Prefill the target GPKG from the source name when still empty."""
        if self.txt_gpkg_path.text().strip() \
                or self.chk_conv_temporary.isChecked():
            return
        stem = os.path.splitext(os.path.basename(
            source_path.rstrip("\\/")))[0] or "converted"
        suggestion = os.path.join(self._last_export_dir(), f"{stem}.gpkg")
        self.txt_gpkg_path.setText(suggestion)

    def _refresh_source_preview(self, file_path: str,
                                fmt: SourceFormat) -> None:
        self.src_layer_tree.clear()
        self.src_csv_profile = None
        try:
            if fmt.key == "csv":
                self.src_csv_profile = sniff_delimited_dataset(file_path)
                self._populate_csv_controls(self.src_csv_profile)

            probe = GisConverterEngine(
                file_path, "", QgsProject.instance().crs(),
                csv_profile=self.src_csv_profile)
            infos = probe.discover_layers(
                is_kmz=has_extension(file_path, ".kmz"))
            probe.cleanup()
        except Exception as exc:
            self.src_preview_group.setVisible(False)
            self.lbl_src_status.setText(f"Could not inspect dataset: {exc}")
            return

        for info in infos:
            item = QTreeWidgetItem(self.src_layer_tree)
            item.setText(0, info.name)
            item.setText(1, info.geometry)
            item.setText(2, "?" if info.feature_count < 0
                         else str(info.feature_count))
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(0, Qt.CheckState.Checked)
            item.setData(0, Qt.ItemDataRole.UserRole, info.name)

        self.src_preview_group.setVisible(bool(infos))
        total = sum(max(info.feature_count, 0) for info in infos)
        self.lbl_src_status.setText(
            f"{len(infos)} layer(s) discovered, ~{total} features. "
            "Uncheck layers you do not need before converting.")

    def _populate_csv_controls(self, profile: CsvGeometryProfile) -> None:
        for combo in (self.cmb_csv_x, self.cmb_csv_y, self.cmb_csv_wkt):
            combo.blockSignals(True)
            combo.clear()
            combo.addItem("(none)", "")
            for name in profile.fields:
                combo.addItem(name, name)
            combo.blockSignals(False)

        def select(combo: QComboBox, value: str) -> None:
            index = combo.findData(value)
            combo.setCurrentIndex(index if index >= 0 else 0)

        select(self.cmb_csv_x, profile.x_field)
        select(self.cmb_csv_y, profile.y_field)
        select(self.cmb_csv_wkt, profile.wkt_field)

        if profile.crs_authid:
            crs = QgsCoordinateReferenceSystem(profile.crs_authid)
            if crs.isValid():
                self.csv_src_crs.setCrs(crs)
        elif not self.csv_src_crs.crs().isValid():
            self.csv_src_crs.setCrs(QgsProject.instance().crs())

        self.lbl_csv_summary.setText(
            f"Delimiter '{profile.delimiter}' — {profile.geometry_summary}")

    def _effective_csv_profile(self) -> CsvGeometryProfile | None:
        """CSV profile with the user's current field overrides applied."""
        if self.src_csv_profile is None:
            return None
        profile = CsvGeometryProfile(
            delimiter=self.src_csv_profile.delimiter,
            fields=list(self.src_csv_profile.fields),
            x_field=self.cmb_csv_x.currentData() or "",
            y_field=self.cmb_csv_y.currentData() or "",
            wkt_field=self.cmb_csv_wkt.currentData() or "",
            crs_authid=self.src_csv_profile.crs_authid,
            row_count=self.src_csv_profile.row_count,
        )
        if profile.wkt_field:
            profile.x_field = ""
            profile.y_field = ""
        return profile

    def _selected_source_layers(self) -> list[str] | None:
        """Checked layer names from the preview tree; None = everything."""
        count = self.src_layer_tree.topLevelItemCount()
        if count == 0:
            return None
        selected = []
        for index in range(count):
            item = self.src_layer_tree.topLevelItem(index)
            if item.checkState(0) == Qt.CheckState.Checked:
                selected.append(item.data(0, Qt.ItemDataRole.UserRole))
        return selected

    def _set_src_tree_checked(self, state: Qt.CheckState) -> None:
        for index in range(self.src_layer_tree.topLevelItemCount()):
            self.src_layer_tree.topLevelItem(index).setCheckState(0, state)

    def _browse_gpkg_destination(self) -> None:
        start = self.txt_gpkg_path.text().strip() or self._last_export_dir()
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Select Output GeoPackage", start, "GeoPackage (*.gpkg)"
        )
        if file_path:
            file_path = ensure_extension(file_path, ".gpkg")
            self.txt_gpkg_path.setText(file_path)
            QSettings().setValue(
                "zero2cadgis/last_export_dir", os.path.dirname(file_path))
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
        fmt = self._current_source_format()
        if fmt is None:
            QMessageBox.information(
                self,
                "Future Enhancement",
                "DWG import is planned for a future enhancement. Convert DWG to DXF first.")
            return

        selected_layers = self._selected_source_layers()
        if selected_layers is not None and not selected_layers:
            QMessageBox.warning(
                self, "Warning",
                "Please check at least one source layer to convert.")
            return

        crs = self.converter_crs.crs()
        if not crs.isValid():
            crs = QgsProject.instance().crs()

        self.progress_conv.setVisible(True)
        self.progress_conv.setValue(5)
        self.progress_conv.setFormat("Initializing GIS Converter...")
        QApplication.processEvents()

        try:
            is_kml = fmt.key == "kml"
            is_kmz = is_kml and has_extension(src, ".kmz")
            is_temp = self.chk_conv_temporary.isChecked()

            csv_profile = None
            csv_crs = ""
            if fmt.key == "csv":
                csv_profile = self._effective_csv_profile()
                if self.csv_src_crs.crs().isValid():
                    csv_crs = self.csv_src_crs.crs().authid()

            self.gis_converter = GisConverterEngine(
                src, dst, crs,
                csv_profile=csv_profile, csv_source_crs=csv_crs)

            layer_total = max(
                len(selected_layers) if selected_layers is not None else 1, 1)
            progress_state = {"done": 0}

            def layer_progress(layer_name: str) -> None:
                progress_state["done"] += 1
                share = min(progress_state["done"] / layer_total, 1.0)
                self.progress_conv.setValue(10 + int(share * 55))
                self.progress_conv.setFormat(f"Converting {layer_name}...")
                QApplication.processEvents()

            if is_temp:
                loaded_layers = self.gis_converter.convert_to_memory(
                    is_kmz=is_kmz,
                    html_expansion=self.chk_conv_kml_expand.isChecked(),
                    selected_layers=selected_layers,
                    progress_cb=layer_progress,
                )
            else:
                loaded_layers = self.gis_converter.convert(
                    is_kmz=is_kmz,
                    html_expansion=self.chk_conv_kml_expand.isChecked(),
                    selected_layers=selected_layers,
                    progress_cb=layer_progress,
                )

            # GroundOverlay Extraction
            if self.chk_conv_raster.isChecked() and is_kml:
                self.progress_conv.setValue(70)
                self.progress_conv.setFormat(
                    "Extracting KML GroundOverlays (kmltools feyz)...")
                QApplication.processEvents()
                raster_layers = self.gis_converter.extract_ground_overlays(
                    is_kmz=is_kmz)
                for rl in raster_layers:
                    QgsProject.instance().addMapLayer(rl)

            self.progress_conv.setValue(85)
            self.progress_conv.setFormat("Adding vector layers to canvas...")
            QApplication.processEvents()

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

            destination = ("temporary scratch layers" if is_temp
                           else os.path.basename(dst))
            self.iface.messageBar().pushMessage(
                "02CadGis",
                f"Converted {len(loaded_layers)} layer(s) from "
                f"{os.path.basename(src.rstrip(chr(92) + '/'))} to {destination}.",
                Qgis.MessageLevel.Success, 7)

            notes = getattr(self.gis_converter, "last_warnings", [])
            for note in notes:
                self.iface.messageBar().pushMessage(
                    "02CadGis", note, Qgis.MessageLevel.Warning, 10)

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
        self._load_ncz_paths(file_paths)

    def _load_ncz_paths(self, file_paths: list[str]) -> None:
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

        self.ncz_readers = {}
        total_records = 0
        total_tables = 0
        versions = set()
        projections = set()
        epsg_codes = set()

        self.progress_ncz.setVisible(True)
        self.progress_ncz.setValue(10)
        self.progress_ncz.setFormat("Indexing selected Netcad drawings...")

        try:
            for idx, file_path in enumerate(file_paths):
                self.progress_ncz.setValue(
                    10 + int((idx / len(file_paths)) * 50))
                self.progress_ncz.setFormat(
                    f"Indexing {os.path.basename(file_path)}...")
                QApplication.processEvents()

                # Index only: metadata + layer catalog, no geometry decode.
                reader = NetcadLazyReader(file_path).index()
                self.ncz_readers[file_path] = reader

                total_records += sum(
                    s.record_count for s in reader.layer_summaries())
                total_tables += len(reader.attribute_tables())
                if reader.version_name:
                    versions.add(reader.version_name)
                if reader.projection_text:
                    projections.add(reader.projection_text)
                if reader.epsg:
                    epsg_codes.add(reader.epsg)

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
                f"{total_records} records / {total_tables} attribute tables "
                f"across {len(file_paths)} files (layers decoded on import)")

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
        if not self.ncz_readers:
            return

        for file_path, reader in sorted(self.ncz_readers.items()):
            file_name = os.path.basename(file_path)

            # 1. File Root Item
            file_item = QTreeWidgetItem(self.ncz_layer_tree)
            file_item.setText(0, file_name)
            file_item.setData(0, Qt.ItemDataRole.UserRole, file_path)
            file_item.setFlags(file_item.flags(
            ) | Qt.ItemFlag.ItemIsAutoTristate | Qt.ItemFlag.ItemIsUserCheckable)
            file_item.setCheckState(0, Qt.CheckState.Checked)
            file_item.setExpanded(True)

            # CAD Layers subroot — one leaf per layer, from the catalog
            summaries = reader.layer_summaries()
            if summaries:
                cad_root = QTreeWidgetItem(file_item)
                cad_root.setText(0, "CAD Layers")
                cad_root.setFlags(
                    cad_root.flags() | Qt.ItemFlag.ItemIsAutoTristate | Qt.ItemFlag.ItemIsUserCheckable)
                cad_root.setCheckState(0, Qt.CheckState.Checked)
                cad_root.setExpanded(True)

                for summary in sorted(summaries, key=lambda s: s.layer_name):
                    item = QTreeWidgetItem(cad_root)
                    item.setText(0, summary.layer_name)
                    item.setText(1, "/".join(sorted(summary.families)))
                    item.setText(2, str(summary.record_count))
                    item.setFlags(
                        item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                    item.setCheckState(0, Qt.CheckState.Checked)
                    item.setData(0, Qt.ItemDataRole.UserRole,
                                 ("LAYER", summary.layer_code,
                                  summary.layer_name))

            # Attribute Tables subroot
            tables = reader.attribute_tables()
            if tables:
                table_root = QTreeWidgetItem(file_item)
                table_root.setText(0, "Attribute Tables (@TAB)")
                table_root.setFlags(table_root.flags(
                ) | Qt.ItemFlag.ItemIsAutoTristate | Qt.ItemFlag.ItemIsUserCheckable)
                table_root.setCheckState(0, Qt.CheckState.Checked)
                table_root.setExpanded(True)

                for table in tables:
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
        if not self.ncz_readers:
            return

        try:
            self.progress_ncz.setVisible(True)
            self.progress_ncz.setValue(10)
            self.progress_ncz.setFormat("Filtering selected layers...")
            QApplication.processEvents()

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
                            if not data:
                                continue
                            if data[0] == "TABLE":
                                selected_by_file[file_path]["tables"].append(
                                    data[1])
                            elif data[0] == "LAYER":
                                # (code, name)
                                selected_by_file[file_path]["layers"].append(
                                    (data[1], data[2]))

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
                list(self.ncz_readers.keys())[0]))[0]
            base_name = self._sanitize_name(f"{first_file}_BATCH") if len(
                self.ncz_readers) > 1 else self._sanitize_name(first_file)

            if is_temp:
                gpkg_path = ""
            else:
                suggested = os.path.join(
                    self._last_export_dir(), f"{base_name.lower()}.gpkg")
                gpkg_path, _ = QFileDialog.getSaveFileName(
                    self, "Select Output GeoPackage for Netcad Data",
                    suggested, "GeoPackage (*.gpkg)")
                if not gpkg_path:
                    self.progress_ncz.setVisible(False)
                    return
                gpkg_path = ensure_extension(gpkg_path, ".gpkg")
                QSettings().setValue(
                    "zero2cadgis/last_export_dir", os.path.dirname(gpkg_path))

            target_crs = self.ncz_crs_selector.crs()
            if not target_crs.isValid():
                target_crs = QgsProject.instance().crs()

            merge_enabled = self.chk_ncz_merge_geometry.isChecked()
            has_multiple_results = len(self.ncz_readers) > 1
            merge_geometry_types = merge_enabled and has_multiple_results
            layer_groups = []
            merged_entity_groups = {}
            transform_context = QgsProject.instance().transformContext()

            file_count = max(len(selected_by_file), 1)
            for file_index, (file_path, selection) in enumerate(
                    selected_by_file.items()):
                selected_layers = selection["layers"]
                selected_codes = {code for code, _name in selected_layers}
                selected_tables = selection["tables"]
                if not selected_codes and not selected_tables:
                    continue

                reader = self.ncz_readers[file_path]
                source_file_name = os.path.splitext(
                    os.path.basename(file_path))[0]
                file_base_name = self._sanitize_name(source_file_name)

                self.progress_ncz.setValue(
                    30 + int((file_index / file_count) * 45))
                self.progress_ncz.setFormat(
                    f"Decoding {len(selected_codes)} layer(s) of "
                    f"{os.path.basename(file_path)}...")
                QApplication.processEvents()

                # Selective decode: only the checked layers are materialized.
                decoded_entities = reader.decode_layers(selected_codes)

                grouped_entities = (
                    merged_entity_groups if merge_geometry_types else {})

                for entity in decoded_entities:
                    family, geometry_type = self._geometry_family(
                        entity.geometry_kind)
                    if not family:
                        continue

                    layer_name = entity.layer_name or f"LAYER_{entity.layer_code}"

                    if merge_geometry_types:
                        family_token = self._sanitize_name(family)
                        layer_token = self._sanitize_name(layer_name)
                        display_name = f"{base_name}_{layer_token}_{family_token}"
                        group_name = f"{base_name}_{family_token}"
                        bucket_key = (layer_token, family, geometry_type)
                    else:
                        display_name = f"{file_base_name}_{self._sanitize_name(layer_name)}_{family}"
                        group_name = f"{file_base_name}_{family}"
                        bucket_key = (entity.layer_code, layer_name, family)

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
                if selected_tables:
                    attribute_group_name = f"{file_base_name}_ATTRIBUTES"
                    attribute_layers = []
                    for table in reader.attribute_tables():
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
                message = "Netcad drawing imported as temporary scratch layers."
            else:
                message = ("Netcad drawing converted to "
                           f"{os.path.basename(gpkg_path)} and loaded.")
            self.iface.messageBar().pushMessage(
                "02CadGis", message, Qgis.MessageLevel.Success, 7)

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
                        with suppress(Exception):
                            augmented_layer = CadFeatureAugmenter.augment_layer(
                                temp_layer)
                            if augmented_layer.featureCount() == temp_layer.featureCount():
                                processed_layer = augmented_layer

                    if self.chk_ncz_style.isChecked():
                        with suppress(Exception):
                            CadStylingEngine.apply_argb_renderer(
                                processed_layer, bucket.geometry_type)

                    if self.chk_ncz_label.isChecked() and bucket.geometry_type == "Point":
                        has_texts = any(
                            e.geometry_kind == "Text" for e in bucket.entities)
                        if has_texts:
                            with suppress(Exception):
                                CadStylingEngine.apply_buffered_labels(
                                    processed_layer)

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
                    column_types.setdefault(key, QMetaType.Type.Int)
                elif isinstance(value, float):
                    column_types.setdefault(key, QMetaType.Type.Double)
                else:
                    column_types.setdefault(key, QMetaType.Type.QString)

        ordered_dynamic_names = sorted(
            name for name in field_names if name not in {
                "source_file", "table_ref", "row_index"})

        fields = [
            QgsField("source_file", QMetaType.Type.QString),
            QgsField("table_ref", QMetaType.Type.QString),
            QgsField("row_index", QMetaType.Type.Int),
        ]
        for name in ordered_dynamic_names:
            fields.append(
                QgsField(
                    name,
                    column_types.get(
                        name,
                        QMetaType.Type.QString)))

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
