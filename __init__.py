# -*- coding: utf-8 -*-
"""zero2gpkg_converter plugin factory.
100% English.
"""

def classFactory(iface):
    from .main_plugin import Zero2GpkgConverter
    return Zero2GpkgConverter(iface)
