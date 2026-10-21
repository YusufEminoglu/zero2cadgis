# -*- coding: utf-8 -*-
"""Processing provider registration.

Copyright (C) 2026 Yusuf Eminoğlu
SPDX-License-Identifier: GPL-2.0-or-later
"""
from __future__ import annotations

import os

from qgis.core import QgsProcessingProvider
from qgis.PyQt.QtGui import QIcon

from .algorithms import (
    CheckPlanConsistencyAlgorithm,
    ConvertDatasetAlgorithm,
    ImportNetcadAlgorithm,
)


class Zero2CadGisProvider(QgsProcessingProvider):
    PROVIDER_ID = "zero2cadgis"
    PROVIDER_NAME = "02CadGis"

    def id(self) -> str:
        return self.PROVIDER_ID

    def name(self) -> str:
        return self.PROVIDER_NAME

    def longName(self) -> str:
        return "02CadGis Universal CAD/GIS Importer"

    def icon(self) -> QIcon:
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "icons", "icon.png")
        return QIcon(icon_path) if os.path.exists(icon_path) else super().icon()

    def loadAlgorithms(self) -> None:
        self.addAlgorithm(ConvertDatasetAlgorithm())
        self.addAlgorithm(ImportNetcadAlgorithm())
        self.addAlgorithm(CheckPlanConsistencyAlgorithm())
