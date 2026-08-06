import sys
from qgis.core import QgsVectorLayer, QgsFeature, QgsGeometry, QgsPointXY, QgsFields, QgsWkbTypes

poly_single = QgsGeometry.fromPolygonXY([[QgsPointXY(0,0), QgsPointXY(1,0), QgsPointXY(1,1), QgsPointXY(0,1), QgsPointXY(0,0)]])
print("Before convertToMultiType wkbType:", poly_single.wkbType(), "isMultiType:", QgsWkbTypes.isMultiType(poly_single.wkbType()))

g = QgsGeometry(poly_single)
g.convertToMultiType()
print("After convertToMultiType wkbType:", g.wkbType(), "isMultiType:", QgsWkbTypes.isMultiType(g.wkbType()))
