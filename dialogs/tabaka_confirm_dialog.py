# -*- coding: utf-8 -*-
"""Confirm proposed tabaka -> MPYY mappings before a plan import.

Only names the matcher could not resolve by itself reach this table, each with
its ranked proposals (synonym first, then spelling similarity). Every row starts
**unticked**: a proposal is applied only when a planner ticks it. Ticked rows are
stored per user by ``tabaka_matching.confirm`` and resolve on their own in every
later import, in 02CadGis and in MPYY Studio alike.

Copyright (C) 2026 Yusuf Eminoğlu
SPDX-License-Identifier: GPL-2.0-or-later
"""
from __future__ import annotations

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
)

LEVEL_TITLES = {"UIP": "UİP", "NIP": "NİP", "CDP": "ÇDP"}


def describe(suggestion) -> str:
    entry = suggestion.entry
    attrs = ", ".join(f"{k}={v}" for k, v in entry.get("attrs", {}).items())
    return f"{suggestion.key}  →  {entry['feature']}" + (f" ({attrs})" if attrs else "")


class TabakaConfirmDialog(QDialog):
    """rows: [(tabaka, feature_count, [Suggestion, ...]), ...]"""

    def __init__(self, level: str, rows, parent=None):
        super().__init__(parent)
        self.level = level
        self.rows = list(rows)
        self.setWindowTitle(f"MPYY {LEVEL_TITLES.get(level, level)} — tabaka eşleştirme önerileri")
        self.resize(980, 520)
        layout = QVBoxLayout(self)
        info = QLabel(
            "Bu tabakalar tam adla, daha önce onayladığın bir eşleştirmeyle ya da anlamı "
            "değiştirmeyen bir yazım kuralıyla bulunamadı. Aşağıdakiler yalnızca öneridir: "
            "işaretlediğin satırlar MPYY türüne aktarılır ve sonraki dosyalar için hatırlanır; "
            "işaretlemediklerin çizimin kendi renkleriyle ayrı grupta kalır.")
        info.setWordWrap(True)
        layout.addWidget(info)

        self.table = QTableWidget(len(self.rows), 5, self)
        self.table.setHorizontalHeaderLabels(["Onayla", "Tabaka", "Nesne", "Önerilen MPYY karşılığı", "Gerekçe"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.checks: list[QCheckBox] = []
        self.combos: list[QComboBox] = []
        for row, (tabaka, count, suggestions) in enumerate(self.rows):
            box = QCheckBox()
            box.setChecked(False)
            holder = QWidget()
            holder_layout = QHBoxLayout(holder)
            holder_layout.setContentsMargins(0, 0, 0, 0)
            holder_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            holder_layout.addWidget(box)
            self.table.setCellWidget(row, 0, holder)
            self.checks.append(box)
            name = QTableWidgetItem(str(tabaka))
            name.setFlags(name.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 1, name)
            number = QTableWidgetItem(str(count))
            number.setFlags(number.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 2, number)
            combo = QComboBox()
            for suggestion in suggestions:
                combo.addItem(f"{describe(suggestion)}   [{suggestion.score:.2f}]", suggestion.key)
            self.table.setCellWidget(row, 3, combo)
            self.combos.append(combo)
            reason = QTableWidgetItem(suggestions[0].reason if suggestions else "")
            reason.setFlags(reason.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 4, reason)
            combo.currentIndexChanged.connect(
                lambda index, r=row, s=suggestions: self.table.item(r, 4).setText(s[index].reason if 0 <= index < len(s) else ""))
        layout.addWidget(self.table)

        buttons = QDialogButtonBox(self)
        self.btn_apply = buttons.addButton("İşaretlileri onayla ve aktar", QDialogButtonBox.ButtonRole.AcceptRole)
        self.btn_skip = buttons.addButton("Onaylamadan aktar", QDialogButtonBox.ButtonRole.RejectRole)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def selections(self) -> list[tuple[str, str]]:
        """(tabaka, crosswalk key) for every ticked row."""
        chosen = []
        for (tabaka, _count, _suggestions), box, combo in zip(self.rows, self.checks, self.combos):
            if box.isChecked() and combo.currentData():
                chosen.append((str(tabaka), str(combo.currentData())))
        return chosen
