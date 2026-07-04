# -*- coding: utf-8 -*-
"""zero2cadgis plugin factory.
100% English.
"""


def classFactory(iface):
    from .main_plugin import Zero2CadGis
    return Zero2CadGis(iface)
