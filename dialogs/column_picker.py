# -*- coding: utf-8 -*-
"""Pick the attribute columns an import or conversion writes.

A tool button whose drop-down lists every column with a check box; the list
stays open while boxes are ticked. Columns another step needs (the tabaka the
styles and MPYY read, the text the labels show) are listed ticked and locked,
with the reason as their tooltip, so they cannot be dropped by accident.

Copyright (C) 2026 Yusuf Eminoğlu
SPDX-License-Identifier: GPL-2.0-or-later
"""
from __future__ import annotations

from typing import Iterable, Optional

from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtWidgets import (
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QWidgetAction,
)


class ColumnPicker(QToolButton):
    """Drop-down check list of column names. ``selected()`` is None when all are kept."""

    changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        menu = QMenu(self)
        holder = QWidget(menu)
        layout = QVBoxLayout(holder)
        layout.setContentsMargins(4, 4, 4, 4)
        self.list = QListWidget(holder)
        self.list.setMinimumWidth(240)
        self.list.setMinimumHeight(220)
        layout.addWidget(self.list)
        buttons = QHBoxLayout()
        self.btn_all = QPushButton("All", holder)
        self.btn_none = QPushButton("Only required", holder)
        self.btn_all.clicked.connect(lambda: self._set_all(True))
        self.btn_none.clicked.connect(lambda: self._set_all(False))
        buttons.addWidget(self.btn_all)
        buttons.addWidget(self.btn_none)
        layout.addLayout(buttons)
        action = QWidgetAction(menu)
        action.setDefaultWidget(holder)
        menu.addAction(action)
        self.setMenu(menu)
        self.list.itemChanged.connect(lambda _item: self._update_text())
        self._locked: dict = {}
        self._update_text()

    def set_columns(self, names: Iterable[str], locked: Optional[dict] = None) -> None:
        """Offer ``names``; ``locked`` maps a name to why it cannot be dropped.

        Columns offered before keep their tick, so a refreshed source or a
        second drawing does not undo the choice.
        """
        previous = {self.list.item(i).text(): self.list.item(i).checkState()
                    for i in range(self.list.count())}
        self._locked = dict(locked or {})
        self.list.blockSignals(True)
        self.list.clear()
        for name in names:
            item = QListWidgetItem(str(name), self.list)
            if name in self._locked:
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsUserCheckable & ~Qt.ItemFlag.ItemIsEnabled)
                item.setCheckState(Qt.CheckState.Checked)
                item.setToolTip("Required: " + self._locked[name])
            else:
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(previous.get(name, Qt.CheckState.Checked))
        self.list.blockSignals(False)
        self._update_text()

    def columns(self) -> list:
        return [self.list.item(i).text() for i in range(self.list.count())]

    def selected(self) -> Optional[set]:
        """Names to keep, or None when every offered column is kept (nothing to drop)."""
        kept = {self.list.item(i).text() for i in range(self.list.count())
                if self.list.item(i).checkState() == Qt.CheckState.Checked}
        if len(kept) == self.list.count():
            return None
        return kept

    def dropped(self) -> set:
        """Offered names the user unticked (locked ones never are)."""
        return {self.list.item(i).text() for i in range(self.list.count())
                if self.list.item(i).checkState() != Qt.CheckState.Checked}

    def set_checked(self, name: str, checked: bool) -> None:
        for i in range(self.list.count()):
            item = self.list.item(i)
            if item.text() == name and name not in self._locked:
                item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)

    def _set_all(self, checked: bool) -> None:
        for i in range(self.list.count()):
            self.set_checked(self.list.item(i).text(), checked)

    def _update_text(self) -> None:
        total = self.list.count()
        if total == 0:
            self.setText("Columns: all")
            self.setEnabled(False)
        else:
            kept = total if self.selected() is None else len(self.selected())
            self.setText(f"Columns: {kept} / {total}")
            self.setEnabled(True)
        self.changed.emit()
