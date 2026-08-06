import sys
from qgis.core import QgsVectorLayer, QgsFeature, QgsGeometry, QgsPointXY, QgsWkbTypes

def coerce_poly(geom, target_type):
    gt = geom.type()
    is_poly_geom = (gt == QgsWkbTypes.GeometryType.PolygonGeometry)
    g_out = geom if is_poly_geom else None
    if g_out and not g_out.isEmpty():
        if target_type == "MultiPolygon" and not QgsWkbTypes.isMultiType(g_out.wkbType()):
            g_copy = QgsGeometry(g_out)
            g_copy.convertToMultiType()
            return g_copy
        elif target_type == "Polygon" and QgsWkbTypes.isMultiType(g_out.wkbType()):
            g_copy = QgsGeometry(g_out)
            g_copy.convertToSingleType()
            return g_copy
    return g_out

mem_layer = QgsVectorLayer("MultiPolygon?crs=EPSG:4326", "Level 0_MultiPolygon", "memory")
prov = mem_layer.dataProvider()

poly_single = QgsGeometry.fromPolygonXY([[QgsPointXY(0,0), QgsPointXY(1,0), QgsPointXY(1,1), QgsPointXY(0,1), QgsPointXY(0,0)]])
coerced_geom = coerce_poly(poly_single, "MultiPolygon")

feat = QgsFeature()
feat.setGeometry(coerced_geom)

result = prov.addFeatures([feat])
print("Result for coerced Polygon in MultiPolygon layer:", result)
print("Layer feature count:", mem_layer.featureCount())
