# -*- coding: utf-8 -*-
"""zero2gpkg_converter — Main plugin entry class.
100% English, fully compatible with PlanX menu structure.
"""
from __future__ import annotations

import os

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMenu, QToolBar, QMessageBox


class Zero2GpkgConverter:
    MENU_NAME = "PlanX"
    TOOLBAR_NAME = "02gpkg CAD/GIS Importer & Converter"

    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.icon_dir = os.path.join(self.plugin_dir, "icons")
        if not os.path.exists(self.icon_dir):
            os.makedirs(self.icon_dir)

        self.actions: list[QAction] = []
        self.menu: QMenu | None = None
        self.toolbar: QToolBar | None = None
        self._dock = None

    # ───────────────────────── QGIS lifecycle ─────────────────────────

    def initGui(self) -> None:
        # Find or create PlanX main menu
        menu_bar = self.iface.mainWindow().menuBar()
        self.menu = None
        for action in menu_bar.actions():
            if action.text() == self.MENU_NAME:
                self.menu = action.menu()
                break

        if self.menu is None:
            self.menu = QMenu(self.MENU_NAME, self.iface.mainWindow())
            menu_bar.addMenu(self.menu)

        self.toolbar = QToolBar(self.TOOLBAR_NAME)
        self.toolbar.setObjectName("Zero2GpkgConverterToolbar")
        self.iface.addToolBar(self.toolbar)

        icon_path = os.path.join(self.icon_dir, "icon.png")
        if not os.path.exists(icon_path):
            icon_path = os.path.join(self.plugin_dir, "icon.png")

        self.panel_action = self._add_action(
            icon_path,
            "02gpkg - CAD & GIS Converter",
            self._toggle_dock,
            checkable=True,
            status_tip="Toggle 02gpkg CAD and GIS Converter panel",
        )

    def unload(self) -> None:
        if self._dock:
            self.iface.removeDockWidget(self._dock)
            self._dock.deleteLater()
            self._dock = None

        for action in self.actions:
            if self.menu:
                self.menu.removeAction(action)
            if self.toolbar:
                self.toolbar.removeAction(action)

        if self.toolbar:
            self.iface.mainWindow().removeToolBar(self.toolbar)
            self.toolbar.deleteLater()
            self.toolbar = None

    # ───────────────────────── Dock widget ─────────────────────────

    def _toggle_dock(self) -> None:
        created = False
        if self._dock is None:
            try:
                from .dialogs.dock import Zero2GpkgConverterDockWidget

                self._dock = Zero2GpkgConverterDockWidget(
                    self.iface, self.icon_dir, self.iface.mainWindow())
                self._dock.setObjectName("Zero2GpkgConverterDock")
                self._dock.visibilityChanged.connect(
                    self.panel_action.setChecked)
                self.iface.addDockWidget(
                    Qt.DockWidgetArea.RightDockWidgetArea, self._dock)
                created = True
            except Exception as exc:
                QMessageBox.critical(
                    self.iface.mainWindow(),
                    "Error",
                    f"Could not create dock widget:\n{exc}")
                self.panel_action.setChecked(False)
                return

        if created or not self._dock.isVisible():
            self._dock.setVisible(True)
            self.panel_action.setChecked(True)
            self._dock.raise_()
        else:
            self._dock.setVisible(False)
            self.panel_action.setChecked(False)

    # ───────────────────────── Helpers ─────────────────────────

    def _add_action(
            self,
            icon_path,
            text,
            callback,
            *,
            add_to_toolbar=True,
            add_to_menu=True,
            checkable=False,
            status_tip=None) -> QAction:
        icon = QIcon(icon_path) if os.path.exists(icon_path) else QIcon()
        action = QAction(icon, text, self.iface.mainWindow())
        action.triggered.connect(callback)
        action.setCheckable(checkable)
        if status_tip:
            action.setStatusTip(status_tip)
        if add_to_toolbar and self.toolbar:
            self.toolbar.addAction(action)
        if add_to_menu and self.menu:
            self.menu.addAction(action)
        self.actions.append(action)
        return action
