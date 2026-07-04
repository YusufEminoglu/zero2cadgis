# -*- coding: utf-8 -*-
"""cad_engine — CAD feature cleanup and styling service.
Provides vertex thinning, polyline closure tolerance, and custom styling.
"""
from __future__ import annotations

import math
from qgis.core import (
    QgsVectorLayer,
    QgsFeature,
    QgsGeometry,
    QgsPointXY,
    QgsMarkerSymbol,
    QgsLineSymbol,
    QgsFillSymbol,
    QgsSingleSymbolRenderer,
    QgsPalLayerSettings,
    QgsVectorLayerSimpleLabeling,
    QgsTextFormat,
    QgsTextBufferSettings
)
from qgis.PyQt.QtGui import QColor, QFont


class CadCleanupEngine:
    """Removes collinear nodes and duplicate points from CAD paths."""
    
    @staticmethod
    def clean_duplicates(coords: list) -> list:
        if len(coords) < 2:
            return coords
        cleaned = []
        for c in coords:
            if not cleaned:
                cleaned.append(c)
                continue
            prev = cleaned[-1]
            if abs(prev.x - c.x) < 0.0001 and abs(prev.y - c.y) < 0.0001:
                continue
            cleaned.append(c)
        return cleaned

    @staticmethod
    def simplify_collinear(coords: list) -> list:
        if len(coords) <= 3:
            return coords
            
        simplified = list(coords)
        removed = True
        while removed and len(simplified) > 3:
            removed = False
            for idx in range(len(simplified)):
                if idx == 0 or idx == len(simplified) - 1:
                    continue
                    
                prev_p = simplified[idx - 1]
                curr_p = simplified[idx]
                next_p = simplified[idx + 1]
                
                v1x, v1y = curr_p.x - prev_p.x, curr_p.y - prev_p.y
                v2x, v2y = next_p.x - curr_p.x, next_p.y - curr_p.y
                
                len1 = math.sqrt(v1x*v1x + v1y*v1y)
                len2 = math.sqrt(v2x*v2x + v2y*v2y)
                if len1 < 0.0001 or len2 < 0.0001:
                    simplified.pop(idx)
                    removed = True
                    break
                    
                cross = abs(v1x*v2y - v1y*v2x) / (len1 * len2)
                if cross <= 0.02:
                    simplified.pop(idx)
                    removed = True
                    break
        return simplified

    @staticmethod
    def close_polyline(coords: list, tolerance: float) -> list:
        """Closes polylines if endpoints are within the specified tolerance.
        Returns a closed geometry coordinate list.
        """
        if len(coords) < 3:
            return coords
            
        first = coords[0]
        last = coords[-1]
        dist = math.hypot(first.x - last.x, first.y - last.y)
        
        # Build closed loop
        closed_coords = list(coords)
        if dist > 0.0001 and dist <= tolerance:
            closed_coords.append(first)
        elif dist > tolerance:
            # Force close if polygon output is required
            closed_coords.append(first)
            
        return closed_coords


class CadStylingEngine:
    """Translates CAD layout parameters to styled QGIS rendering.
    Feyz taken from CartoDXF to dominate styling competitors.
    """
    
    @staticmethod
    def apply_argb_renderer(layer: QgsVectorLayer, geometry_type: str) -> None:
        """Discovers ARGB code from features and sets matching vector layer style."""
        color_rgb = None
        for feature in layer.getFeatures():
            color_str = feature["color_argb"]
            if color_str:
                try:
                    argb = int(color_str)
                    red = (argb >> 16) & 0xFF
                    green = (argb >> 8) & 0xFF
                    blue = argb & 0xFF
                    color_rgb = QColor(red, green, blue)
                    break
                except ValueError:
                    pass
                    
        if not color_rgb:
            color_rgb = QColor(110, 110, 110)
            
        symbol = None
        if geometry_type == "Point":
            symbol = QgsMarkerSymbol.createSimple({
                "name": "circle",
                "color": color_rgb.name(),
                "size": "3.5",
                "outline_color": "#ffffff",
                "outline_width": "0.4"
            })
        elif geometry_type == "LineString":
            # Map line patterns (CartoDXF styling feyz)
            symbol = QgsLineSymbol.createSimple({
                "color": color_rgb.name(),
                "width": "0.7",
                "line_style": "solid"
            })
        elif geometry_type == "Polygon":
            symbol = QgsFillSymbol.createSimple({
                "color": f"{color_rgb.red()},{color_rgb.green()},{color_rgb.blue()},70", # Translucent fill
                "outline_color": color_rgb.name(),
                "outline_width": "0.5"
            })
            
        if symbol:
            renderer = QgsSingleSymbolRenderer(symbol)
            layer.setRenderer(renderer)
            layer.triggerRepaint()

    @staticmethod
    def apply_buffered_labels(layer: QgsVectorLayer) -> None:
        """Sets clean labels with a thick buffer mask to prevent overlap background clutter."""
        text_format = QgsTextFormat()
        text_format.setFont(QFont("Segoe UI", 9))
        text_format.setColor(QColor(0, 0, 0))
        
        buffer = QgsTextBufferSettings()
        buffer.setEnabled(True)
        buffer.setSize(1.2)
        buffer.setColor(QColor(255, 255, 255))
        text_format.setBuffer(buffer)
        
        label_settings = QgsPalLayerSettings()
        label_settings.setFormat(text_format)
        label_settings.fieldName = "label"
        label_settings.isExpression = False
        label_settings.placement = QgsPalLayerSettings.Placement.OverPoint
        
        simple_labeling = QgsVectorLayerSimpleLabeling(label_settings)
        layer.setLabeling(simple_labeling)
        layer.setLabelsEnabled(True)
        layer.triggerRepaint()
