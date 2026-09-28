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
import shutil
import time
import contextlib
from contextlib import suppress
from dataclasses import dataclass, field

from qgis.PyQt.QtCore import QMetaType, Qt, QSettings
from qgis.PyQt.QtGui import QBrush, QColor, QIcon
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
    QRadioButton,
    QButtonGroup,
    QDoubleSpinBox,
    QSpinBox,
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
    QgsCoordinateTransform,
    QgsRectangle,
    QgsVectorFileWriter,
    QgsLayoutItemMap,
    QgsWkbTypes,
    QgsMapLayerType,
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
from ..core.symbology import PlanSymbologyMatcher, apply_plan_symbology
from ..core.plangml_schema import lookup_tabaka, upper_group_of
from ..core.path_utils import ensure_extension, has_extension
from ..core.qgis_compat import (
    add_features_or_raise,
    fix_mojibake,
    memory_geometry_type_name,
)
from ..core.conversion_receipt import ConvertedLayer, build_conversion_receipt
from ..core.spatial_filter import (
    ExtentBox,
    ExtentInspectionResult,
    SUPPORTED_FILTER_EXTENSIONS,
    discover_files,
    inspect_file_extent,
    evaluate_qgis_spatial_match,
    scan_and_filter_files,
)

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

/* ── dialogs & sub-windows: pinned white so top-level child windows never
      render black on dark-themed QGIS or Windows ── */
QDialog {
    background-color: #ffffff;
    color: #263238;
}
QDialog QScrollArea,
QDialog QScrollArea > QWidget > QWidget {
    background-color: #ffffff;
}

/* ── group boxes ── */
QGroupBox {
    font-weight: bold;
    color: #37474f;
    background-color: #ffffff;
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
    background-color: #ffffff;
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
    alternate-background-color: #f8fafc;
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
    background-color: #cfd8dc;
    color: #546e7a;
    border: 1px solid #b0bec5;
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
    background: #eceff1;
    color: #78909c;
    border: 1px solid #cfd8dc;
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
    SourceFormat("dwg", "AutoCAD DWG (*.dwg)", "Select AutoCAD DWG File",
                 "AutoCAD DWG (*.dwg)", (".dwg",)),
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
    SourceFormat("mdb", "MS Access / Personal Geodatabase (*.accdb, *.mdb)",
                 "Select MS Access Database File",
                 "MS Access / Personal Geodatabase (*.accdb *.mdb)", (".accdb", ".mdb")),
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

    CAD_FIELD_DEFINITIONS = [
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

    PLANGML_FIELD_DEFINITIONS = [
        QgsField("UST_GRUP_ID", QMetaType.Type.QString),
        QgsField("UST_GRUP_ADI", QMetaType.Type.QString),
        QgsField("ALT_GRUP_ID", QMetaType.Type.QString),
        QgsField("ALT_GRUP_ADI", QMetaType.Type.QString),
        QgsField("PLAN_KODU", QMetaType.Type.QString),
        QgsField("FONKSIYON_KODU", QMetaType.Type.QString),
        QgsField("TAM_ADI", QMetaType.Type.QString),
        QgsField("GISTERIM", QMetaType.Type.QString),
        QgsField("uip_tabaka", QMetaType.Type.QString),
        QgsField("YapiDuzeni", QMetaType.Type.QString),
        QgsField("KatAdedi", QMetaType.Type.Int),
        QgsField("EmsalKaks", QMetaType.Type.Double),
        QgsField("Taks", QMetaType.Type.Double),
        QgsField("YapiYuksekligi", QMetaType.Type.Double),
        QgsField("Yencok", QMetaType.Type.QString),
        QgsField("OnBahceMesafesi", QMetaType.Type.Double),
        QgsField("YanBahceMesafesi", QMetaType.Type.Double),
        QgsField("ArkaBahceMesafesi", QMetaType.Type.Double),
        QgsField("AdaNo", QMetaType.Type.QString),
        QgsField("ParselNo", QMetaType.Type.QString),
        QgsField("YolGenisligi", QMetaType.Type.Double),
        QgsField("PlanNotu", QMetaType.Type.QString),
    ]

    FIELD_DEFINITIONS = CAD_FIELD_DEFINITIONS + PLANGML_FIELD_DEFINITIONS

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
        self._cad_split_field: str = ""
        self._export_selection_connections: set[str] = set()
        self._spatial_filter_results: list[ExtentInspectionResult] = []
        self._filter_discovered_files: list[str] = []
        self._poly_selection_connections: set[str] = set()

        self._build_ui()
        self._restore_persistent_options()
        self.setAcceptDrops(True)

        project = QgsProject.instance()
        with suppress(Exception):
            project.layersAdded.connect(self._populate_layers_combo)
            project.layersRemoved.connect(self._populate_layers_combo)
            if hasattr(self.iface, "mapCanvas") and self.iface.mapCanvas():
                self.iface.mapCanvas().extentsChanged.connect(
                    self._on_map_canvas_extent_changed)

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

        # If dropped a directory or multiple mixed files, open spatial filter sub-dialog
        if (any(os.path.isdir(p) and not p.lower().endswith(".gdb") for p in paths)
                or (len(paths) > 1 and not all(p.lower().endswith(NCZ_EXTENSIONS) for p in paths))):
            self._apply_filter_source_paths(paths)
            self.spatial_filter_dialog.show()
            self.spatial_filter_dialog.raise_()
            self.spatial_filter_dialog.activateWindow()
            return

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
            if (os.path.isdir(local)
                    or local.lower().endswith(NCZ_EXTENSIONS)
                    or local.lower().endswith(SUPPORTED_FILTER_EXTENSIONS)
                    or format_for_path(local) is not None):
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

        self.btn_cad_filter_extent = QPushButton("Filter by Extent...")
        self.btn_cad_filter_extent.setToolTip(
            "Filter candidate CAD & GIS datasets by current map canvas or boundary.")
        self.btn_cad_filter_extent.clicked.connect(
            self._filter_current_cad_by_extent)
        path_layout.addWidget(self.btn_cad_filter_extent)
        src_layout.addLayout(path_layout)

        self.lbl_src_status = QLabel(
            "Tip: drag && drop any supported file onto this panel.")
        self.lbl_src_status.setObjectName("dock_subtitle")
        self.lbl_src_status.setWordWrap(True)
        src_layout.addWidget(self.lbl_src_status)

        cad_row = QHBoxLayout()
        cad_row.setSpacing(4)
        self.chk_cad_split = QCheckBox("Split into CAD layers (by Layer/Level)")
        self.chk_cad_split.setToolTip(
            "DXF, DWG and DGN files store every entity in one table tagged with a "
            "CAD layer name (DXF/DWG) or level (DGN). When enabled, each CAD layer "
            "becomes its own selectable QGIS layer instead of one merged blob.")
        self.chk_cad_split.setChecked(True)
        self.chk_cad_split.setVisible(False)
        self.chk_cad_split.toggled.connect(self._on_cad_split_toggled)
        cad_row.addWidget(self.chk_cad_split)

        self.btn_oda_path = QPushButton("ODA Path...")
        self.btn_oda_path.setToolTip(
            "Set custom executable path to ODAFileConverter.exe for modern DWG files (R2004-R2024).")
        self.btn_oda_path.clicked.connect(self._configure_oda_path)
        cad_row.addWidget(self.btn_oda_path)

        self.btn_clear_ogr_cache = QPushButton("Clear catalog cache")
        self.btn_clear_ogr_cache.setToolTip(
            "Delete the cached layer catalogs used to reopen Geodatabase and "
            "database sources instantly. The cache also rebuilds automatically "
            "whenever a source file changes.")
        self.btn_clear_ogr_cache.clicked.connect(self._clear_ogr_cache)
        cad_row.addStretch(1)
        cad_row.addWidget(self.btn_clear_ogr_cache)
        src_layout.addLayout(cad_row)

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

        self.chk_conv_symbology = QCheckBox(
            "Auto-apply plan symbology (e-Plan / Mevzuat Lejanti)")
        self.chk_conv_symbology.setChecked(True)
        opt_form.addRow(self.chk_conv_symbology)

        cad_gis_layout.addWidget(opt_group)

        # Output mode — three mutually exclusive destinations
        out_group = QGroupBox("Output Mode")
        out_layout = QVBoxLayout(out_group)
        out_layout.setContentsMargins(6, 10, 6, 6)
        out_layout.setSpacing(2)

        self.rb_out_gpkg = QRadioButton("GeoPackage file (durable, transformed)")
        self.rb_out_gpkg.setChecked(True)
        self.rb_out_scratch = QRadioButton(
            "Temporary scratch layers (in memory, no file)")
        self.rb_out_live = QRadioButton(
            "Live — no conversion, zero-copy references")
        self.rb_out_live.setToolTip(
            "Add the checked layers straight to QGIS as live references to the "
            "source file. Nothing is written or copied, so even huge FileGDB / "
            "Personal GDB layers open in milliseconds. QGIS reads features on "
            "demand and reprojects on the fly using each layer's own CRS.")

        self.output_mode_group = QButtonGroup(self)
        for rb in (self.rb_out_gpkg, self.rb_out_scratch, self.rb_out_live):
            self.output_mode_group.addButton(rb)
            out_layout.addWidget(rb)
        self.output_mode_group.buttonToggled.connect(
            lambda *_: self._sync_output_mode())

        cad_gis_layout.addWidget(out_group)

        # Progress Bar & Trigger
        self.progress_conv = QProgressBar()
        self.progress_conv.setVisible(False)
        cad_gis_layout.addWidget(self.progress_conv)

        self.btn_convert_gis = QPushButton("Convert to GeoPackage")
        self.btn_convert_gis.setObjectName("convert_btn")
        self.btn_convert_gis.setEnabled(False)
        self.btn_convert_gis.clicked.connect(self._convert_gis_dataset)
        cad_gis_layout.addWidget(self.btn_convert_gis)

        self.conversion_receipt_group = QGroupBox("Last Conversion Receipt")
        receipt_layout = QVBoxLayout(self.conversion_receipt_group)
        receipt_layout.setContentsMargins(6, 10, 6, 6)
        receipt_layout.setSpacing(3)
        self.txt_conversion_receipt = QTextBrowser()
        self.txt_conversion_receipt.setMinimumHeight(120)
        self.txt_conversion_receipt.setOpenExternalLinks(False)
        receipt_layout.addWidget(self.txt_conversion_receipt)
        receipt_actions = QHBoxLayout()
        receipt_actions.addStretch(1)
        self.btn_copy_receipt = QPushButton("Copy Receipt")
        self.btn_copy_receipt.clicked.connect(
            lambda: QApplication.clipboard().setText(
                self.txt_conversion_receipt.toPlainText()))
        receipt_actions.addWidget(self.btn_copy_receipt)
        receipt_layout.addLayout(receipt_actions)
        self.conversion_receipt_group.setVisible(False)
        cad_gis_layout.addWidget(self.conversion_receipt_group)

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

        self.btn_ncz_filter_extent = QPushButton("Filter by Extent...")
        self.btn_ncz_filter_extent.setToolTip(
            "Filter the selected Netcad drawings down to only those that "
            "intersect the current map canvas or selected polygon.")
        self.btn_ncz_filter_extent.clicked.connect(
            self._filter_current_ncz_by_extent)
        ncz_file_layout.addWidget(self.btn_ncz_filter_extent)

        self.btn_clear_ncz_cache = QPushButton("Clear cache")
        self.btn_clear_ncz_cache.setToolTip(
            "Delete the local NCZ index cache. The cache also rebuilds "
            "automatically whenever a drawing file changes.")
        self.btn_clear_ncz_cache.clicked.connect(self._clear_ncz_cache)
        ncz_file_layout.addWidget(self.btn_clear_ncz_cache)
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
        ncz_opt_group = QGroupBox("CAD Optimization && Styling")
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

        self.chk_ncz_plan_symbology = QCheckBox(
            "PlanGML spatial planning mode (official schema and symbology)")
        self.chk_ncz_plan_symbology.setToolTip(
            "Turn this on for imar plan drawings only. Layers are grouped into "
            "the official PlanGML upper groups, the PlanGML schema columns are "
            "added, and each tabaka is drawn with its official e-Plan "
            "gösterim. Left off, raw CAD layers, attributes and colors are "
            "kept exactly as they are.")
        self.chk_ncz_plan_symbology.setChecked(False)
        self.chk_ncz_plan_symbology.toggled.connect(
            lambda _checked: self._sync_merge_geometry_availability())
        ncz_opt_form.addRow(self.chk_ncz_plan_symbology)

        self.cmb_plan_type = QComboBox()
        self.cmb_plan_type.addItems([
            "Auto (detect from file name)",
            "Uygulama İmar Planı (1/1000)",
            "Nazım İmar Planı (1/5000)",
            "Çevre Düzeni Planı (1/25.000+)",
        ])
        self.cmb_plan_type.setToolTip(
            "Which official e-Plan style set to draw with. Auto reads the "
            "scale from the file name: 1000 uses uygulama imar, 5000 nazım "
            "imar, 25000 and above çevre düzeni.")
        ncz_opt_form.addRow("Plan type (official symbology):", self.cmb_plan_type)

        self.chk_ncz_mpyy = QCheckBox(
            "MPYY yapısında aktar (MPYY UİP / NİP / ÇDP stilleri)")
        self.chk_ncz_mpyy.setToolTip(
            "Writes the drawing into a MPYY 1.1.7 workspace GeoPackage: each "
            "tabaka goes to its MPYY feature type with its XSD attributes "
            "(e.g. Konut, KonutTip=GelismeKonut) and is drawn with the MPYY "
            "e-Plan style of the chosen plan level. Tabaka the crosswalk does "
            "not define are not guessed; they stay in a separate group.")
        self.chk_ncz_mpyy.setChecked(False)
        ncz_opt_form.addRow(self.chk_ncz_mpyy)

        self.chk_ncz_label = QCheckBox("Convert text elements to map labels")
        self.chk_ncz_label.setChecked(True)
        ncz_opt_form.addRow(self.chk_ncz_label)

        self.chk_ncz_join = QCheckBox(
            "Join attribute tables (@TAB) automatically")
        self.chk_ncz_join.setChecked(True)
        ncz_opt_form.addRow(self.chk_ncz_join)

        self.chk_ncz_merge_geometry = QCheckBox(
            "Build unified upper layers (Polygon / Line / Point)")
        self.chk_ncz_merge_geometry.setToolTip(
            "Merge CAD tabaka into one layer per geometry type instead of one "
            "layer each. In PlanGML mode the layers are grouped by official "
            "upper group and categorized by tabaka inside each group.")
        self.chk_ncz_merge_geometry.setChecked(True)
        self.chk_ncz_merge_geometry.setEnabled(True)
        ncz_opt_form.addRow(self.chk_ncz_merge_geometry)

        self.chk_ncz_temporary = QCheckBox(
            "Import directly as temporary scratch layers (no GPKG)")
        ncz_opt_form.addRow(self.chk_ncz_temporary)

        self._sync_merge_geometry_availability()

        ncz_layout.addWidget(ncz_opt_group)

        # Progress Bar & Trigger
        self.progress_ncz = QProgressBar()
        self.progress_ncz.setVisible(False)
        ncz_layout.addWidget(self.progress_ncz)

        self.btn_convert_ncz = QPushButton("Convert Netcad && Load to Canvas")
        self.btn_convert_ncz.setObjectName("convert_btn")
        self.btn_convert_ncz.setEnabled(False)
        self.btn_convert_ncz.clicked.connect(self._import_netcad_dataset)
        ncz_layout.addWidget(self.btn_convert_ncz)

        # Subtle, compact MBTiles bridge link without cluttering the UI
        mbtiles_link_row = QHBoxLayout()
        mbtiles_link_row.setContentsMargins(2, 2, 2, 0)
        mbtiles_link_row.addStretch(1)
        self.btn_ncz_to_mbtiles = QPushButton("Need raster tiles? Open MBTiles Exporter →")
        self.btn_ncz_to_mbtiles.setToolTip(
            "Open the CAD & GIS Exporter tab pre-configured to generate an MBTiles pyramid from current canvas layers.")
        self.btn_ncz_to_mbtiles.setFlat(True)
        self.btn_ncz_to_mbtiles.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ncz_to_mbtiles.setStyleSheet(
            "color: #0277bd; font-size: 11px; text-decoration: underline; background: transparent; border: none; padding: 1px 4px;"
        )
        self.btn_ncz_to_mbtiles.clicked.connect(
            self._send_ncz_to_mbtiles_exporter)
        mbtiles_link_row.addWidget(self.btn_ncz_to_mbtiles)
        ncz_layout.addLayout(mbtiles_link_row)

        tab_ncz = self._make_scroll_tab(tab2_inner)
        main_tab.addTab(
            tab_ncz,
            QIcon(
                os.path.join(
                    self.icon_dir,
                    "icon_ncz.png")),
            "Netcad NCZ/NCA Importer")

        # ───────────────────────── Spatial Filter Sub-Dialog (shared by CAD & NCZ) ───
        self.spatial_filter_dialog = QDialog(self)
        self.spatial_filter_dialog.setObjectName("spatial_filter_dialog")
        self.spatial_filter_dialog.setWindowTitle("02CadGis — Batch Spatial Filter")
        self.spatial_filter_dialog.setWindowIcon(
            QIcon(
                os.path.join(
                    self.icon_dir,
                    "icon_filter.png")))
        self.spatial_filter_dialog.resize(800, 800)
        self.spatial_filter_dialog.setMinimumSize(680, 520)
        self.spatial_filter_dialog.setStyleSheet(self.styleSheet())
        dlg_layout = QVBoxLayout(self.spatial_filter_dialog)
        dlg_layout.setContentsMargins(6, 6, 6, 6)
        tab_filter_inner = QWidget()
        tab_filter_inner.setObjectName("tab_filter_inner")
        self._build_spatial_filter_tab(tab_filter_inner)
        dlg_scroll = self._make_scroll_tab(tab_filter_inner)
        dlg_layout.addWidget(dlg_scroll)

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
        self.cmb_exp_layer.currentIndexChanged.connect(
            self._on_export_layer_changed)
        exp_form.addRow("Select Source Layer:", self.cmb_exp_layer)

        self.cmb_exp_format = QComboBox()
        self.cmb_exp_format.addItems([
            "AutoCAD DXF (*.dxf)",
            "Google Earth KML (*.kml)",
            "Google Earth KMZ (*.kmz)",
            "Web Map Tiles MBTiles (*.mbtiles)",
        ])
        self.cmb_exp_format.currentIndexChanged.connect(
            self._on_export_format_changed)
        exp_form.addRow("Target Export Format:", self.cmb_exp_format)

        # MBTiles options group
        self.widget_mbtiles_opts = QWidget()
        self.widget_mbtiles_opts.setVisible(False)
        mbtiles_layout = QVBoxLayout(self.widget_mbtiles_opts)
        mbtiles_layout.setContentsMargins(0, 2, 0, 2)
        mbtiles_layout.setSpacing(2)

        zoom_row = QHBoxLayout()
        zoom_row.addWidget(QLabel("Min Zoom:"))
        self.spn_mbtiles_min_zoom = QSpinBox()
        self.spn_mbtiles_min_zoom.setRange(0, 24)
        self.spn_mbtiles_min_zoom.setValue(14)
        self.spn_mbtiles_min_zoom.setToolTip(
            "Minimum zoom level for the tile pyramid (lower = wider overview).")
        zoom_row.addWidget(self.spn_mbtiles_min_zoom)

        zoom_row.addWidget(QLabel("Max Zoom:"))
        self.spn_mbtiles_max_zoom = QSpinBox()
        self.spn_mbtiles_max_zoom.setRange(0, 24)
        self.spn_mbtiles_max_zoom.setValue(16)
        self.spn_mbtiles_max_zoom.setToolTip(
            "Maximum zoom level for the tile pyramid (higher = finer detail).")
        zoom_row.addWidget(self.spn_mbtiles_max_zoom)
        mbtiles_layout.addLayout(zoom_row)

        opts_row = QHBoxLayout()
        self.cmb_mbtiles_tile_format = QComboBox()
        self.cmb_mbtiles_tile_format.addItems(
            ["PNG (Transparent)", "JPEG (Opaque)"])
        self.cmb_mbtiles_tile_format.setToolTip(
            "PNG supports transparent background overlays; JPEG is smaller.")
        opts_row.addWidget(self.cmb_mbtiles_tile_format, 1)

        opts_row.addWidget(QLabel("DPI:"))
        self.spn_mbtiles_dpi = QSpinBox()
        self.spn_mbtiles_dpi.setRange(72, 600)
        self.spn_mbtiles_dpi.setValue(96)
        self.spn_mbtiles_dpi.setToolTip(
            "Tile resolution (96 is standard web map DPI).")
        opts_row.addWidget(self.spn_mbtiles_dpi)

        opts_row.addWidget(QLabel("Metatile:"))
        self.spn_mbtiles_metatile = QSpinBox()
        self.spn_mbtiles_metatile.setRange(1, 8)
        self.spn_mbtiles_metatile.setValue(1)
        self.spn_mbtiles_metatile.setToolTip(
            "Metatile buffer size (1 is fastest and lightest on memory).")
        opts_row.addWidget(self.spn_mbtiles_metatile)
        mbtiles_layout.addLayout(opts_row)

        extent_row = QHBoxLayout()
        extent_row.addWidget(QLabel("Extent:"))
        self.cmb_mbtiles_extent = QComboBox()
        self.cmb_mbtiles_extent.addItems([
            "CAD / Vector Data Extent (Auto)",
            "Current Map Canvas Extent",
        ])
        self.cmb_mbtiles_extent.setToolTip(
            "CAD/Vector extent exports only the drawing area (fast & compact).\n"
            "Canvas extent exports what is currently visible on your screen."
        )
        extent_row.addWidget(self.cmb_mbtiles_extent, 1)
        mbtiles_layout.addLayout(extent_row)

        self.lbl_mbtiles_estimate = QLabel("Estimated tiles: calculating...")
        self.lbl_mbtiles_estimate.setStyleSheet(
            "font-size: 11px; font-weight: bold; color: #2e7d32; padding: 3px 6px; background: #e8f5e9; border-radius: 3px;"
        )
        mbtiles_layout.addWidget(self.lbl_mbtiles_estimate)

        self.spn_mbtiles_min_zoom.valueChanged.connect(self._update_mbtiles_estimate)
        self.spn_mbtiles_max_zoom.valueChanged.connect(self._update_mbtiles_estimate)
        self.cmb_mbtiles_extent.currentIndexChanged.connect(self._update_mbtiles_estimate)

        exp_form.addRow("Tile Settings:", self.widget_mbtiles_opts)

        self.export_crs = QgsProjectionSelectionWidget()
        self.export_crs.setOptionVisible(
            QgsProjectionSelectionWidget.CrsOption.ProjectCrs, True)
        self.export_crs.setCrs(QgsProject.instance().crs())
        exp_form.addRow("Output CRS:", self.export_crs)

        self.lbl_export_crs_hint = QLabel(
            "DXF uses the chosen engineering/project CRS.")
        self.lbl_export_crs_hint.setObjectName("dock_subtitle")
        self.lbl_export_crs_hint.setWordWrap(True)
        exp_form.addRow("", self.lbl_export_crs_hint)

        self.chk_export_selected = QCheckBox("Selected features only")
        self.chk_export_selected.setToolTip(
            "Export only the features currently selected on the source layer. "
            "The full layer is exported when this option is off.")
        exp_form.addRow("Feature Scope:", self.chk_export_selected)

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
        self._sync_output_mode()

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
        dialog.setStyleSheet(self.styleSheet())
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
          <li>Review <b>Layers Found in Source</b> and uncheck anything you do not need. For Geodatabase and database sources the layer catalog is cached, so reopening the same unchanged file lists its layers instantly; use <b>Clear catalog cache</b> to reset it.</li>
          <li>For <b>DXF / DGN</b>, keep <b>Split into CAD layers</b> enabled to turn each CAD layer (DXF <i>Layer</i>) or level (DGN <i>Level</i>) into its own selectable QGIS layer instead of one merged table.</li>
          <li>Pick an <b>Output Mode</b>: GeoPackage file, temporary scratch layers, or live (no conversion).</li>
          <li>For delimited text, check the <b>Delimited Text Geometry</b> card: the delimiter and X/Y or WKT columns are auto-detected and can be overridden, and the source CRS defaults to EPSG:4326 for lon/lat columns.</li>
          <li>Choose a target `.gpkg` (a name is pre-suggested from the source), enable temporary scratch layers when you only want to inspect the result, or enable <b>Load selected layers live</b> to add them straight to QGIS with no conversion at all.</li>
          <li><b>Live loading (FileGDB / Personal GDB):</b> live mode adds the checked layers as zero-copy references to the source, so even multi-million-feature Geodatabase layers open in a fraction of a second. QGIS reads features on demand and reprojects on the fly; use GeoPackage output later if you need a standalone, transformed copy.</li>
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

        <h3>3. Batch Spatial Extent Filter</h3>
        <p>When working with hundreds of CAD, Netcad, or GIS files (e.g. municipal sheets/paftas) where only a subset intersect your project area, use the <b>Batch Spatial Filter</b> tab:</p>
        <ol>
          <li>Select the folder containing candidate drawings (or pick specific files). Subfolders are scanned recursively by default.</li>
          <li>Choose your spatial boundary: <b>Active Map Canvas</b>, <b>Selected Feature(s) in Polygon Layer</b>, <b>Print Layout Map</b>, or a manual bounding box.</li>
          <li>Optionally set a buffer distance (e.g. 50 m margin) and spatial predicate (intersects or within).</li>
          <li>Click <b>Scan &amp; Filter Extents</b>. Candidate file headers/extents are inspected in milliseconds without loading full layers into memory or crashing QGIS.</li>
          <li>Click <b>Preview Footprints on Canvas</b> to see a labeled visual overlay of sheet extents directly on the map.</li>
          <li>Click <b>Import Matched Files</b> to load the matching files into QGIS, merge them into a single GeoPackage, or copy them to a dedicated folder.</li>
        </ol>

        <h3>4. Export QGIS Layers</h3>
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

    @staticmethod
    def _is_cad_format(fmt: SourceFormat | None) -> bool:
        return fmt is not None and fmt.key in ("dxf", "dwg", "dgn")

    def _configure_oda_path(self) -> None:
        current = QSettings().value("zero2cadgis/oda_converter_path", "")
        start_dir = os.path.dirname(str(current)) if current and os.path.exists(str(current)) else r"C:\Program Files"
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select ODAFileConverter.exe Executable",
            start_dir, "ODAFileConverter (ODAFileConverter.exe *.exe);;All Files (*.*)")
        if file_path and os.path.exists(file_path):
            QSettings().setValue("zero2cadgis/oda_converter_path", file_path)
            self.iface.messageBar().pushMessage(
                "02CadGis",
                f"Saved ODA File Converter path: {file_path}",
                Qgis.MessageLevel.Success, 5)
            src_path = self.txt_src_path.text().strip()
            fmt = self._current_source_format()
            if src_path and fmt is not None:
                self._refresh_source_preview(src_path, fmt)

    def _handle_dwg_error(self, file_path: str, err_msg: str) -> bool:
        """Show an interactive setup dialog when ODA File Converter is needed for DWG files."""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("DWG Import - ODA File Converter Required")
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setText(
            f"GDAL CAD driver could not read modern DWG file:\n'{os.path.basename(file_path)}'\n\n"
            "Standard GDAL builds only support legacy DWG R2000 files. "
            "Modern DWG files (R2004-R2024) require the free ODA File Converter utility "
            "from Open Design Alliance."
        )
        msg_box.setInformativeText(
            "If ODA File Converter is installed, click 'Locate ODAFileConverter.exe' to set its location.\n"
            "Otherwise, click 'Download ODA Converter' to get the free utility."
        )
        btn_locate = msg_box.addButton("Locate ODAFileConverter.exe...", QMessageBox.ButtonRole.ActionRole)
        btn_download = msg_box.addButton("Download ODA Converter", QMessageBox.ButtonRole.HelpRole)
        btn_cancel = msg_box.addButton(QMessageBox.StandardButton.Cancel)

        msg_box.exec()
        clicked = msg_box.clickedButton()

        if clicked == btn_locate:
            path, _ = QFileDialog.getOpenFileName(
                self, "Select ODAFileConverter.exe Executable",
                r"C:\Program Files", "Executable Files (ODAFileConverter.exe *.exe);;All Files (*.*)")
            if path and os.path.exists(path):
                QSettings().setValue("zero2cadgis/oda_converter_path", path)
                self.iface.messageBar().pushMessage(
                    "02CadGis", f"Saved ODA File Converter path: {path}",
                    Qgis.MessageLevel.Success, 5)
                return True
        elif clicked == btn_download:
            from qgis.PyQt.QtGui import QDesktopServices
            from qgis.PyQt.QtCore import QUrl
            QDesktopServices.openUrl(QUrl("https://www.opendesign.com/guestfiles/oda_file_converter"))

        return False

    def _on_source_type_changed(self, index: int) -> None:
        self.txt_src_path.clear()
        self.btn_convert_gis.setEnabled(False)
        fmt = self._current_source_format()
        is_kml = fmt is not None and fmt.key == "kml"
        self.chk_conv_kml_expand.setEnabled(is_kml)
        self.chk_conv_raster.setEnabled(is_kml)
        self.csv_group.setVisible(fmt is not None and fmt.key == "csv")
        self.chk_cad_split.setVisible(self._is_cad_format(fmt))
        self.src_layer_tree.clear()
        self.src_preview_group.setVisible(False)
        self.src_csv_profile = None
        self._cad_split_field = ""
        self.lbl_src_status.setText(
            "Tip: drag && drop any supported file onto this panel.")

    def _on_cad_split_toggled(self, _checked: bool) -> None:
        path = self.txt_src_path.text().strip()
        fmt = self._current_source_format()
        if path and fmt is not None:
            self._refresh_source_preview(path, fmt)
            self._update_convert_gis_button_state()

    def _clear_ogr_cache(self) -> None:
        from ..core import ogr_catalog_cache
        removed = ogr_catalog_cache.clear()
        self.iface.messageBar().pushMessage(
            "02CadGis",
            f"Cleared {removed} cached source catalog(s).",
            Qgis.MessageLevel.Info, 5)

    def _browse_src_dataset(self) -> None:
        fmt = self._current_source_format()
        start_dir = self._last_import_dir()
        if fmt is None:
            fmt = SOURCE_FORMATS[0]

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
        self.chk_cad_split.setVisible(self._is_cad_format(fmt))

        self.txt_src_path.setText(file_path)
        self._remember_import_dir(file_path)
        self._suggest_gpkg_destination(file_path)
        self._refresh_source_preview(file_path, fmt)
        self._update_convert_gis_button_state()

    def _suggest_gpkg_destination(self, source_path: str) -> None:
        """Prefill the target GPKG from the source name when still empty."""
        if self.txt_gpkg_path.text().strip() \
                or self.rb_out_scratch.isChecked() \
                or self.rb_out_live.isChecked():
            return
        stem = os.path.splitext(os.path.basename(
            source_path.rstrip("\\/")))[0] or "converted"
        suggestion = os.path.join(self._last_export_dir(), f"{stem}.gpkg")
        self.txt_gpkg_path.setText(suggestion)

    def _refresh_source_preview(self, file_path: str,
                                fmt: SourceFormat) -> None:
        self.src_layer_tree.clear()
        self.src_csv_profile = None
        self._cad_split_field = ""
        cad_split = self._is_cad_format(fmt) and self.chk_cad_split.isChecked()
        try:
            if fmt.key == "csv":
                self.src_csv_profile = sniff_delimited_dataset(file_path)
                self._populate_csv_controls(self.src_csv_profile)

            probe = GisConverterEngine(
                file_path, "", QgsProject.instance().crs(),
                csv_profile=self.src_csv_profile)
            if cad_split:
                infos, field = probe.discover_cad_layers()
                self._cad_split_field = field
                if not field:
                    # Source had no CAD-layer field; fall back to plain view.
                    infos = probe.discover_layers()
            else:
                infos = probe.discover_layers(
                    is_kmz=has_extension(file_path, ".kmz"))
            from_cache = probe.catalog_from_cache
            probe.cleanup()
        except Exception as exc:
            err_text = str(exc)
            if fmt and fmt.key == "dwg" and ("ODA" in err_text or "GDAL CAD driver" in err_text or "legacy DWG R2000" in err_text):
                if self._handle_dwg_error(file_path, err_text):
                    self._refresh_source_preview(file_path, fmt)
                    return
            self.src_preview_group.setVisible(False)
            self.lbl_src_status.setText(f"Could not inspect dataset: {exc}")
            return

        header = ("CAD Layer" if self._cad_split_field else "Layer Name")
        self.src_layer_tree.setHeaderLabels([header, "Geometry", "Features"])
        for info in infos:
            item = QTreeWidgetItem(self.src_layer_tree)
            item.setText(0, fix_mojibake(info.name))
            item.setText(1, info.geometry)
            item.setText(2, "?" if info.feature_count < 0
                         else str(info.feature_count))
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(0, Qt.CheckState.Checked)
            item.setData(0, Qt.ItemDataRole.UserRole, info.key)

        self.src_preview_group.setVisible(bool(infos))
        total = sum(max(info.feature_count, 0) for info in infos)
        unit = "CAD layer(s)" if self._cad_split_field else "layer(s)"
        cache_note = " (from cache)" if from_cache else ""
        self.lbl_src_status.setText(
            f"{len(infos)} {unit} discovered, ~{total} features{cache_note}. "
            "Uncheck anything you do not need before converting.")

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

    def _sync_output_mode(self) -> None:
        """Keep the destination widgets and button label in sync with the
        selected output mode (GeoPackage / scratch / live)."""
        is_temp = self.rb_out_scratch.isChecked()
        is_live = self.rb_out_live.isChecked()
        writes_gpkg = not (is_temp or is_live)

        self.txt_gpkg_path.setEnabled(writes_gpkg)
        self.btn_browse_gpkg.setEnabled(writes_gpkg)
        if not writes_gpkg:
            self.txt_gpkg_path.clear()
            self.chk_conv_load.setChecked(True)
        self.chk_conv_load.setEnabled(writes_gpkg)

        if is_live:
            self.btn_convert_gis.setText("Add Live Layers to Canvas")
        elif is_temp:
            self.btn_convert_gis.setText("Import as Scratch Layers")
        else:
            self.btn_convert_gis.setText("Convert to GeoPackage")
        self._update_convert_gis_button_state()

    def _update_convert_gis_button_state(self) -> None:
        has_src = bool(self.txt_src_path.text().strip())
        is_temp = self.rb_out_scratch.isChecked()
        is_live = self.rb_out_live.isChecked()
        has_dst = bool(self.txt_gpkg_path.text().strip())
        self.btn_convert_gis.setEnabled(
            has_src and (is_temp or is_live or has_dst))

    def _convert_gis_dataset(self) -> None:
        src = self.txt_src_path.text()
        dst = self.txt_gpkg_path.text()
        fmt = self._current_source_format()
        if fmt is None:
            fmt = format_for_path(src) or SOURCE_FORMATS[0]

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
            is_temp = self.rb_out_scratch.isChecked()
            is_live = self.rb_out_live.isChecked()

            csv_profile = None
            csv_crs = ""
            if fmt.key == "csv":
                csv_profile = self._effective_csv_profile()
                if self.csv_src_crs.crs().isValid():
                    csv_crs = self.csv_src_crs.crs().authid()

            src_crs_param = None
            if fmt.key == "csv" and self.csv_src_crs.crs().isValid():
                src_crs_param = self.csv_src_crs.crs()
            self.gis_converter = GisConverterEngine(
                src, dst, crs,
                csv_profile=csv_profile, csv_source_crs=csv_crs,
                source_crs=src_crs_param)
            if self._cad_split_field and self._is_cad_format(fmt):
                self.gis_converter.cad_split_field = self._cad_split_field

            layer_total = max(
                len(selected_layers) if selected_layers is not None else 1, 1)
            progress_state = {"done": 0}

            verb = "Adding" if is_live else "Converting"

            def layer_progress(layer_name: str) -> None:
                progress_state["done"] += 1
                share = min(progress_state["done"] / layer_total, 1.0)
                self.progress_conv.setValue(10 + int(share * 55))
                self.progress_conv.setFormat(f"{verb} {layer_name}...")
                QApplication.processEvents()

            if is_live:
                loaded_layers = self.gis_converter.load_layers_live(
                    is_kmz=is_kmz,
                    selected_layers=selected_layers,
                    progress_cb=layer_progress,
                )
            elif is_temp:
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

            if (is_live or self.chk_conv_load.isChecked()) and loaded_layers:
                root = QgsProject.instance().layerTreeRoot()
                suffix = ("LIVE" if is_live
                          else "TEMP" if is_temp else "GPKG")
                group_name = f"{
                    self._sanitize_name(
                        os.path.basename(src))}_{suffix}"

                existing = root.findGroup(group_name)
                if existing:
                    root.removeChildNode(existing)

                group = root.addGroup(group_name)
                for cl in loaded_layers:
                    if getattr(self, "chk_conv_symbology", None) is None or self.chk_conv_symbology.isChecked():
                        with suppress(Exception):
                            from ..core.symbology import apply_plan_symbology
                            apply_plan_symbology(
                                cl, source_name=os.path.basename(src))
                    QgsProject.instance().addMapLayer(cl, False)
                    node = group.addLayer(cl)
                    from ..core.cad_engine import is_helper_or_noise_layer
                    if node and is_helper_or_noise_layer(cl.name()):
                        with suppress(Exception):
                            node.setItemVisibilityChecked(False)

            self.progress_conv.setValue(100)
            self.progress_conv.setVisible(False)

            # Refresh exporter layer combo list
            self._populate_layers_combo()

            src_label = os.path.basename(src.rstrip(chr(92) + '/'))
            if is_live:
                message = (
                    f"Added {len(loaded_layers)} live layer(s) from "
                    f"{src_label} without conversion (zero-copy references).")
            else:
                destination = ("temporary scratch layers" if is_temp
                               else os.path.basename(dst))
                message = (
                    f"Converted {len(loaded_layers)} layer(s) from "
                    f"{src_label} to {destination}.")
            self.iface.messageBar().pushMessage(
                "02CadGis", message, Qgis.MessageLevel.Success, 7)

            notes = getattr(self.gis_converter, "last_warnings", [])
            for note in notes:
                self.iface.messageBar().pushMessage(
                    "02CadGis", note, Qgis.MessageLevel.Warning, 10)

            mode_name = ("Live / zero-copy" if is_live else
                         "Temporary scratch" if is_temp else
                         "Atomic GeoPackage")
            destination = (src if is_live else
                           "QGIS temporary memory" if is_temp else dst)
            receipt_layers = []
            for layer in loaded_layers:
                with suppress(Exception):
                    receipt_layers.append(ConvertedLayer(
                        name=layer.name(),
                        geometry=memory_geometry_type_name(layer),
                        feature_count=int(layer.featureCount()),
                        crs=layer.crs().authid(),
                    ))
            receipt = build_conversion_receipt(
                source=src,
                mode=mode_name,
                destination=destination,
                target_crs=("source CRS / on-the-fly" if is_live
                            else crs.authid()),
                layers=receipt_layers,
                warnings=notes,
            )
            self.txt_conversion_receipt.setPlainText(receipt)
            self.conversion_receipt_group.setVisible(True)

        except Exception as exc:
            self.progress_conv.setVisible(False)
            err_text = str(exc)
            if fmt and fmt.key == "dwg" and ("ODA" in err_text or "GDAL CAD driver" in err_text or "legacy DWG R2000" in err_text):
                if self._handle_dwg_error(src, err_text):
                    self._convert_gis_dataset()
                    return
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

    def _clear_ncz_cache(self) -> None:
        from ..core.ncz_engine.v2 import cache as ncz_cache
        removed = ncz_cache.clear()
        self.iface.messageBar().pushMessage(
            "02CadGis",
            f"Cleared {removed} cached NCZ index file(s).",
            Qgis.MessageLevel.Info, 5)

    def _load_ncz_paths(self, file_paths: list[str]) -> None:
        self._remember_import_dir(file_paths[0])
        self.current_netcad_paths = file_paths
        if len(file_paths) == 1:
            self.txt_ncz_path.setText(file_paths[0])
        else:
            self.txt_ncz_path.setText(f"{len(file_paths)} files selected")

        self._sync_merge_geometry_availability(len(file_paths) > 1)

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

            self.progress_ncz.setFormat("Detecting coordinate system...")
            QApplication.processEvents()
            detection_note = self._auto_detect_ncz_crs()

            # Populate card
            self.lbl_ncz_version.setText(
                ", ".join(versions) or "Standard / Older version")
            projection_note = ", ".join(projections) or "Undefined"
            if epsg_codes:
                # The drawing's own SRS id is not an EPSG code; keep it visible
                # so the detected EPSG can be checked against it.
                projection_note += f"  (drawing SRS: {', '.join(sorted(epsg_codes))})"
            self.lbl_ncz_projection.setText(projection_note)
            self.lbl_ncz_epsg.setText(detection_note)
            self.lbl_ncz_epsg.setToolTip(detection_note)
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

    def _auto_detect_ncz_crs(self) -> str:
        """Name the drawings' CRS and preselect it, returning what to show.

        A Netcad drawing stores its own SRS id, not an EPSG code, so the EPSG
        is worked out from the projection text plus a coordinate sample. The
        result only preselects the CRS combo — the user always keeps the last
        word, which is why the reasoning is reported rather than hidden.
        """
        from ..core.crs_detect import detect_crs

        detections = {}
        for file_path, reader in self.ncz_readers.items():
            sample = []
            with suppress(Exception):
                sample = reader.sample_coordinates()
            with suppress(Exception):
                detections[file_path] = detect_crs(
                    reader.projection_text, sample)
        if not detections:
            return "Not detected"

        named = [d for d in detections.values() if d.epsg]
        if not named:
            return next(iter(detections.values())).reason

        chosen = named[0]
        codes = {d.epsg for d in named}
        crs = QgsCoordinateReferenceSystem(chosen.authid)
        if not crs.isValid():
            return f"{chosen.authid} is not available in this QGIS installation."
        self.ncz_crs_selector.setCrs(crs)

        note = f"{chosen.authid} — {chosen.label}"
        if chosen.confidence != "high":
            note += " (please confirm)"
        note += f". {chosen.reason}"
        if len(codes) > 1:
            others = ", ".join(sorted(
                f"EPSG:{c}" for c in codes if c != chosen.epsg))
            note += (f" The selected drawings do not agree — {others} was also "
                     f"detected, so check the CRS before converting.")
        return note

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

                for summary in sorted(summaries, key=lambda s: fix_mojibake(s.layer_name)):
                    item = QTreeWidgetItem(cad_root)
                    item.setText(0, fix_mojibake(summary.layer_name))
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
            self,
            geometry_kind: str,
            is_closed: bool = False,
            coords: list | None = None) -> tuple[str, str] | tuple[None, None]:
        if geometry_kind in ("Point", "Text", "Symbol", "Block"):
            return "POINT/TEXT", "Point"
        if geometry_kind in (
            "Polygon",
            "Box",
            "Circle",
            "Triangle",
            "MapSheet",
            "SmartObject"):
            return "POLYGON", "Polygon"
        if geometry_kind in ("Line", "Polyline", "Arc"):
            if geometry_kind == "Polyline":
                if is_closed and coords and len(coords) >= 3:
                    return "POLYGON", "Polygon"
                if coords and len(coords) >= 4 and abs(coords[0].x - coords[-1].x) < 1e-4 and abs(coords[0].y - coords[-1].y) < 1e-4:
                    return "POLYGON", "Polygon"
            return "LINE", "LineString"
        return None, None

    def _sanitize_name(self, value: str) -> str:
        text = re.sub(r"\W+", "_", str(value).strip(), flags=re.UNICODE)
        return text.strip("_").upper() or "LAYER"

    def _sync_merge_geometry_availability(
            self, is_batch_import: bool | None = None) -> None:
        """Decide whether unified upper layers can be produced.

        In CAD mode merging only makes sense across several drawings. PlanGML
        mode is defined by grouping tabaka into official upper groups, so it
        enables merging for a single plan file too.
        """
        if is_batch_import is None:
            is_batch_import = len(self.current_netcad_paths or []) > 1
        chk_merge = getattr(self, "chk_ncz_merge_geometry", None)
        if chk_merge is None:
            return
        chk_plan = getattr(self, "chk_ncz_plan_symbology", None)
        is_plangml = chk_plan is not None and chk_plan.isChecked()

        chk_merge.setEnabled(is_batch_import or is_plangml)
        if is_plangml:
            chk_merge.setChecked(True)
        elif not is_batch_import:
            chk_merge.setChecked(False)

        combo_plan = getattr(self, "cmb_plan_type", None)
        if combo_plan is not None:
            combo_plan.setEnabled(is_plangml)
        chk_mpyy = getattr(self, "chk_ncz_mpyy", None)
        if chk_mpyy is not None:
            chk_mpyy.setEnabled(is_plangml)
            if not is_plangml:
                chk_mpyy.setChecked(False)

        chk_style = getattr(self, "chk_ncz_style", None)
        if chk_style is not None:
            was_enabled = chk_style.isEnabled()
            chk_style.setEnabled(not is_plangml)
            if is_plangml:
                # Remember the user's choice only when leaving the free state,
                # so a second sync in PlanGML mode cannot overwrite it.
                if was_enabled:
                    self._ncz_style_before_plangml = chk_style.isChecked()
                chk_style.setChecked(False)
                chk_style.setToolTip(
                    "PlanGML spatial planning mode applies official Ministry legislation "
                    "symbology; raw CAD colors are bypassed.")
            else:
                if not was_enabled:
                    chk_style.setChecked(
                        getattr(self, "_ncz_style_before_plangml", True))
                chk_style.setToolTip(
                    "Apply original Netcad entity and layer ARGB colors.")

    def _selected_plan_type(self) -> str:
        """Official e-Plan style set chosen in the UI: AUTO / UIP / NIP / CDP."""
        combo = getattr(self, "cmb_plan_type", None)
        if combo is None:
            return "AUTO"
        return {0: "AUTO", 1: "UIP", 2: "NIP", 3: "CDP"}.get(
            combo.currentIndex(), "AUTO")

    def _resolve_plan_type(self, source_name: str) -> str:
        """Concrete plan type for a source file: UI choice, else filename scan."""
        plan_type = self._selected_plan_type()
        if plan_type != "AUTO":
            return plan_type
        from ..core.symbology import detect_plan_type
        return detect_plan_type(source_name) or "UIP"

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

            merge_geometry_types = self.chk_ncz_merge_geometry.isChecked()
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
                        entity.geometry_kind, entity.is_closed, entity.coordinates)
                    if not family:
                        continue

                    layer_name = entity.layer_name or f"LAYER_{entity.layer_code}"
                    is_plangml = getattr(self, "chk_ncz_plan_symbology", None) is not None and self.chk_ncz_plan_symbology.isChecked()
                    from ..core.cad_engine import is_helper_or_noise_layer
                    is_noise = is_helper_or_noise_layer(layer_name)

                    if is_noise:
                        display_name = f"{file_base_name}_{self._sanitize_name(layer_name)}_{family}"
                        group_name = f"{file_base_name}_CAD_DRAFT" if merge_geometry_types else f"{file_base_name}_{family}"
                        bucket_key = (entity.layer_code, layer_name, family)
                    elif merge_geometry_types and is_plangml:
                        # Grouped by the Ministry's own upper groups, so the
                        # layer tree is organised the way the regulation is.
                        ust_token = self._sanitize_name(
                            upper_group_of(layer_name))
                        family_token = self._sanitize_name(family)
                        display_name = f"{file_base_name}_{ust_token}_{family_token}"
                        group_name = file_base_name
                        bucket_key = (ust_token, family, geometry_type)
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

                # Topological polygonization for zoning boundaries drafted as lines
                if is_plangml:
                    with suppress(Exception):
                        from ..core.cad_polygonizer import polygonize_cad_entities
                        # Filters to open line work of plan-area tabaka itself.
                        poly_entities = polygonize_cad_entities(decoded_entities)
                        if poly_entities:
                            for entity in poly_entities:
                                family, geometry_type = self._geometry_family(
                                    entity.geometry_kind, entity.is_closed, entity.coordinates)
                                if not family:
                                    continue
                                layer_name = entity.layer_name or f"LAYER_{entity.layer_code}"
                                is_poly_noise = is_helper_or_noise_layer(layer_name)
                                if is_poly_noise:
                                    display_name = f"{file_base_name}_{self._sanitize_name(layer_name)}_{family}"
                                    group_name = f"{file_base_name}_CAD_DRAFT" if merge_geometry_types else f"{file_base_name}_{family}"
                                    bucket_key = (entity.layer_code, layer_name, family)
                                elif merge_geometry_types and is_plangml:
                                    ust_token = self._sanitize_name(
                                        upper_group_of(layer_name))
                                    family_token = self._sanitize_name(family)
                                    display_name = f"{file_base_name}_{ust_token}_{family_token}"
                                    group_name = file_base_name
                                    bucket_key = (ust_token, family, geometry_type)
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

            if getattr(self, "chk_ncz_mpyy", None) is not None and self.chk_ncz_mpyy.isChecked():
                from ..core.mpyy_transfer import mpyy_level_for
                level = mpyy_level_for(self._resolve_plan_type(first_file))
                if level is None:
                    raise ValueError(
                        "MPYY aktarımı için plan kademesi (UİP / NİP / ÇDP) belirlenemedi.")
                self._finish_mpyy_import(layer_groups, level, base_name, is_temp, gpkg_path)
                return

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
            with suppress(Exception):
                if hasattr(self.iface, "mapCanvas") and self.iface.mapCanvas():
                    self.iface.mapCanvas().refresh()

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

    def _finish_mpyy_import(
            self,
            layer_groups: list[LayerGroup],
            level: str,
            base_name: str,
            is_temp: bool,
            gpkg_path: str) -> None:
        """Deliver the import as a MPYY workspace styled with the MPYY styles.

        The workspace is the chosen GeoPackage, or a temporary one for scratch
        imports (a MPYY workspace is a GeoPackage by definition). Tabaka the
        crosswalk does not define stay as ordinary layers in their own group.
        """
        import tempfile
        from ..core.mpyy_transfer import LEVEL_TITLES, transfer_to_mpyy

        spatial = [lyr for grp in layer_groups for lyr in grp.layers if lyr.isSpatial()]
        tables = [grp for grp in layer_groups
                  if grp.layers and not any(lyr.isSpatial() for lyr in grp.layers)]
        if is_temp:
            workspace = os.path.join(
                tempfile.mkdtemp(prefix="zero2cadgis_mpyy_"),
                f"{base_name.lower()}_mpyy_{level.lower()}.gpkg")
        else:
            workspace = gpkg_path
            if os.path.exists(workspace):
                os.remove(workspace)   # overwrite was confirmed in the save dialog

        self.progress_ncz.setValue(85)
        self.progress_ncz.setFormat(
            f"MPYY {LEVEL_TITLES.get(level, level)} çalışma alanına aktarılıyor...")
        QApplication.processEvents()
        result = transfer_to_mpyy(
            spatial, level, workspace, f"{base_name}_MPYY_{level}")
        self.last_mpyy_result = result

        extra = []
        if result.leftovers:
            extra.append(LayerGroup(
                name=f"{base_name}_ESLESMEYEN_TABAKALAR", layers=result.leftovers))
        extra.extend(tables)
        if extra:
            self._add_groups_to_project(extra)
        with suppress(Exception):
            if hasattr(self.iface, "mapCanvas") and self.iface.mapCanvas():
                self.iface.mapCanvas().refresh()

        self.progress_ncz.setValue(100)
        self.progress_ncz.setVisible(False)
        self._populate_layers_combo()
        level_msg = (Qgis.MessageLevel.Warning if result.unmatched
                     else Qgis.MessageLevel.Success)
        self.iface.messageBar().pushMessage(
            "02CadGis", result.summary(), level_msg, 12)

    def _build_layer_groups_from_buckets(
            self,
            grouped_entities: dict,
            target_crs: QgsCoordinateReferenceSystem) -> list[LayerGroup]:
        layer_groups = []
        is_plan_mode = (getattr(self, "chk_ncz_plan_symbology", None) is None
                        or self.chk_ncz_plan_symbology.isChecked())
        # Texts are gathered across all groups: without geometry merging the
        # texts sit in a "<file>_POINT/TEXT" group apart from the polygons
        # they describe, and a per-group search found none of them.
        text_pts = []
        if is_plan_mode:
            from ..core.cad_engine import is_helper_or_noise_layer
            for buckets in grouped_entities.values():
                for bkt in buckets.values():
                    if bkt.geometry_type != "Point":
                        continue
                    for e in bkt.entities:
                        txt = e.label_text or e.name
                        if (txt and e.coordinates
                                and not is_helper_or_noise_layer(e.layer_name)):
                            text_pts.append(
                                (e.coordinates[0].x, e.coordinates[0].y, str(txt)))
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

                    if getattr(self, "chk_ncz_plan_symbology", None) is None or self.chk_ncz_plan_symbology.isChecked():
                        with suppress(Exception):
                            apply_plan_symbology(
                                processed_layer,
                                plan_type=self._resolve_plan_type(source_file_name),
                                source_name=source_file_name)
                    elif self.chk_ncz_style.isChecked():
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

            # Spatial zoning parameter extraction: join texts inside plan polygons
            if is_plan_mode and layers:
                if text_pts and not group_name.endswith("_CAD_DRAFT"):
                    with suppress(Exception):
                        from ..core.zoning_text_extractor import (
                            assign_zoning_parameters_to_polygons,
                            assign_road_widths_to_lines,
                        )
                        for lyr in layers:
                            if lyr.geometryType() == QgsWkbTypes.GeometryType.PolygonGeometry:
                                assign_zoning_parameters_to_polygons(lyr, text_pts)
                            elif lyr.geometryType() == QgsWkbTypes.GeometryType.LineGeometry:
                                assign_road_widths_to_lines(lyr, text_pts)

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

        is_plangml = getattr(self, "chk_ncz_plan_symbology", None) is not None and self.chk_ncz_plan_symbology.isChecked()
        field_defs = list(self.CAD_FIELD_DEFINITIONS)
        if is_plangml:
            field_defs.extend(self.PLANGML_FIELD_DEFINITIONS)

        provider = layer.dataProvider()
        provider.addAttributes(field_defs)
        layer.updateFields()

        # Symbology rule and official identity depend only on the tabaka name
        # and the plan type; a drawing has dozens of tabaka and ~1e5 features.
        plan_type = self._resolve_plan_type(source_file_name) if is_plangml else ""
        plan_kodu = {
            "UIP": "UIP_1000",
            "NIP": "NIP_5000",
            "CDP": "CDP_25000",
        }.get(plan_type, "UIP_1000")
        tabaka_memo: dict[str, tuple] = {}

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
            if geom and geometry_type == "Polygon" and entity.interior_rings:
                with suppress(Exception):
                    geom = QgsGeometry.fromPolygonXY([
                        [QgsPointXY(c.x, c.y) for c in ring]
                        for ring in [coords, *entity.interior_rings]])
            if not geom or geom.isEmpty():
                continue

            source_value = source_file_name
            if entity_source_files:
                source_value = entity_source_files.get(
                    id(entity), source_file_name)

            tabaka_name = entity.layer_name or f"LAYER_{entity.layer_code}"

            attr_values = [
                source_value,
                entity.layer_code,
                tabaka_name,
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
            ]

            if is_plangml:
                memo = tabaka_memo.get(tabaka_name)
                if memo is None:
                    memo = (
                        PlanSymbologyMatcher.match_rule(
                            tabaka_name, plan_type=plan_type),
                        lookup_tabaka(tabaka_name),
                    )
                    tabaka_memo[tabaka_name] = memo
                rule, identity = memo

                # The codes are the Ministry's, taken from its own UİP tabaka
                # catalog. A tabaka the catalog does not define — a CAD symbol
                # or text layer, or a local name with no unambiguous official
                # counterpart — gets empty code cells rather than invented ones.
                if identity is not None:
                    ust_grup_id = identity.ust_grup_id
                    ust_grup_adi = identity.ust_grup_adi
                    alt_grup_id = identity.fonksiyon_kodu
                    alt_grup_adi = identity.fonksiyon_adi
                    fonksiyon_kodu = identity.fonksiyon_kodu
                    tam_adi = identity.fonksiyon_adi
                else:
                    ust_grup_id = ""
                    ust_grup_adi = ""
                    alt_grup_id = ""
                    alt_grup_adi = ""
                    fonksiyon_kodu = ""
                    tam_adi = ""

                attr_values.extend([
                    ust_grup_id,
                    ust_grup_adi,
                    alt_grup_id,
                    alt_grup_adi,
                    plan_kodu,
                    fonksiyon_kodu,
                    tam_adi,
                    rule.display_name,   # GISTERIM: how it is drawn
                    tabaka_name,         # uip_tabaka: the drawing's own name
                    "",                  # YapiDuzeni
                    None,                # KatAdedi
                    None,                # EmsalKaks
                    None,                # Taks
                    None,                # YapiYuksekligi
                    "",                  # Yencok
                    None,                # OnBahceMesafesi
                    None,                # YanBahceMesafesi
                    None,                # ArkaBahceMesafesi
                    "",                  # AdaNo
                    "",                  # ParselNo
                    None,                # YolGenisligi
                    "",                  # PlanNotu
                ])

            feature = QgsFeature(layer.fields())
            feature.setGeometry(geom)
            feature.setAttributes(attr_values)
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
        from ..core.cad_engine import is_helper_or_noise_layer, CadStylingEngine

        for item in layer_groups:
            existing_group = root.findGroup(item.name)
            if existing_group is not None:
                parent = existing_group.parent() or root
                parent.removeChildNode(existing_group)

            group = root.addGroup(item.name)
            is_draft_group = "CAD_DRAFT" in item.name.upper()

            for layer in item.layers:
                is_plangml = (getattr(self, "chk_ncz_plan_symbology", None) is None
                              or self.chk_ncz_plan_symbology.isChecked())

                if is_plangml:
                    with suppress(Exception):
                        apply_plan_symbology(
                            layer,
                            plan_type=self._selected_plan_type(),
                            source_name=layer.name())
                elif getattr(self, "chk_ncz_style", None) and self.chk_ncz_style.isChecked():
                    with suppress(Exception):
                        geom_type = layer.geometryType()
                        geom_str = "Polygon" if geom_type == QgsWkbTypes.GeometryType.PolygonGeometry else ("LineString" if geom_type == QgsWkbTypes.GeometryType.LineGeometry else "Point")
                        CadStylingEngine.apply_argb_renderer(layer, geom_str)

                if getattr(self, "chk_ncz_label", None) and self.chk_ncz_label.isChecked() and layer.geometryType() == QgsWkbTypes.GeometryType.PointGeometry:
                    with suppress(Exception):
                        CadStylingEngine.apply_buffered_labels(layer)

                project.addMapLayer(layer, False)
                node = group.addLayer(layer)
                if node and (is_draft_group or is_helper_or_noise_layer(layer.name())):
                    with suppress(Exception):
                        node.setItemVisibilityChecked(False)
                with suppress(Exception):
                    layer.triggerRepaint()

            if is_draft_group and group:
                with suppress(Exception):
                    group.setItemVisibilityChecked(False)
                    group.setExpanded(False)

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
                "Box", "Triangle", "MapSheet", "SmartObject", "Polyline"}
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
        previous_id = self.cmb_exp_layer.currentData()
        self.cmb_exp_layer.clear()
        if self.cmb_exp_format.currentIndex() == 3:  # MBTiles
            self.cmb_exp_layer.addItem(
                "[All Visible Canvas Layers / Project]", "__ALL_PROJECT_LAYERS__")
        layers = QgsProject.instance().mapLayers().values()
        for layer in layers:
            if isinstance(layer, QgsVectorLayer) and layer.isValid():
                self.cmb_exp_layer.addItem(layer.name(), layer.id())
                if layer.id() not in self._export_selection_connections:
                    layer.selectionChanged.connect(
                        self._update_export_selection_scope)
                    self._export_selection_connections.add(layer.id())
        previous_index = self.cmb_exp_layer.findData(previous_id)
        if previous_index >= 0:
            self.cmb_exp_layer.setCurrentIndex(previous_index)
        elif self.cmb_exp_layer.count() > 0:
            self.cmb_exp_layer.setCurrentIndex(0)
        self._on_export_layer_changed(self.cmb_exp_layer.currentIndex())
        self._update_export_button_state()
        self._populate_filter_polygon_layers()
        self._populate_filter_layouts()

    def _on_export_format_changed(self, index: int) -> None:
        self.txt_exp_path.clear()
        if index == 3:  # MBTiles
            if hasattr(self, "widget_mbtiles_opts"):
                self.widget_mbtiles_opts.setVisible(True)
            self.chk_export_selected.setVisible(False)
            self.export_crs.setCrs(QgsCoordinateReferenceSystem("EPSG:3857"))
            self.export_crs.setEnabled(False)
            self.lbl_export_crs_hint.setText(
                "Web Map Tiles MBTiles standard uses EPSG:3857 (Web Mercator) "
                "with automated tile pyramid generation (TMS / XYZ).")
            self._update_mbtiles_estimate()
        elif index in (1, 2):
            if hasattr(self, "widget_mbtiles_opts"):
                self.widget_mbtiles_opts.setVisible(False)
            self.chk_export_selected.setVisible(True)
            self.export_crs.setCrs(QgsCoordinateReferenceSystem("EPSG:4326"))
            self.export_crs.setEnabled(False)
            self.lbl_export_crs_hint.setText(
                "KML/KMZ is always exported as WGS 84 (EPSG:4326) for "
                "standards-compliant Google Earth positioning.")
        else:
            if hasattr(self, "widget_mbtiles_opts"):
                self.widget_mbtiles_opts.setVisible(False)
            self.chk_export_selected.setVisible(True)
            self.export_crs.setEnabled(True)
            layer = self._selected_export_layer()
            if layer is not None and layer.crs().isValid():
                self.export_crs.setCrs(layer.crs())
            self.lbl_export_crs_hint.setText(
                "DXF uses the chosen engineering/project CRS.")
        self._populate_layers_combo()
        self._update_export_button_state()

    def _selected_export_layer(self) -> QgsVectorLayer | None:
        data = self.cmb_exp_layer.currentData()
        if data == "__ALL_PROJECT_LAYERS__":
            return None
        layer = QgsProject.instance().mapLayer(data)
        if isinstance(layer, QgsVectorLayer) and layer.isValid():
            return layer
        return None

    def _on_export_layer_changed(self, _index: int) -> None:
        layer = self._selected_export_layer()
        self._update_export_selection_scope()
        if self.cmb_exp_format.currentIndex() == 0 and layer is not None \
                and layer.crs().isValid():
            self.export_crs.setCrs(layer.crs())
        self._update_export_button_state()
        self._update_mbtiles_estimate()

    def _update_mbtiles_estimate(self, *_args) -> None:
        """Dynamically compute and display estimated tile count for MBTiles export."""
        if not hasattr(self, "lbl_mbtiles_estimate") or not hasattr(self, "spn_mbtiles_min_zoom"):
            return
        min_z = self.spn_mbtiles_min_zoom.value()
        max_z = self.spn_mbtiles_max_zoom.value()
        if min_z > max_z:
            self.lbl_mbtiles_estimate.setText("Min Zoom cannot exceed Max Zoom!")
            self.lbl_mbtiles_estimate.setStyleSheet(
                "font-size: 11px; font-weight: bold; color: #c62828; padding: 3px 6px; background: #ffebee; border-radius: 3px;"
            )
            return

        extent_mode = self.cmb_mbtiles_extent.currentIndex() if hasattr(self, "cmb_mbtiles_extent") else 0
        extent_3857 = None
        dest_crs = QgsCoordinateReferenceSystem("EPSG:3857")

        if extent_mode == 1:  # Canvas extent
            canvas = getattr(self, "iface", None) and self.iface.mapCanvas()
            if canvas:
                c_ext = canvas.extent()
                c_crs = canvas.mapSettings().destinationCrs()
                if c_crs.isValid() and c_crs != dest_crs:
                    with contextlib.suppress(Exception):
                        ct = QgsCoordinateTransform(c_crs, dest_crs, QgsProject.instance())
                        extent_3857 = ct.transformBoundingBox(c_ext)
                else:
                    extent_3857 = c_ext
        else:
            layer = self._selected_export_layer()
            if layer and layer.isValid() and not layer.extent().isEmpty():
                l_ext = layer.extent()
                l_crs = layer.crs()
                if l_crs.isValid() and l_crs != dest_crs:
                    with contextlib.suppress(Exception):
                        ct = QgsCoordinateTransform(l_crs, dest_crs, QgsProject.instance())
                        extent_3857 = ct.transformBoundingBox(l_ext)
                else:
                    extent_3857 = l_ext
            else:
                for lyr in QgsProject.instance().mapLayers().values():
                    if lyr.isValid() and lyr.type() == QgsMapLayerType.VectorLayer and not lyr.extent().isEmpty():
                        l_ext = lyr.extent()
                        if lyr.crs().isValid() and lyr.crs() != dest_crs:
                            with contextlib.suppress(Exception):
                                ct = QgsCoordinateTransform(lyr.crs(), dest_crs, QgsProject.instance())
                                l_ext = ct.transformBoundingBox(l_ext)
                        if l_ext.width() > 1000000.0 or l_ext.height() > 1000000.0:
                            continue
                        if extent_3857 is None:
                            extent_3857 = QgsRectangle(l_ext)
                        else:
                            extent_3857.combineExtentWith(l_ext)

        from ..core.gis_engine import estimate_mbtiles_tile_count
        count = estimate_mbtiles_tile_count(extent_3857, min_z, max_z) if extent_3857 else 0

        if count == 0:
            self.lbl_mbtiles_estimate.setText("Estimated: ~0 tiles (No active data extent)")
            self.lbl_mbtiles_estimate.setStyleSheet(
                "font-size: 11px; font-weight: normal; color: #546e7a; padding: 3px 6px; background: #eceff1; border-radius: 3px;"
            )
        elif count <= 250:
            self.lbl_mbtiles_estimate.setText(f"Estimated: ~{count:,} tiles (Fast, < 5 sec)")
            self.lbl_mbtiles_estimate.setStyleSheet(
                "font-size: 11px; font-weight: bold; color: #2e7d32; padding: 3px 6px; background: #e8f5e9; border-radius: 3px;"
            )
        elif count <= 2500:
            self.lbl_mbtiles_estimate.setText(f"Estimated: ~{count:,} tiles (Moderate, ~10-30 sec)")
            self.lbl_mbtiles_estimate.setStyleSheet(
                "font-size: 11px; font-weight: bold; color: #ef6c00; padding: 3px 6px; background: #fff3e0; border-radius: 3px;"
            )
        else:
            self.lbl_mbtiles_estimate.setText(f"⚠️ Warning: ~{count:,} tiles! (Reduce zoom range or use canvas extent)")
            self.lbl_mbtiles_estimate.setStyleSheet(
                "font-size: 11px; font-weight: bold; color: #c62828; padding: 3px 6px; background: #ffebee; border-radius: 3px;"
            )

    def _update_export_selection_scope(self, *_signal_args) -> None:
        """Keep selected-feature scope live as the canvas selection changes."""
        layer = self._selected_export_layer()
        selected_count = layer.selectedFeatureCount() if layer else 0
        self.chk_export_selected.setText(
            f"Selected features only ({selected_count} selected)")
        self.chk_export_selected.setEnabled(selected_count > 0)
        if selected_count == 0:
            self.chk_export_selected.setChecked(False)
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
        elif idx == 2:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export to KMZ Package", self._last_export_dir(), "Google Earth KMZ (*.kmz)"
            )
            file_path = ensure_extension(file_path, ".kmz")
        else:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export to Web Map Tiles (MBTiles)", self._last_export_dir(), "Web Map Tiles MBTiles (*.mbtiles)"
            )
            file_path = ensure_extension(file_path, ".mbtiles")

        if file_path:
            self.txt_exp_path.setText(file_path)
            QSettings().setValue("zero2cadgis/last_export_dir", os.path.dirname(file_path))
            self._update_export_button_state()

    def _update_export_button_state(self) -> None:
        has_layer = self.cmb_exp_layer.currentIndex() >= 0
        has_path = bool(self.txt_exp_path.text().strip())
        self.btn_run_export.setEnabled(has_layer and has_path)

    def _send_ncz_to_mbtiles_exporter(self) -> None:
        """Switch to Exporter tab preset for MBTiles export of current plan canvas."""
        self.main_tab.setCurrentIndex(2)
        self.cmb_exp_format.setCurrentIndex(3)
        self._populate_layers_combo()
        if self.cmb_exp_layer.count() > 0:
            self.cmb_exp_layer.setCurrentIndex(0)
        src_path = self.txt_ncz_path.text().strip()
        if src_path:
            base = os.path.splitext(os.path.basename(src_path))[0]
            out_dir = os.path.dirname(src_path)
            default_out = os.path.join(out_dir, f"{base}.mbtiles")
            self.txt_exp_path.setText(default_out)
        self._update_export_button_state()

    def _run_export_layer(self) -> None:
        layer_id = self.cmb_exp_layer.currentData()
        output_path = self.txt_exp_path.text()
        format_idx = self.cmb_exp_format.currentIndex()

        is_all_project = (layer_id == "__ALL_PROJECT_LAYERS__")
        layer = None if is_all_project else QgsProject.instance().mapLayer(layer_id)
        if not is_all_project and (not layer or not isinstance(layer, QgsVectorLayer)):
            QMessageBox.warning(
                self,
                "Export Warning",
                "Source layer is no longer valid.")
            return

        try:
            selected_only = self.chk_export_selected.isChecked() and not is_all_project
            if selected_only and layer and layer.selectedFeatureCount() == 0:
                raise ValueError(
                    "Selected-features mode is enabled, but the layer no "
                    "longer has a selection.")
            target_crs = self.export_crs.crs()
            if not target_crs.isValid() and format_idx != 3:
                raise ValueError("Choose a valid output CRS before exporting.")

            if format_idx == 0:  # DXF
                result = CadExportEngine.export_layer_to_dxf(
                    layer, output_path,
                    target_crs=target_crs,
                    selected_only=selected_only)
            elif format_idx == 1:  # KML
                result = GisConverterEngine.export_layer_to_gis(
                    layer, output_path, "KML",
                    target_crs=target_crs,
                    selected_only=selected_only)
            elif format_idx == 2:  # KMZ
                result = GisConverterEngine.export_layer_to_gis(
                    layer, output_path, "KMZ",
                    target_crs=target_crs,
                    selected_only=selected_only)
            else:  # MBTiles
                min_zoom = self.spn_mbtiles_min_zoom.value()
                max_zoom = self.spn_mbtiles_max_zoom.value()
                if min_zoom > max_zoom:
                    raise ValueError(
                        f"Minimum zoom ({min_zoom}) cannot exceed maximum zoom ({max_zoom}).")
                tile_format = "PNG" if self.cmb_mbtiles_tile_format.currentIndex() == 0 else "JPEG"
                dpi = self.spn_mbtiles_dpi.value()
                metatile = self.spn_mbtiles_metatile.value()
                extent_to_pass = None
                if getattr(self, "cmb_mbtiles_extent", None) and self.cmb_mbtiles_extent.currentIndex() == 1:
                    canvas = getattr(self, "iface", None) and self.iface.mapCanvas()
                    if canvas:
                        c_ext = canvas.extent()
                        c_crs = canvas.mapSettings().destinationCrs()
                        dest_crs = QgsCoordinateReferenceSystem("EPSG:3857")
                        if c_crs.isValid() and c_crs != dest_crs:
                            with contextlib.suppress(Exception):
                                ct = QgsCoordinateTransform(c_crs, dest_crs, QgsProject.instance())
                                extent_to_pass = ct.transformBoundingBox(c_ext)
                        else:
                            extent_to_pass = c_ext

                result = GisConverterEngine.export_to_mbtiles(
                    output_path=output_path,
                    layer=layer,
                    project=QgsProject.instance() if is_all_project else None,
                    extent=extent_to_pass,
                    min_zoom=min_zoom,
                    max_zoom=max_zoom,
                    tile_format=tile_format,
                    dpi=dpi,
                    metatile_size=metatile
                )

            size_mb = result.bytes_written / (1024 * 1024)
            if format_idx == 3:
                scope = (
                    "all project layers" if is_all_project
                    else f"layer '{layer.name()}'"
                )
                details = (
                    f"Verified {result.driver} export complete.\n\n"
                    f"Scope: {scope}\n"
                    f"Zoom Levels: {self.spn_mbtiles_min_zoom.value()} - {self.spn_mbtiles_max_zoom.value()}\n"
                    f"Tiles: {result.feature_count:,}\n"
                    f"Output CRS: {result.target_crs}\n"
                    f"File size: {size_mb:.2f} MB\n"
                    f"Path: {result.path}"
                )
            else:
                scope = "selected features" if selected_only else "all features"
                details = (
                    f"Verified {result.driver} export complete.\n\n"
                    f"Layer: {layer.name()}\n"
                    f"Scope: {scope}\n"
                    f"Features: {result.feature_count:,}\n"
                    f"Output CRS: {result.target_crs}\n"
                    f"File size: {size_mb:.2f} MB\n"
                    f"Path: {result.path}"
                )
            QMessageBox.information(
                self,
                "Export Complete",
                details)

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed exporting QGIS layer:\n{exc}")

    # ───────────────────────── TAB 3: Batch Spatial Filter Methods ───────────

    def _build_spatial_filter_tab(self, inner_widget: QWidget) -> None:
        filter_layout = QVBoxLayout(inner_widget)
        filter_layout.setContentsMargins(6, 6, 6, 6)
        filter_layout.setSpacing(6)

        # ── Group 1: Source Files / Directory ──
        src_group = QGroupBox("1. Candidate Drawings / GIS Datasets")
        src_vbox = QVBoxLayout(src_group)
        src_vbox.setContentsMargins(8, 12, 8, 8)
        src_vbox.setSpacing(3)

        mode_row = QHBoxLayout()
        self.rb_filter_src_dir = QRadioButton("Directory / Folder (Batch)")
        self.rb_filter_src_dir.setChecked(True)
        self.rb_filter_src_files = QRadioButton("Specific Files")
        self.filter_src_group = QButtonGroup(self)
        self.filter_src_group.addButton(self.rb_filter_src_dir)
        self.filter_src_group.addButton(self.rb_filter_src_files)
        self.filter_src_group.buttonToggled.connect(
            lambda *_: self._on_filter_source_mode_changed())
        mode_row.addWidget(self.rb_filter_src_dir)
        mode_row.addWidget(self.rb_filter_src_files)
        mode_row.addStretch(1)
        src_vbox.addLayout(mode_row)

        path_row = QHBoxLayout()
        self.txt_filter_source_path = QLineEdit()
        self.txt_filter_source_path.setPlaceholderText(
            "Select folder or drop files/folder here...")
        self.txt_filter_source_path.textChanged.connect(
            self._refresh_filter_discovered_files)
        path_row.addWidget(self.txt_filter_source_path, 1)

        self.btn_browse_filter_dir = QPushButton("Browse Folder...")
        self.btn_browse_filter_dir.clicked.connect(self._browse_filter_source_dir)
        path_row.addWidget(self.btn_browse_filter_dir)

        self.btn_browse_filter_files = QPushButton("Browse Files...")
        self.btn_browse_filter_files.setVisible(False)
        self.btn_browse_filter_files.clicked.connect(self._browse_filter_source_files)
        path_row.addWidget(self.btn_browse_filter_files)
        src_vbox.addLayout(path_row)

        opts_row = QHBoxLayout()
        self.chk_filter_recursive = QCheckBox("Scan subfolders recursively")
        self.chk_filter_recursive.setChecked(True)
        self.chk_filter_recursive.toggled.connect(
            self._refresh_filter_discovered_files)
        opts_row.addWidget(self.chk_filter_recursive)

        opts_row.addSpacing(10)
        opts_row.addWidget(QLabel("Format filter:"))
        self.cmb_filter_type = QComboBox()
        self.cmb_filter_type.addItem(
            "All Supported (*.ncz, *.dxf, *.dwg, *.kml, *.shp, *.gdb...)", "all")
        self.cmb_filter_type.addItem("Netcad Only (*.ncz, *.nca)", "netcad")
        self.cmb_filter_type.addItem("CAD Drawings (*.dxf, *.dwg, *.dgn)", "cad")
        self.cmb_filter_type.addItem(
            "GIS Vectors (*.shp, *.kml, *.kmz, *.gdb, *.geojson...)", "gis")
        self.cmb_filter_type.currentIndexChanged.connect(
            self._refresh_filter_discovered_files)
        opts_row.addWidget(self.cmb_filter_type, 1)
        src_vbox.addLayout(opts_row)

        self.lbl_filter_discovered = QLabel("0 candidate files ready for scanning.")
        self.lbl_filter_discovered.setObjectName("dock_subtitle")
        src_vbox.addWidget(self.lbl_filter_discovered)

        filter_layout.addWidget(src_group)

        # ── Group 2: Spatial Boundary Criteria ──
        bound_group = QGroupBox("2. Target Boundary Criteria")
        bound_vbox = QVBoxLayout(bound_group)
        bound_vbox.setContentsMargins(8, 12, 8, 8)
        bound_vbox.setSpacing(3)

        mode_row2 = QHBoxLayout()
        mode_row2.addWidget(QLabel("Boundary Source:"))
        self.cmb_filter_boundary_mode = QComboBox()
        self.cmb_filter_boundary_mode.addItem("Active Map Canvas Extent", "canvas")
        self.cmb_filter_boundary_mode.addItem(
            "Selected Feature(s) in Polygon Layer", "polygon")
        self.cmb_filter_boundary_mode.addItem("Print Layout Map Extent", "layout")
        self.cmb_filter_boundary_mode.addItem("Manual Bounding Box", "manual")
        self.cmb_filter_boundary_mode.currentIndexChanged.connect(
            self._on_filter_boundary_mode_changed)
        mode_row2.addWidget(self.cmb_filter_boundary_mode, 1)
        bound_vbox.addLayout(mode_row2)

        # A) Canvas info
        self.widget_filter_canvas = QWidget()
        canvas_layout = QHBoxLayout(self.widget_filter_canvas)
        canvas_layout.setContentsMargins(0, 2, 0, 2)
        self.lbl_canvas_extent_info = QLabel("Canvas extent: Loading...")
        self.lbl_canvas_extent_info.setObjectName("dock_subtitle")
        self.lbl_canvas_extent_info.setWordWrap(True)
        canvas_layout.addWidget(self.lbl_canvas_extent_info, 1)
        self.btn_refresh_canvas_extent = QPushButton("Refresh Canvas")
        self.btn_refresh_canvas_extent.clicked.connect(self._refresh_canvas_extent_info)
        canvas_layout.addWidget(self.btn_refresh_canvas_extent)
        bound_vbox.addWidget(self.widget_filter_canvas)

        # B) Polygon layer selector
        self.widget_filter_poly = QWidget()
        self.widget_filter_poly.setVisible(False)
        poly_layout = QVBoxLayout(self.widget_filter_poly)
        poly_layout.setContentsMargins(0, 2, 0, 2)
        poly_layout.setSpacing(2)
        poly_row = QHBoxLayout()
        poly_row.addWidget(QLabel("Polygon Layer:"))
        self.cmb_filter_poly_layer = QComboBox()
        self.cmb_filter_poly_layer.currentIndexChanged.connect(
            self._on_filter_poly_layer_changed)
        poly_row.addWidget(self.cmb_filter_poly_layer, 1)
        self.btn_zoom_filter_poly = QPushButton("Zoom to Layer")
        self.btn_zoom_filter_poly.clicked.connect(self._zoom_to_selected_polygon)
        poly_row.addWidget(self.btn_zoom_filter_poly)
        poly_layout.addLayout(poly_row)

        poly_opts = QHBoxLayout()
        self.chk_filter_use_selected_only = QCheckBox("Use only selected polygon features")
        self.chk_filter_use_selected_only.setChecked(True)
        self.chk_filter_use_selected_only.toggled.connect(
            self._update_filter_poly_selection_status)
        poly_opts.addWidget(self.chk_filter_use_selected_only)
        self.lbl_poly_selection_status = QLabel("0 features selected")
        self.lbl_poly_selection_status.setObjectName("dock_subtitle")
        poly_opts.addWidget(self.lbl_poly_selection_status)
        poly_opts.addStretch(1)
        poly_layout.addLayout(poly_opts)
        bound_vbox.addWidget(self.widget_filter_poly)

        # C) Print Layout selector
        self.widget_filter_layout = QWidget()
        self.widget_filter_layout.setVisible(False)
        layout_box = QVBoxLayout(self.widget_filter_layout)
        layout_box.setContentsMargins(0, 2, 0, 2)
        layout_row = QHBoxLayout()
        layout_row.addWidget(QLabel("Print Layout:"))
        self.cmb_filter_layout = QComboBox()
        self.cmb_filter_layout.currentIndexChanged.connect(
            self._on_filter_layout_changed)
        layout_row.addWidget(self.cmb_filter_layout, 1)
        layout_box.addLayout(layout_row)
        self.lbl_layout_extent_info = QLabel("Select a print layout.")
        self.lbl_layout_extent_info.setObjectName("dock_subtitle")
        layout_box.addWidget(self.lbl_layout_extent_info)
        bound_vbox.addWidget(self.widget_filter_layout)

        # D) Manual Bbox
        self.widget_filter_manual = QWidget()
        self.widget_filter_manual.setVisible(False)
        manual_box = QVBoxLayout(self.widget_filter_manual)
        manual_box.setContentsMargins(0, 2, 0, 2)
        m_row1 = QHBoxLayout()
        m_row1.addWidget(QLabel("Min X:"))
        self.txt_filter_minx = QLineEdit()
        m_row1.addWidget(self.txt_filter_minx)
        m_row1.addWidget(QLabel("Min Y:"))
        self.txt_filter_miny = QLineEdit()
        m_row1.addWidget(self.txt_filter_miny)
        manual_box.addLayout(m_row1)
        m_row2 = QHBoxLayout()
        m_row2.addWidget(QLabel("Max X:"))
        self.txt_filter_maxx = QLineEdit()
        m_row2.addWidget(self.txt_filter_maxx)
        m_row2.addWidget(QLabel("Max Y:"))
        self.txt_filter_maxy = QLineEdit()
        m_row2.addWidget(self.txt_filter_maxy)
        manual_box.addLayout(m_row2)
        m_row3 = QHBoxLayout()
        m_row3.addWidget(QLabel("Manual CRS:"))
        self.crs_filter_manual = QgsProjectionSelectionWidget(self)
        if QgsProject.instance().crs().isValid():
            self.crs_filter_manual.setCrs(QgsProject.instance().crs())
        m_row3.addWidget(self.crs_filter_manual, 1)
        self.btn_capture_manual_bbox = QPushButton("Capture Canvas")
        self.btn_capture_manual_bbox.clicked.connect(self._capture_manual_bbox_from_canvas)
        m_row3.addWidget(self.btn_capture_manual_bbox)
        manual_box.addLayout(m_row3)
        bound_vbox.addWidget(self.widget_filter_manual)

        # Spatial Predicate & Buffer distance
        match_params = QHBoxLayout()
        match_params.addWidget(QLabel("Predicate:"))
        self.cmb_filter_predicate = QComboBox()
        self.cmb_filter_predicate.addItem("Intersects (Any overlap)", "intersects")
        self.cmb_filter_predicate.addItem("Within (Completely inside)", "within")
        match_params.addWidget(self.cmb_filter_predicate, 1)

        match_params.addSpacing(10)
        match_params.addWidget(QLabel("Buffer:"))
        self.spin_filter_buffer = QDoubleSpinBox()
        self.spin_filter_buffer.setRange(-50000.0, 50000.0)
        self.spin_filter_buffer.setValue(0.0)
        self.spin_filter_buffer.setSuffix(" m")
        self.spin_filter_buffer.setSingleStep(10.0)
        self.spin_filter_buffer.setToolTip(
            "Expand or shrink search boundary by this distance (in meters) before testing.")
        match_params.addWidget(self.spin_filter_buffer)
        bound_vbox.addLayout(match_params)

        filter_layout.addWidget(bound_group)

        # ── Group 3: Filter Scan & Results ──
        res_group = QGroupBox("3. Spatial Scan && Matched Files")
        res_vbox = QVBoxLayout(res_group)
        res_vbox.setContentsMargins(8, 12, 8, 8)
        res_vbox.setSpacing(3)

        scan_btn_row = QHBoxLayout()
        self.btn_run_filter_scan = QPushButton("Scan && Filter Extents")
        self.btn_run_filter_scan.setObjectName("convert_btn")
        self.btn_run_filter_scan.clicked.connect(self._run_spatial_filter_scan)
        scan_btn_row.addWidget(self.btn_run_filter_scan, 1)

        self.btn_preview_footprints = QPushButton("Preview Footprints on Canvas")
        self.btn_preview_footprints.setEnabled(False)
        self.btn_preview_footprints.setToolTip(
            "Create a temporary polygon overlay on the map showing all file bounding boxes "
            "with labels, color-coded by match status.")
        self.btn_preview_footprints.clicked.connect(self._preview_footprints_on_canvas)
        scan_btn_row.addWidget(self.btn_preview_footprints)
        res_vbox.addLayout(scan_btn_row)

        self.progress_spatial_filter = QProgressBar()
        self.progress_spatial_filter.setVisible(False)
        res_vbox.addWidget(self.progress_spatial_filter)

        self.lbl_filter_scan_status = QLabel("Ready to scan.")
        self.lbl_filter_scan_status.setObjectName("dock_subtitle")
        res_vbox.addWidget(self.lbl_filter_scan_status)

        res_tools = QHBoxLayout()
        self.chk_filter_show_only_matched = QCheckBox("Show only matching files")
        self.chk_filter_show_only_matched.setChecked(True)
        self.chk_filter_show_only_matched.toggled.connect(
            self._on_filter_show_matched_toggled)
        res_tools.addWidget(self.chk_filter_show_only_matched)

        res_tools.addStretch(1)
        self.btn_filter_sel_all = QPushButton("Select All")
        self.btn_filter_sel_all.clicked.connect(
            lambda: self._set_filter_tree_checked_state(True))
        res_tools.addWidget(self.btn_filter_sel_all)

        self.btn_filter_desel_all = QPushButton("Deselect All")
        self.btn_filter_desel_all.clicked.connect(
            lambda: self._set_filter_tree_checked_state(False))
        res_tools.addWidget(self.btn_filter_desel_all)
        res_vbox.addLayout(res_tools)

        self.tree_filter_results = QTreeWidget()
        self.tree_filter_results.setHeaderLabels([
            "Status", "File Name", "Format", "Size", "CRS",
            "Extent (Xmin, Ymin, Xmax, Ymax)", "Path"
        ])
        self.tree_filter_results.setAlternatingRowColors(True)
        self.tree_filter_results.setRootIsDecorated(False)
        self.tree_filter_results.setSortingEnabled(True)
        self.tree_filter_results.itemChanged.connect(self._on_filter_tree_item_changed)
        self.tree_filter_results.itemDoubleClicked.connect(
            self._on_filter_tree_double_clicked)
        self.tree_filter_results.setMinimumHeight(140)
        res_vbox.addWidget(self.tree_filter_results)

        filter_layout.addWidget(res_group)

        # ── Group 4: Import / Action ──
        act_group = QGroupBox("4. Import Matched Files")
        act_vbox = QVBoxLayout(act_group)
        act_vbox.setContentsMargins(8, 12, 8, 8)
        act_vbox.setSpacing(3)

        out_mode_row = QHBoxLayout()
        self.rb_filter_out_qgis = QRadioButton("Directly into QGIS Canvas")
        self.rb_filter_out_qgis.setChecked(True)
        self.rb_filter_out_gpkg = QRadioButton("Unified GeoPackage")
        self.rb_filter_out_copy = QRadioButton("Copy matched files to folder")
        self.filter_out_group = QButtonGroup(self)
        self.filter_out_group.addButton(self.rb_filter_out_qgis)
        self.filter_out_group.addButton(self.rb_filter_out_gpkg)
        self.filter_out_group.addButton(self.rb_filter_out_copy)
        self.filter_out_group.buttonToggled.connect(
            lambda *_: self._on_filter_output_mode_changed())
        out_mode_row.addWidget(self.rb_filter_out_qgis)
        out_mode_row.addWidget(self.rb_filter_out_gpkg)
        out_mode_row.addWidget(self.rb_filter_out_copy)
        out_mode_row.addStretch(1)
        act_vbox.addLayout(out_mode_row)

        self.widget_filter_target = QWidget()
        self.widget_filter_target.setVisible(False)
        target_row = QHBoxLayout(self.widget_filter_target)
        target_row.setContentsMargins(0, 2, 0, 2)
        self.txt_filter_target_path = QLineEdit()
        self.txt_filter_target_path.setPlaceholderText("Select output destination...")
        target_row.addWidget(self.txt_filter_target_path, 1)
        self.btn_browse_filter_target = QPushButton("Browse...")
        self.btn_browse_filter_target.clicked.connect(self._browse_filter_target)
        target_row.addWidget(self.btn_browse_filter_target)
        act_vbox.addWidget(self.widget_filter_target)

        fallback_crs_row = QHBoxLayout()
        fallback_crs_row.addWidget(QLabel("Fallback / CAD CRS:"))
        self.cmb_filter_cad_crs = QComboBox()
        self.cmb_filter_cad_crs.addItem("Auto-detect / Project CRS", "")
        self.cmb_filter_cad_crs.addItem("EPSG:5254 (TUREF / TM30)", "EPSG:5254")
        self.cmb_filter_cad_crs.addItem("EPSG:7932 (ITRF96 / TM30)", "EPSG:7932")
        self.cmb_filter_cad_crs.addItem("EPSG:5255 (TUREF / TM33)", "EPSG:5255")
        self.cmb_filter_cad_crs.addItem("EPSG:5256 (TUREF / TM36)", "EPSG:5256")
        self.cmb_filter_cad_crs.addItem("EPSG:4326 (WGS 84)", "EPSG:4326")
        self.cmb_filter_cad_crs.addItem("EPSG:3857 (Web Mercator)", "EPSG:3857")
        self.cmb_filter_cad_crs.setToolTip(
            "Used for CAD/Netcad files that lack CRS headers or projection files.")
        fallback_crs_row.addWidget(self.cmb_filter_cad_crs, 1)
        act_vbox.addLayout(fallback_crs_row)

        import_row = QHBoxLayout()
        self.btn_filter_import = QPushButton("Import 0 Matched Files")
        self.btn_filter_import.setObjectName("convert_btn")
        self.btn_filter_import.setEnabled(False)
        self.btn_filter_import.clicked.connect(self._import_filtered_files)
        import_row.addWidget(self.btn_filter_import, 1)

        self.btn_filter_send_cad = QPushButton("Send to CAD Tab")
        self.btn_filter_send_cad.setToolTip(
            "Send the matched CAD/GIS files to the CAD & GIS Converter tab.")
        self.btn_filter_send_cad.setEnabled(False)
        self.btn_filter_send_cad.clicked.connect(self._send_filtered_to_cad_tab)
        import_row.addWidget(self.btn_filter_send_cad)

        self.btn_filter_send_ncz = QPushButton("Send to Netcad Tab")
        self.btn_filter_send_ncz.setToolTip(
            "Send only the matched Netcad files to Tab 2 for layer-by-layer inspection or official PlanGML styling.")
        self.btn_filter_send_ncz.setEnabled(False)
        self.btn_filter_send_ncz.clicked.connect(self._send_filtered_to_ncz_tab)
        import_row.addWidget(self.btn_filter_send_ncz)
        act_vbox.addLayout(import_row)

        filter_layout.addWidget(act_group)
        filter_layout.addStretch(1)

        self._refresh_canvas_extent_info()

    def _on_filter_source_mode_changed(self) -> None:
        is_dir = self.rb_filter_src_dir.isChecked()
        self.btn_browse_filter_dir.setVisible(is_dir)
        self.btn_browse_filter_files.setVisible(not is_dir)
        self.chk_filter_recursive.setEnabled(is_dir)
        self.txt_filter_source_path.clear()
        self.txt_filter_source_path.setPlaceholderText(
            "Select folder or drop folder here..." if is_dir else "Select files or drop files here..."
        )
        self._filter_discovered_files = []
        self._refresh_filter_discovered_files()

    def _browse_filter_source_dir(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self, "Select Directory Containing Drawings", self._last_import_dir()
        )
        if folder:
            self._remember_import_dir(folder)
            self.txt_filter_source_path.setText(folder)

    def _browse_filter_source_files(self) -> None:
        ext_pattern = " ".join(f"*{ext}" for ext in SUPPORTED_FILTER_EXTENSIONS)
        filter_str = (
            f"All Supported Files ({ext_pattern});;"
            "Netcad Drawings (*.ncz *.nca);;"
            "AutoCAD DXF/DWG (*.dxf *.dwg);;"
            "GIS Vectors (*.shp *.kml *.kmz *.geojson *.json *.gml *.sqlite *.gdb);;"
            "All Files (*.*)"
        )
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Candidate Files", self._last_import_dir(), filter_str
        )
        if files:
            self._remember_import_dir(files[0])
            self._apply_filter_source_paths(files)

    def _apply_filter_source_paths(self, paths: list[str]) -> None:
        if not paths:
            return
        if len(paths) == 1 and os.path.isdir(paths[0]) and not paths[0].lower().endswith(".gdb"):
            self.rb_filter_src_dir.setChecked(True)
            self.txt_filter_source_path.setText(paths[0])
        else:
            self.rb_filter_src_files.setChecked(True)
            valid = [
                p for p in paths
                if os.path.isfile(p) or (os.path.isdir(p) and p.lower().endswith(".gdb"))
            ]
            self._filter_discovered_files = valid
            self.txt_filter_source_path.setText(f"{len(valid)} candidate files selected")
            self._refresh_filter_discovered_files()

    def _refresh_filter_discovered_files(self, *_) -> None:
        type_key = self.cmb_filter_type.currentData() or "all"
        if type_key == "netcad":
            exts = (".ncz", ".nca")
        elif type_key == "cad":
            exts = (".dxf", ".dwg", ".dgn")
        elif type_key == "gis":
            exts = (
                ".shp", ".kml", ".kmz", ".gdb", ".geojson",
                ".json", ".gml", ".sqlite", ".db", ".gpx"
            )
        else:
            exts = SUPPORTED_FILTER_EXTENSIONS

        if self.rb_filter_src_dir.isChecked():
            folder = self.txt_filter_source_path.text().strip()
            if os.path.isdir(folder) and not folder.lower().endswith(".gdb"):
                self._filter_discovered_files = discover_files(
                    folder,
                    recursive=self.chk_filter_recursive.isChecked(),
                    extensions=exts,
                )
            else:
                self._filter_discovered_files = []
        else:
            if type_key != "all":
                self._filter_discovered_files = [
                    p for p in self._filter_discovered_files
                    if any(p.lower().endswith(ext) for ext in exts)
                ]

        count = len(self._filter_discovered_files)
        self.lbl_filter_discovered.setText(
            f"{count:,} candidate files discovered and ready to scan.")
        self.btn_run_filter_scan.setEnabled(count > 0)

    def _on_filter_boundary_mode_changed(self) -> None:
        mode = self.cmb_filter_boundary_mode.currentData()
        self.widget_filter_canvas.setVisible(mode == "canvas")
        self.widget_filter_poly.setVisible(mode == "polygon")
        self.widget_filter_layout.setVisible(mode == "layout")
        self.widget_filter_manual.setVisible(mode == "manual")

        if mode == "canvas":
            self._refresh_canvas_extent_info()
        elif mode == "polygon":
            self._populate_filter_polygon_layers()
        elif mode == "layout":
            self._populate_filter_layouts()

    def _on_map_canvas_extent_changed(self) -> None:
        if (hasattr(self, "cmb_filter_boundary_mode")
                and self.cmb_filter_boundary_mode.currentData() == "canvas"):
            self._refresh_canvas_extent_info()

    def _refresh_canvas_extent_info(self) -> None:
        if not hasattr(self, "lbl_canvas_extent_info"):
            return
        info_text = "Canvas extent unavailable."
        with suppress(Exception):
            if self.iface and hasattr(self.iface, "mapCanvas") and self.iface.mapCanvas():
                canvas = self.iface.mapCanvas()
                rect = canvas.extent()
                crs = canvas.mapSettings().destinationCrs()
                authid = crs.authid() if (hasattr(crs, "isValid") and crs.isValid()) else "Unknown CRS"
                xmin = float(rect.xMinimum())
                ymin = float(rect.yMinimum())
                xmax = float(rect.xMaximum())
                ymax = float(rect.yMaximum())
                info_text = (
                    f"Canvas Bounds: [{xmin:.2f}, {ymin:.2f}] - "
                    f"[{xmax:.2f}, {ymax:.2f}] ({authid})"
                )
        self.lbl_canvas_extent_info.setText(info_text)

    def _populate_filter_polygon_layers(self) -> None:
        if not hasattr(self, "cmb_filter_poly_layer"):
            return
        self.cmb_filter_poly_layer.blockSignals(True)
        prev_data = self.cmb_filter_poly_layer.currentData()
        self.cmb_filter_poly_layer.clear()

        for lyr_id in list(self._poly_selection_connections):
            lyr = QgsProject.instance().mapLayer(lyr_id)
            if lyr:
                with suppress(Exception):
                    lyr.selectionChanged.disconnect(
                        self._update_filter_poly_selection_status)
        self._poly_selection_connections.clear()

        for lyr in QgsProject.instance().mapLayers().values():
            if isinstance(lyr, QgsVectorLayer) and lyr.isValid():
                if QgsWkbTypes.geometryType(lyr.wkbType()) == QgsWkbTypes.GeometryType.Polygon:
                    self.cmb_filter_poly_layer.addItem(lyr.name(), lyr.id())
                    with suppress(Exception):
                        lyr.selectionChanged.connect(
                            self._update_filter_poly_selection_status)
                        self._poly_selection_connections.add(lyr.id())

        if prev_data is not None:
            idx = self.cmb_filter_poly_layer.findData(prev_data)
            if idx >= 0:
                self.cmb_filter_poly_layer.setCurrentIndex(idx)
        self.cmb_filter_poly_layer.blockSignals(False)
        self._update_filter_poly_selection_status()

    def _on_filter_poly_layer_changed(self, idx: int = -1) -> None:
        self._update_filter_poly_selection_status()

    def _update_filter_poly_selection_status(self) -> None:
        if (not hasattr(self, "cmb_filter_poly_layer")
                or not hasattr(self, "lbl_poly_selection_status")):
            return
        layer_id = self.cmb_filter_poly_layer.currentData()
        lyr = QgsProject.instance().mapLayer(layer_id) if layer_id else None
        if isinstance(lyr, QgsVectorLayer) and lyr.isValid():
            tot = lyr.featureCount()
            sel = lyr.selectedFeatureCount()
            if sel > 0:
                self.lbl_poly_selection_status.setText(
                    f"{tot:,} features ({sel:,} selected)")
            else:
                self.lbl_poly_selection_status.setText(
                    f"{tot:,} features (none selected -- using all features)")
        else:
            self.lbl_poly_selection_status.setText("No polygon layer in project.")

    def _zoom_to_selected_polygon(self) -> None:
        layer_id = self.cmb_filter_poly_layer.currentData()
        lyr = QgsProject.instance().mapLayer(layer_id) if layer_id else None
        if (isinstance(lyr, QgsVectorLayer) and lyr.isValid()
                and self.iface and self.iface.mapCanvas()):
            canvas = self.iface.mapCanvas()
            if (self.chk_filter_use_selected_only.isChecked()
                    and lyr.selectedFeatureCount() > 0):
                box = lyr.boundingBoxOfSelected()
            else:
                box = lyr.extent()
            dest_crs = canvas.mapSettings().destinationCrs()
            if lyr.crs().isValid() and dest_crs.isValid() and lyr.crs() != dest_crs:
                transform = QgsCoordinateTransform(
                    lyr.crs(), dest_crs, QgsProject.instance())
                box = transform.transformBoundingBox(box)
            canvas.setExtent(box)
            canvas.refresh()

    def _populate_filter_layouts(self) -> None:
        if not hasattr(self, "cmb_filter_layout"):
            return
        self.cmb_filter_layout.blockSignals(True)
        self.cmb_filter_layout.clear()
        layouts = QgsProject.instance().layoutManager().printLayouts()
        for lay in layouts:
            self.cmb_filter_layout.addItem(lay.name(), lay.name())
        self.cmb_filter_layout.blockSignals(False)
        self._on_filter_layout_changed()

    def _on_filter_layout_changed(self, idx: int = -1) -> None:
        if not hasattr(self, "lbl_layout_extent_info"):
            return
        name = self.cmb_filter_layout.currentText()
        if not name:
            self.lbl_layout_extent_info.setText("No print layouts in project.")
            return
        layout = QgsProject.instance().layoutManager().layoutByName(name)
        if not layout:
            self.lbl_layout_extent_info.setText("Layout not found.")
            return
        map_item = layout.referenceMap()
        if not map_item:
            for item in layout.items():
                if isinstance(item, QgsLayoutItemMap):
                    map_item = item
                    break
        if map_item:
            ext = map_item.extent()
            crs = map_item.crs()
            self.lbl_layout_extent_info.setText(
                f"Map Item Bounds: [{ext.xMinimum():.1f}, {ext.yMinimum():.1f}] - "
                f"[{ext.xMaximum():.1f}, {ext.yMaximum():.1f}] "
                f"({crs.authid() if crs.isValid() else 'Unknown'})"
            )
        else:
            self.lbl_layout_extent_info.setText("Layout has no map item.")

    def _capture_manual_bbox_from_canvas(self) -> None:
        with suppress(Exception):
            if self.iface and hasattr(self.iface, "mapCanvas") and self.iface.mapCanvas():
                canvas = self.iface.mapCanvas()
                ext = canvas.extent()
                crs = canvas.mapSettings().destinationCrs()
                self.txt_filter_minx.setText(f"{float(ext.xMinimum()):.4f}")
                self.txt_filter_miny.setText(f"{float(ext.yMinimum()):.4f}")
                self.txt_filter_maxx.setText(f"{float(ext.xMaximum()):.4f}")
                self.txt_filter_maxy.setText(f"{float(ext.yMaximum()):.4f}")
                if hasattr(crs, "isValid") and crs.isValid():
                    self.crs_filter_manual.setCrs(crs)

    def _get_current_boundary_geometry(
            self) -> tuple[QgsGeometry | None, QgsCoordinateReferenceSystem | None]:
        mode = self.cmb_filter_boundary_mode.currentData()

        if mode == "canvas":
            if not self.iface or not hasattr(self.iface, "mapCanvas") or not self.iface.mapCanvas():
                raise ValueError("Map canvas is not available.")
            canvas = self.iface.mapCanvas()
            rect = canvas.extent()
            crs = canvas.mapSettings().destinationCrs()
            return QgsGeometry.fromRect(rect), crs

        if mode == "polygon":
            layer_id = self.cmb_filter_poly_layer.currentData()
            lyr = QgsProject.instance().mapLayer(layer_id) if layer_id else None
            if not isinstance(lyr, QgsVectorLayer) or not lyr.isValid():
                raise ValueError("Please select a valid polygon layer.")

            use_selected = self.chk_filter_use_selected_only.isChecked()
            if use_selected and lyr.selectedFeatureCount() > 0:
                features = list(lyr.selectedFeatures())
            else:
                features = list(lyr.getFeatures())

            geoms = [
                f.geometry() for f in features
                if f.hasGeometry() and not f.geometry().isEmpty()
            ]
            if not geoms:
                raise ValueError("Selected layer has no valid polygon geometries.")

            union_geom = QgsGeometry.unaryUnion(geoms)
            return union_geom, lyr.crs()

        if mode == "layout":
            name = self.cmb_filter_layout.currentText()
            if not name:
                raise ValueError("Please select a print layout.")
            layout = QgsProject.instance().layoutManager().layoutByName(name)
            if not layout:
                raise ValueError(f"Layout '{name}' not found.")
            map_item = layout.referenceMap()
            if not map_item:
                for item in layout.items():
                    if isinstance(item, QgsLayoutItemMap):
                        map_item = item
                        break
            if not map_item:
                raise ValueError(f"Layout '{name}' contains no map items.")
            rect = map_item.extent()
            crs = map_item.crs()
            return QgsGeometry.fromRect(rect), crs

        if mode == "manual":
            try:
                x_min = float(self.txt_filter_minx.text().strip())
                y_min = float(self.txt_filter_miny.text().strip())
                x_max = float(self.txt_filter_maxx.text().strip())
                y_max = float(self.txt_filter_maxy.text().strip())
            except ValueError:
                raise ValueError(
                    "Please enter valid numeric coordinates for Min/Max X and Y.")
            rect = QgsRectangle(x_min, y_min, x_max, y_max)
            crs = self.crs_filter_manual.crs()
            return QgsGeometry.fromRect(rect), crs

        return None, None

    def _run_spatial_filter_scan(self) -> None:
        if not self._filter_discovered_files:
            self._refresh_filter_discovered_files()
            if not self._filter_discovered_files:
                QMessageBox.warning(
                    self, "No Files",
                    "Please select a directory or candidate files to scan.")
                return

        try:
            boundary_geom, boundary_crs = self._get_current_boundary_geometry()
        except Exception as exc:
            QMessageBox.warning(self, "Invalid Boundary", str(exc))
            return

        if boundary_geom is None or boundary_geom.isEmpty():
            QMessageBox.warning(
                self, "Empty Boundary",
                "The specified boundary geometry is empty.")
            return

        predicate = self.cmb_filter_predicate.currentData() or "intersects"
        buffer_dist = self.spin_filter_buffer.value()
        fallback_crs = self.cmb_filter_cad_crs.currentData()
        if not fallback_crs and boundary_crs and boundary_crs.isValid():
            fallback_crs = boundary_crs.authid()

        total = len(self._filter_discovered_files)
        self.progress_spatial_filter.setVisible(True)
        self.progress_spatial_filter.setValue(0)
        self.lbl_filter_scan_status.setText(
            f"Scanning {total} candidate files...")
        QApplication.processEvents()

        t0 = time.monotonic()

        def on_progress(done: int, tot: int, filename: str) -> None:
            pct = int((done / max(tot, 1)) * 100)
            self.progress_spatial_filter.setValue(pct)
            self.progress_spatial_filter.setFormat(
                f"Scanning {done}/{tot}: {filename}...")
            QApplication.processEvents()

        try:
            self._spatial_filter_results = scan_and_filter_files(
                self._filter_discovered_files,
                target_geometry=boundary_geom,
                target_crs=boundary_crs,
                predicate=predicate,
                buffer_distance=buffer_dist,
                fallback_crs=fallback_crs,
                progress_callback=on_progress,
            )
            elapsed = time.monotonic() - t0
            self.progress_spatial_filter.setValue(100)
            self.progress_spatial_filter.setVisible(False)

            self._populate_filter_results_tree()

            matched_count = sum(1 for r in self._spatial_filter_results if r.matches)
            self.lbl_filter_scan_status.setText(
                f"Scan complete in {elapsed:.2f}s: {matched_count:,} matched out of "
                f"{total:,} candidate files ({total - matched_count:,} excluded)."
            )
            self.btn_preview_footprints.setEnabled(
                len(self._spatial_filter_results) > 0)

        except Exception as exc:
            self.progress_spatial_filter.setVisible(False)
            QMessageBox.critical(
                self, "Scan Error",
                f"Failed scanning candidate files:\n{exc}")

    def _populate_filter_results_tree(self) -> None:
        self.tree_filter_results.blockSignals(True)
        self.tree_filter_results.clear()

        show_only_matched = self.chk_filter_show_only_matched.isChecked()

        for res in self._spatial_filter_results:
            item = QTreeWidgetItem()
            status_text = (
                "Matched" if res.matches
                else ("Error" if res.error else "Outside")
            )
            item.setText(0, status_text)
            item.setCheckState(
                0,
                Qt.CheckState.Checked if res.matches else Qt.CheckState.Unchecked)

            if res.matches:
                item.setForeground(0, QBrush(QColor("#2e7d32")))
                item.setForeground(1, QBrush(QColor("#1b5e20")))
            elif res.error:
                item.setForeground(0, QBrush(QColor("#c62828")))
                item.setForeground(1, QBrush(QColor("#b71c1c")))
            else:
                item.setForeground(0, QBrush(QColor("#78909c")))
                item.setForeground(1, QBrush(QColor("#546e7a")))

            item.setText(1, res.file_name)
            item.setText(2, res.format_key.upper())
            item.setText(3, res.formatted_size)
            item.setText(4, res.crs_authid or "Unknown")
            if res.box.is_valid:
                ext_str = (
                    f"[{res.box.min_x:.1f}, {res.box.min_y:.1f}] - "
                    f"[{res.box.max_x:.1f}, {res.box.max_y:.1f}]"
                )
            else:
                ext_str = res.error or "Invalid extent"
            item.setText(5, ext_str)
            item.setText(6, res.file_path)
            item.setData(0, Qt.ItemDataRole.UserRole, res)

            if show_only_matched and not res.matches:
                item.setHidden(True)

            self.tree_filter_results.addTopLevelItem(item)

        for col in range(5):
            self.tree_filter_results.resizeColumnToContents(col)

        self.tree_filter_results.blockSignals(False)
        self._update_filter_import_button_count()

    def _on_filter_tree_item_changed(
            self, item: QTreeWidgetItem, column: int) -> None:
        if column == 0:
            self._update_filter_import_button_count()

    def _update_filter_import_button_count(self) -> None:
        count = 0
        has_ncz = False
        for idx in range(self.tree_filter_results.topLevelItemCount()):
            it = self.tree_filter_results.topLevelItem(idx)
            if it.checkState(0) == Qt.CheckState.Checked:
                count += 1
                if it.text(2) in ("NCZ", "NCA"):
                    has_ncz = True

        self.btn_filter_import.setText(f"Import {count} Checked Files")
        self.btn_filter_import.setEnabled(count > 0)
        self.btn_filter_send_cad.setEnabled(count > 0)
        self.btn_filter_send_ncz.setEnabled(has_ncz)

    def _on_filter_show_matched_toggled(self, checked: bool) -> None:
        for idx in range(self.tree_filter_results.topLevelItemCount()):
            item = self.tree_filter_results.topLevelItem(idx)
            res = item.data(0, Qt.ItemDataRole.UserRole)
            if checked:
                item.setHidden(not (res and res.matches))
            else:
                item.setHidden(False)

    def _set_filter_tree_checked_state(self, select_matched: bool) -> None:
        self.tree_filter_results.blockSignals(True)
        for idx in range(self.tree_filter_results.topLevelItemCount()):
            item = self.tree_filter_results.topLevelItem(idx)
            res = item.data(0, Qt.ItemDataRole.UserRole)
            if select_matched:
                item.setCheckState(
                    0,
                    Qt.CheckState.Checked if (res and res.matches)
                    else Qt.CheckState.Unchecked)
            else:
                item.setCheckState(0, Qt.CheckState.Unchecked)
        self.tree_filter_results.blockSignals(False)
        self._update_filter_import_button_count()

    def _on_filter_tree_double_clicked(
            self, item: QTreeWidgetItem, column: int) -> None:
        res = item.data(0, Qt.ItemDataRole.UserRole)
        if not res or not res.box.is_valid:
            return
        if self.iface and hasattr(self.iface, "mapCanvas") and self.iface.mapCanvas():
            canvas = self.iface.mapCanvas()
            rect = QgsRectangle(
                res.box.min_x, res.box.min_y, res.box.max_x, res.box.max_y)
            src_crs = (
                QgsCoordinateReferenceSystem(res.crs_authid)
                if res.crs_authid
                else canvas.mapSettings().destinationCrs()
            )
            dest_crs = canvas.mapSettings().destinationCrs()
            if src_crs.isValid() and dest_crs.isValid() and src_crs != dest_crs:
                with suppress(Exception):
                    transform = QgsCoordinateTransform(
                        src_crs, dest_crs, QgsProject.instance())
                    rect = transform.transformBoundingBox(rect)
            canvas.setExtent(rect)
            canvas.refresh()

    def _preview_footprints_on_canvas(self) -> None:
        if not self._spatial_filter_results:
            return

        target_crs = QgsProject.instance().crs()
        if not target_crs.isValid():
            target_crs = QgsCoordinateReferenceSystem("EPSG:4326")

        layer = QgsVectorLayer(
            f"Polygon?crs={target_crs.authid()}",
            "02CadGis Filter Footprints", "memory")
        provider = layer.dataProvider()
        provider.addAttributes([
            QgsField("filename", QMetaType.Type.QString),
            QgsField("status", QMetaType.Type.QString),
            QgsField("format", QMetaType.Type.QString),
            QgsField("size", QMetaType.Type.QString),
            QgsField("crs", QMetaType.Type.QString),
            QgsField("path", QMetaType.Type.QString),
        ])
        layer.updateFields()

        features = []
        for res in self._spatial_filter_results:
            if not res.box.is_valid:
                continue
            rect = QgsRectangle(
                res.box.min_x, res.box.min_y, res.box.max_x, res.box.max_y)
            geom = QgsGeometry.fromRect(rect)
            src_crs = (
                QgsCoordinateReferenceSystem(res.crs_authid)
                if res.crs_authid
                else target_crs
            )
            if src_crs.isValid() and target_crs.isValid() and src_crs != target_crs:
                with suppress(Exception):
                    transform = QgsCoordinateTransform(
                        src_crs, target_crs, QgsProject.instance())
                    geom.transform(transform)

            feat = QgsFeature(layer.fields())
            feat.setGeometry(geom)
            status = "Matched" if res.matches else "Outside"
            feat.setAttribute("filename", res.file_name)
            feat.setAttribute("status", status)
            feat.setAttribute("format", res.format_key.upper())
            feat.setAttribute("size", res.formatted_size)
            feat.setAttribute("crs", res.crs_authid or "Unknown")
            feat.setAttribute("path", res.file_path)
            features.append(feat)

        if features:
            provider.addFeatures(features)
            layer.updateExtents()

        from qgis.core import (
            QgsCategorizedSymbolRenderer,
            QgsRendererCategory,
            QgsFillSymbol,
            QgsPalLayerSettings,
            QgsVectorLayerSimpleLabeling,
            QgsTextFormat,
            QgsTextBufferSettings,
        )

        sym_match = QgsFillSymbol.createSimple({
            "color": "46,125,50,45",
            "outline_color": "46,125,50,230",
            "outline_width": "0.6",
        })
        cat_match = QgsRendererCategory(
            "Matched", sym_match, "Matched (Inside boundary)")

        sym_out = QgsFillSymbol.createSimple({
            "color": "158,158,158,20",
            "outline_color": "120,144,156,150",
            "outline_width": "0.3",
        })
        cat_out = QgsRendererCategory("Outside", sym_out, "Outside boundary")

        renderer = QgsCategorizedSymbolRenderer("status", [cat_match, cat_out])
        layer.setRenderer(renderer)

        pal = QgsPalLayerSettings()
        pal.fieldName = "filename"
        text_fmt = QgsTextFormat()
        text_fmt.setSize(8.5)
        text_fmt.setColor(QColor("#263238"))
        buf = QgsTextBufferSettings()
        buf.setEnabled(True)
        buf.setSize(1.0)
        buf.setColor(QColor(255, 255, 255, 220))
        text_fmt.setBuffer(buf)
        pal.setFormat(text_fmt)
        layer.setLabeling(QgsVectorLayerSimpleLabeling(pal))
        layer.setLabelsEnabled(True)

        QgsProject.instance().addMapLayer(layer)
        if self.iface:
            self.iface.messageBar().pushMessage(
                "02CadGis",
                f"Footprint preview layer added with {len(features)} drawing extents.",
                Qgis.MessageLevel.Success, 5,
            )

    def _on_filter_output_mode_changed(self) -> None:
        is_qgis = self.rb_filter_out_qgis.isChecked()
        self.widget_filter_target.setVisible(not is_qgis)
        if self.rb_filter_out_gpkg.isChecked():
            self.txt_filter_target_path.setPlaceholderText(
                "Select destination GeoPackage (.gpkg)...")
        else:
            self.txt_filter_target_path.setPlaceholderText(
                "Select destination directory...")

    def _browse_filter_target(self) -> None:
        if self.rb_filter_out_gpkg.isChecked():
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Select Destination GeoPackage",
                self._last_import_dir(), "GeoPackage (*.gpkg)"
            )
            if file_path:
                if not file_path.lower().endswith(".gpkg"):
                    file_path += ".gpkg"
                self.txt_filter_target_path.setText(file_path)
        else:
            folder = QFileDialog.getExistingDirectory(
                self, "Select Destination Directory", self._last_import_dir()
            )
            if folder:
                self.txt_filter_target_path.setText(folder)

    def _send_filtered_to_ncz_tab(self) -> None:
        ncz_paths = []
        for idx in range(self.tree_filter_results.topLevelItemCount()):
            it = self.tree_filter_results.topLevelItem(idx)
            if it.checkState(0) == Qt.CheckState.Checked and it.text(2) in ("NCZ", "NCA"):
                res = it.data(0, Qt.ItemDataRole.UserRole)
                if res and res.file_path:
                    ncz_paths.append(res.file_path)

        if not ncz_paths:
            QMessageBox.information(
                self, "No Netcad Files",
                "No checked Netcad drawing files found in the results.")
            return

        self._load_ncz_paths(ncz_paths)
        self.main_tab.setCurrentIndex(1)
        if hasattr(self, "spatial_filter_dialog") and self.spatial_filter_dialog.isVisible():
            self.spatial_filter_dialog.hide()
        if self.iface:
            self.iface.messageBar().pushMessage(
                "02CadGis",
                f"Transferred {len(ncz_paths)} matched Netcad drawings to Netcad tab.",
                Qgis.MessageLevel.Success, 5,
            )

    def _send_filtered_to_cad_tab(self) -> None:
        cad_paths = []
        for idx in range(self.tree_filter_results.topLevelItemCount()):
            it = self.tree_filter_results.topLevelItem(idx)
            if it.checkState(0) == Qt.CheckState.Checked:
                res = it.data(0, Qt.ItemDataRole.UserRole)
                if res and res.file_path:
                    cad_paths.append(res.file_path)

        if not cad_paths:
            QMessageBox.information(
                self, "No Files Selected",
                "No checked drawing or GIS files found in the results.")
            return

        fmt = format_for_path(cad_paths[0]) or SOURCE_FORMATS[0]
        self._apply_source_path(cad_paths[0], fmt)
        self.main_tab.setCurrentIndex(0)
        if hasattr(self, "spatial_filter_dialog") and self.spatial_filter_dialog.isVisible():
            self.spatial_filter_dialog.hide()
        if self.iface:
            self.iface.messageBar().pushMessage(
                "02CadGis",
                f"Transferred {len(cad_paths)} matched files to CAD tab (primary: {os.path.basename(cad_paths[0])}).",
                Qgis.MessageLevel.Success, 5,
            )

    def _filter_current_cad_by_extent(self) -> None:
        src = self.txt_src_path.text().strip()
        if src:
            self._apply_filter_source_paths([src])
            self._run_spatial_filter_scan()
        self.cmb_filter_type.setCurrentIndex(0)
        self.spatial_filter_dialog.show()
        self.spatial_filter_dialog.raise_()
        self.spatial_filter_dialog.activateWindow()

    def _filter_current_ncz_by_extent(self) -> None:
        if self.current_netcad_paths:
            self._apply_filter_source_paths(self.current_netcad_paths)
            self._run_spatial_filter_scan()
        elif self.txt_ncz_path.text().strip():
            self._apply_filter_source_paths([self.txt_ncz_path.text().strip()])
            self._run_spatial_filter_scan()
        self.cmb_filter_type.setCurrentIndex(1)
        self.spatial_filter_dialog.show()
        self.spatial_filter_dialog.raise_()
        self.spatial_filter_dialog.activateWindow()

    def _import_filtered_files(self) -> None:
        checked_results = []
        for idx in range(self.tree_filter_results.topLevelItemCount()):
            it = self.tree_filter_results.topLevelItem(idx)
            if it.checkState(0) == Qt.CheckState.Checked:
                res = it.data(0, Qt.ItemDataRole.UserRole)
                if res:
                    checked_results.append(res)

        if not checked_results:
            QMessageBox.warning(
                self, "No Selection",
                "Please check at least one file to import.")
            return

        fallback_crs = self.cmb_filter_cad_crs.currentData() or ""

        # Mode 3: Copy to folder
        if self.rb_filter_out_copy.isChecked():
            dest_dir = self.txt_filter_target_path.text().strip()
            if not dest_dir or not os.path.isdir(dest_dir):
                QMessageBox.warning(
                    self, "Invalid Directory",
                    "Please select a valid destination directory.")
                return

            copied = 0
            for r in checked_results:
                src_path = r.file_path
                base = os.path.basename(src_path)
                target_file = os.path.join(dest_dir, base)
                with suppress(Exception):
                    if os.path.isdir(src_path) and src_path.lower().endswith(".gdb"):
                        shutil.copytree(src_path, target_file, dirs_exist_ok=True)
                    else:
                        shutil.copy2(src_path, target_file)
                        if src_path.lower().endswith(".shp"):
                            stem = os.path.splitext(src_path)[0]
                            for ext in (".dbf", ".shx", ".prj", ".cpg", ".qpj"):
                                sidecar = stem + ext
                                if os.path.exists(sidecar):
                                    shutil.copy2(
                                        sidecar,
                                        os.path.join(
                                            dest_dir, os.path.basename(sidecar)))
                    copied += 1

            QMessageBox.information(
                self,
                "Copy Complete",
                f"Successfully copied {copied} of {len(checked_results)} files to:\n{dest_dir}"
            )
            return

        # Mode 2: Unified GeoPackage
        if self.rb_filter_out_gpkg.isChecked():
            dst_gpkg = self.txt_filter_target_path.text().strip()
            if not dst_gpkg:
                QMessageBox.warning(
                    self, "Invalid GeoPackage",
                    "Please choose a target .gpkg file path.")
                return
            if not dst_gpkg.lower().endswith(".gpkg"):
                dst_gpkg += ".gpkg"

            self.progress_spatial_filter.setVisible(True)
            self.progress_spatial_filter.setValue(10)
            self.progress_spatial_filter.setFormat(
                "Converting matched files to GeoPackage...")
            QApplication.processEvents()

            target_crs = QgsProject.instance().crs()
            if not target_crs.isValid():
                target_crs = QgsCoordinateReferenceSystem("EPSG:4326")

            success_count = 0
            for idx, r in enumerate(checked_results):
                self.progress_spatial_filter.setValue(
                    10 + int((idx / len(checked_results)) * 80))
                self.progress_spatial_filter.setFormat(
                    f"Writing {r.file_name} to GeoPackage...")
                QApplication.processEvents()

                with suppress(Exception):
                    if r.file_path.lower().endswith(NCZ_EXTENSIONS):
                        layers = self._import_single_ncz_file_to_layers(
                            r.file_path, fallback_crs)
                        for lyr in layers:
                            safe_name = self._sanitize_name(lyr.name())
                            opts = QgsVectorFileWriter.SaveVectorOptions()
                            opts.driverName = "GPKG"
                            opts.layerName = safe_name
                            opts.actionOnExistingFile = (
                                QgsVectorFileWriter.ActionOnExistingFile.CreateOrOverwriteLayer
                            )
                            opts.fileEncoding = "UTF-8"
                            QgsVectorFileWriter.writeAsVectorFormatV3(
                                lyr, dst_gpkg,
                                QgsProject.instance().transformContext(), opts
                            )
                        success_count += 1
                    else:
                        converter = GisConverterEngine(
                            r.file_path, dst_gpkg, target_crs,
                            source_crs=target_crs
                        )
                        converter.convert_to_gpkg()
                        success_count += 1

            self.progress_spatial_filter.setValue(100)
            self.progress_spatial_filter.setVisible(False)

            import_group = QgsProject.instance().layerTreeRoot().addGroup(
                f"02CadGis GeoPackage ({os.path.basename(dst_gpkg)})"
            )
            loaded_gpkg = QgsVectorLayer(
                dst_gpkg, os.path.basename(dst_gpkg), "ogr")
            if loaded_gpkg.isValid():
                sublayers = loaded_gpkg.dataProvider().subLayers()
                for sub in sublayers:
                    parts = sub.split("!!::!!")
                    sub_uri = parts[0]
                    sub_name = parts[1] if len(parts) > 1 else "layer"
                    sub_lyr = QgsVectorLayer(sub_uri, sub_name, "ogr")
                    if sub_lyr.isValid():
                        QgsProject.instance().addMapLayer(sub_lyr, False)
                        import_group.addLayer(sub_lyr)

            QMessageBox.information(
                self,
                "GeoPackage Created",
                f"Successfully converted {success_count} of {len(checked_results)} files into:\n{dst_gpkg}"
            )
            return

        # Mode 1: Directly into QGIS canvas
        self.progress_spatial_filter.setVisible(True)
        self.progress_spatial_filter.setValue(10)
        self.progress_spatial_filter.setFormat(
            "Loading matched files into canvas...")
        QApplication.processEvents()

        root = QgsProject.instance().layerTreeRoot()
        import_group = root.addGroup(
            f"02CadGis Filtered ({len(checked_results)} files)")
        success_count = 0

        for idx, r in enumerate(checked_results):
            self.progress_spatial_filter.setValue(
                10 + int((idx / len(checked_results)) * 80))
            self.progress_spatial_filter.setFormat(
                f"Importing {r.file_name}...")
            QApplication.processEvents()

            with suppress(Exception):
                if r.file_path.lower().endswith(NCZ_EXTENSIONS):
                    layers = self._import_single_ncz_file_to_layers(
                        r.file_path, fallback_crs)
                    if layers:
                        sub_group = import_group.addGroup(r.file_name)
                        for lyr in layers:
                            QgsProject.instance().addMapLayer(lyr, False)
                            sub_group.addLayer(lyr)
                        success_count += 1
                else:
                    vlayer = QgsVectorLayer(r.file_path, r.file_name, "ogr")
                    if vlayer.isValid():
                        sublayers = vlayer.dataProvider().subLayers()
                        if len(sublayers) > 1:
                            sub_group = import_group.addGroup(r.file_name)
                            for sub in sublayers:
                                parts = sub.split("!!::!!")
                                sub_uri = parts[0]
                                sub_name = (
                                    parts[1] if len(parts) > 1 else r.file_name
                                )
                                sub_lyr = QgsVectorLayer(
                                    sub_uri, f"{r.file_name} - {sub_name}", "ogr")
                                if sub_lyr.isValid():
                                    QgsProject.instance().addMapLayer(
                                        sub_lyr, False)
                                    sub_group.addLayer(sub_lyr)
                        else:
                            QgsProject.instance().addMapLayer(vlayer, False)
                            import_group.addLayer(vlayer)
                        success_count += 1

        self.progress_spatial_filter.setValue(100)
        self.progress_spatial_filter.setVisible(False)

        if self.iface and hasattr(self.iface, "mapCanvas") and self.iface.mapCanvas():
            self.iface.mapCanvas().refresh()

        self._populate_layers_combo()

        QMessageBox.information(
            self,
            "Import Complete",
            f"Successfully imported {success_count} of {len(checked_results)} datasets into QGIS canvas."
        )

    def _import_single_ncz_file_to_layers(
            self, file_path: str, fallback_crs: str) -> list[QgsVectorLayer]:
        reader = NetcadLazyReader(file_path).index()
        summaries = reader.layer_summaries()
        wanted_codes = {s.layer_code for s in summaries if s.record_count > 0}
        if not wanted_codes:
            return []
        entities = reader.decode_layers(wanted_codes)
        if not entities:
            return []

        from ..core.crs_detect import detect_crs
        detection = detect_crs(reader.projection_text, reader.sample_coordinates())
        authid = (
            detection.authid if detection and detection.epsg
            else (fallback_crs or "EPSG:5254")
        )
        target_crs = QgsCoordinateReferenceSystem(authid)
        if not target_crs.isValid():
            target_crs = QgsProject.instance().crs()

        base_name = self._sanitize_name(
            os.path.splitext(os.path.basename(file_path))[0])
        grouped: dict = {}
        for entity in entities:
            family, geom_type = self._geometry_family(
                entity.geometry_kind, entity.is_closed, entity.coordinates)
            if not family:
                continue

            group_name = f"{base_name}_{family}"
            bucket_key = (entity.layer_code, entity.layer_name or "LAYER", family)
            bucket = grouped.setdefault(group_name, {}).setdefault(
                bucket_key,
                LayerBucket(
                    display_name=f"{base_name}_{self._sanitize_name(entity.layer_name or 'LAYER')}_{family}",
                    geometry_type=geom_type,
                ),
            )
            bucket.entities.append(entity)
            bucket.source_files[id(entity)] = base_name

        is_plangml = getattr(self, "chk_ncz_plan_symbology", None) is None or self.chk_ncz_plan_symbology.isChecked()
        if is_plangml:
            with suppress(Exception):
                from ..core.cad_polygonizer import polygonize_cad_entities
                line_entities = [
                    e for e in entities
                    if e.geometry_kind in ("Line", "Polyline", "Arc") or not e.is_closed
                ]
                for entity in polygonize_cad_entities(line_entities):
                    family, geom_type = self._geometry_family(
                        entity.geometry_kind, entity.is_closed, entity.coordinates)
                    if not family:
                        continue
                    group_name = f"{base_name}_{family}"
                    bucket_key = (entity.layer_code, entity.layer_name or "LAYER", family)
                    bucket = grouped.setdefault(group_name, {}).setdefault(
                        bucket_key,
                        LayerBucket(
                            display_name=f"{base_name}_{self._sanitize_name(entity.layer_name or 'LAYER')}_{family}",
                            geometry_type=geom_type,
                        ),
                    )
                    bucket.entities.append(entity)
                    bucket.source_files[id(entity)] = base_name

        layer_groups = self._build_layer_groups_from_buckets(
            grouped, target_crs)
        result_layers = []
        for g in layer_groups:
            result_layers.extend(g.layers)
        return result_layers

