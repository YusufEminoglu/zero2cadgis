# -*- coding: utf-8 -*-
"""Confirm proposed tabaka -> MPYY mappings before a plan import.

Only names the matcher could not resolve by itself reach this table. Each row
offers the matcher's ranked proposals first and, below them, every MPYY function
drawn with the layer's geometry, searchable by typing ("ARITMA", "sağlık").
Rows start **unticked**: a proposal is applied only when a planner ticks it, and
picking a function by hand ticks the row, since that is the planner's decision.
Tabaka without a proposal are listed too, hidden until asked for, so any of them
can still be given a function. Ticked rows are stored per user by
``tabaka_matching.confirm`` and resolve on their own in every later import, in
02CadGis and in MPYY Studio alike.

Copyright (C) 2026 Yusuf Eminoğlu
SPDX-License-Identifier: GPL-2.0-or-later
"""
from __future__ import annotations

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QCompleter,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

LEVEL_TITLES = {"UIP": "UİP", "NIP": "NİP", "CDP": "ÇDP"}
GEOMETRY_TITLES = {"polygon": "Alan", "line": "Çizgi", "point": "Nokta", "": ""}


def describe_entry(label: str, entry: dict) -> str:
    attrs = ", ".join(f"{k}={v}" for k, v in entry.get("attrs", {}).items())
    return f"{label}  →  {entry['feature']}" + (f" ({attrs})" if attrs else "")


def describe(suggestion) -> str:
    return describe_entry(getattr(suggestion, "label", "") or suggestion.key, suggestion.entry)


class TabakaConfirmDialog(QDialog):
    """rows: [(tabaka, feature_count, [Suggestion, ...]), ...]

    ``functions``: {key: Target} offered for a hand pick; ``geometries``:
    {tabaka: "polygon" | "line" | "point"} limits that list per row.
    """

    def __init__(self, level: str, rows, parent=None, functions=None, geometries=None):
        super().__init__(parent)
        self.level = level
        self.rows = list(rows)
        functions = functions or {}
        geometries = geometries or {}
        self.setWindowTitle(f"MPYY {LEVEL_TITLES.get(level, level)} — tabaka eşleştirme")
        self.resize(1080, 580)
        layout = QVBoxLayout(self)
        info = QLabel(
            "Bu tabakalar tam adla, daha önce onayladığın bir eşleştirmeyle ya da anlamı "
            "değiştirmeyen bir yazım kuralıyla bulunamadı. Listedekiler yalnızca öneridir; "
            "istersen kutuya yazarak başka bir MPYY fonksiyonu seçebilirsin (elle seçim satırı "
            "işaretler). İşaretlediğin satırlar MPYY türüne aktarılır ve sonraki dosyalar için "
            "hatırlanır; işaretlemediklerin çizimin kendi renkleriyle ayrı grupta kalır.")
        info.setWordWrap(True)
        layout.addWidget(info)

        self.table = QTableWidget(len(self.rows), 6, self)
        self.table.setHorizontalHeaderLabels(
            ["Onayla", "Tabaka", "Geometri", "Nesne", "MPYY karşılığı (yazarak ara)", "Gerekçe"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.checks: list[QCheckBox] = []
        self.combos: list[QComboBox] = []
        self._unproposed_rows: list[int] = []
        for row, (tabaka, count, suggestions) in enumerate(self.rows):
            geometry = geometries.get(tabaka, "")
            box = QCheckBox()
            box.setChecked(False)
            holder = QWidget()
            holder_layout = QHBoxLayout(holder)
            holder_layout.setContentsMargins(0, 0, 0, 0)
            holder_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            holder_layout.addWidget(box)
            self.table.setCellWidget(row, 0, holder)
            self.checks.append(box)
            for column, text in ((1, str(tabaka)), (2, GEOMETRY_TITLES.get(geometry, geometry)), (3, str(count))):
                item = QTableWidgetItem(text)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, column, item)
            reason = QTableWidgetItem(suggestions[0].reason if suggestions else "öneri yok — elle seç")
            reason.setFlags(reason.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 5, reason)
            combo = self._function_combo(suggestions, functions, geometry)
            self.table.setCellWidget(row, 4, combo)
            self.combos.append(combo)
            combo.currentIndexChanged.connect(
                lambda index, r=row, n=len(suggestions): self._picked(r, index, n))
            if not suggestions:
                self._unproposed_rows.append(row)
        layout.addWidget(self.table)

        self.chk_show_all = QCheckBox(f"Önerisi olmayan {len(self._unproposed_rows)} tabakayı da göster")
        self.chk_show_all.toggled.connect(self._show_unproposed)
        self.chk_show_all.setVisible(bool(self._unproposed_rows))
        layout.addWidget(self.chk_show_all)
        self._show_unproposed(False)

        buttons = QDialogButtonBox(self)
        self.btn_apply = buttons.addButton("İşaretlileri onayla ve aktar", QDialogButtonBox.ButtonRole.AcceptRole)
        self.btn_skip = buttons.addButton("Onaylamadan aktar", QDialogButtonBox.ButtonRole.RejectRole)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @staticmethod
    def _function_combo(suggestions, functions, geometry) -> QComboBox:
        combo = QComboBox()
        combo.setEditable(True)
        combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        if not suggestions:
            combo.addItem("— seçilmedi —", None)
        for suggestion in suggestions:
            combo.addItem(f"{describe(suggestion)}   [{suggestion.score:.2f}]", suggestion.key)
        proposed = {s.key for s in suggestions}
        others = sorted((t for k, t in functions.items()
                         if k not in proposed and (not geometry or not t.geometry or t.geometry == geometry)),
                        key=lambda t: t.label)
        if others:
            combo.insertSeparator(combo.count())
            for target in others:
                combo.addItem(describe_entry(target.label, target.entry), target.key)
        completer = QCompleter(combo.model(), combo)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        combo.setCompleter(completer)
        combo.setCurrentIndex(0)
        return combo

    def _picked(self, row: int, index: int, proposals: int) -> None:
        combo = self.combos[row]
        offset = 0 if proposals else 1          # the "— seçilmedi —" item
        if index >= proposals + offset and combo.itemData(index):
            self.checks[row].setChecked(True)   # a hand pick is the planner's own decision
            self.table.item(row, 5).setText("elle seçildi")
        elif 0 <= index < proposals:
            self.table.item(row, 5).setText(self.rows[row][2][index].reason)

    def _show_unproposed(self, shown: bool) -> None:
        for row in self._unproposed_rows:
            self.table.setRowHidden(row, not shown)

    def selections(self) -> list[tuple[str, str]]:
        """(tabaka, function key) for every ticked row."""
        chosen = []
        for (tabaka, _count, _suggestions), box, combo in zip(self.rows, self.checks, self.combos):
            if box.isChecked() and combo.currentData():
                chosen.append((str(tabaka), str(combo.currentData())))
        return chosen
