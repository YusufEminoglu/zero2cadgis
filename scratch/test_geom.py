import sys
from qgis.core import QgsGeometry, QgsPoint, QgsLineString, QgsWkbTypes

pt1 = QgsPoint(10.0, 20.0, 30.0)
pt2 = QgsPoint(40.0, 50.0, 60.0)
line3d = QgsGeometry(QgsLineString([pt1, pt2]))
print("Original WKT:", line3d.asWkt(), "hasZ:", QgsWkbTypes.hasZ(line3d.wkbType()))

g = QgsGeometry(line3d)
if g.get():
    g.get().dropZValue()
print("After dropZ WKT:", g.asWkt(), "hasZ:", QgsWkbTypes.hasZ(g.wkbType()))
