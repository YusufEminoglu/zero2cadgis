# -*- coding: utf-8 -*-
"""02CadGis Processing algorithms.

The same engines as the dock, without the dock: so a conversion, a Netcad
import or a plan check can sit in a model, run as a batch over many files,
or be called from a script (``processing.run("zero2cadgis:...", {...})``).

Copyright (C) 2026 Yusuf Eminoğlu
SPDX-License-Identifier: GPL-2.0-or-later
"""
from __future__ import annotations

import os
import re

from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsFeature,
    QgsFeatureSink,
    QgsGeometry,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterCrs,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFile,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterMultipleLayers,
    QgsProcessingParameterNumber,
    QgsProcessingParameterVectorLayer,
    QgsProcessingOutputNumber,
    QgsProject,
    QgsVectorFileWriter,
    QgsVectorLayer,
    QgsWkbTypes,
)

CLIP_MODES = (("none", "Import every feature"),
              ("keep_whole", "Keep whole features that touch the boundary"),
              ("exact_clip", "Crop features at the boundary"))


def _boundary(algorithm, parameters, context):
    """(geometry, crs) of the optional BOUNDARY source, or (None, None)."""
    source = algorithm.parameterAsSource(parameters, "BOUNDARY", context)
    if source is None:
        return None, None
    geometries = [f.geometry() for f in source.getFeatures()
                  if f.hasGeometry() and not f.geometry().isEmpty()]
    if not geometries:
        raise QgsProcessingException("The boundary layer holds no polygon.")
    return QgsGeometry.unaryUnion(geometries), source.sourceCrs()


def _add_boundary_parameters(algorithm) -> None:
    algorithm.addParameter(QgsProcessingParameterFeatureSource(
        "BOUNDARY", "Spatial boundary",
        [QgsProcessing.SourceType.TypeVectorPolygon], optional=True))
    algorithm.addParameter(QgsProcessingParameterEnum(
        "CLIP_MODE", "Features and the boundary",
        options=[label for _key, label in CLIP_MODES], defaultValue=1))


def _clip_mode(algorithm, parameters, context, boundary) -> str:
    if boundary is None:
        return "none"
    return CLIP_MODES[algorithm.parameterAsEnum(parameters, "CLIP_MODE", context)][0]


def _load_on_completion(context, path: str, layer_names: list, group: str) -> None:
    """Have Processing add the written GeoPackage layers to the project."""
    for name in layer_names:
        layer = QgsVectorLayer(f"{path}|layername={name}", name, "ogr")
        if not layer.isValid():
            continue
        context.temporaryLayerStore().addMapLayer(layer)
        details = QgsProcessingContext.LayerDetails(name, context.project(), "OUTPUT")
        details.groupName = group
        context.addLayerToLoadOnCompletion(layer.id(), details)


class _Base(QgsProcessingAlgorithm):
    def group(self) -> str:
        return ""

    def groupId(self) -> str:
        return ""

    def createInstance(self):
        return type(self)()


class ConvertDatasetAlgorithm(_Base):
    """CAD / GIS dataset -> GeoPackage, through the converter engine."""

    def name(self) -> str:
        return "convertdataset"

    def displayName(self) -> str:
        return "Convert CAD / GIS dataset to GeoPackage"

    def shortHelpString(self) -> str:
        return (
            "Converts a DXF, DWG, DGN, KML/KMZ, GML, GeoJSON, CSV, SpatiaLite, GPX, "
            "File Geodatabase or MS Access dataset into one GeoPackage, as the "
            "02CadGis converter does. A CAD drawing can be split into one layer per "
            "CAD layer (DXF) or level (DGN); its points, lines and polygons always go "
            "to separate GeoPackage layers. A File Geodatabase is a folder: pick any "
            "file inside the .gdb folder.\n\n"
            "With a spatial boundary, either only the features that touch it are "
            "kept, unchanged, or features are cropped at it.")

    def initAlgorithm(self, config=None) -> None:
        self.addParameter(QgsProcessingParameterFile(
            "INPUT", "Source dataset", behavior=QgsProcessingParameterFile.Behavior.File))
        self.addParameter(QgsProcessingParameterBoolean(
            "SPLIT_CAD_LAYERS", "Split a CAD drawing by CAD layer / level", defaultValue=True))
        self.addParameter(QgsProcessingParameterCrs(
            "SOURCE_CRS", "Source CRS (when the dataset declares none)", optional=True))
        self.addParameter(QgsProcessingParameterCrs(
            "TARGET_CRS", "Target CRS", defaultValue="ProjectCrs"))
        _add_boundary_parameters(self)
        self.addParameter(QgsProcessingParameterFileDestination(
            "OUTPUT", "GeoPackage", fileFilter="GeoPackage (*.gpkg)"))
        self.addOutput(QgsProcessingOutputNumber("LAYER_COUNT", "Layers written"))
        self.addOutput(QgsProcessingOutputNumber("FEATURE_COUNT", "Features written"))

    def processAlgorithm(self, parameters, context, feedback):
        from ..core.gis_engine import GisConverterEngine

        source = self.parameterAsFile(parameters, "INPUT", context)
        parent = os.path.dirname(source)
        if parent.lower().endswith(".gdb"):
            source = parent
        if not os.path.exists(source):
            raise QgsProcessingException(f"Source dataset not found: {source}")
        target_crs = self.parameterAsCrs(parameters, "TARGET_CRS", context)
        source_crs = self.parameterAsCrs(parameters, "SOURCE_CRS", context)
        output = self.parameterAsFileOutput(parameters, "OUTPUT", context)
        boundary, boundary_crs = _boundary(self, parameters, context)
        engine = GisConverterEngine(
            source, output, target_crs,
            source_crs=source_crs if source_crs.isValid() else None,
            clip_geometry=boundary,
            clip_mode=_clip_mode(self, parameters, context, boundary),
            clip_crs=boundary_crs)
        if self.parameterAsBoolean(parameters, "SPLIT_CAD_LAYERS", context) and engine.is_cad_source:
            _infos, field = engine.discover_cad_layers(is_kmz=False)
            engine.cad_split_field = field or ""
        is_kmz = source.lower().endswith(".kmz")
        try:
            layers = engine.convert(
                is_kmz=is_kmz,
                progress_cb=lambda name: feedback.pushInfo(f"Writing {name}"))
        except ValueError as exc:
            raise QgsProcessingException(str(exc)) from exc
        for note in engine.last_warnings:
            feedback.pushWarning(note)
        names = [layer.name() for layer in layers]
        stored = [layer.source().split("layername=")[-1] for layer in layers]
        features = sum(layer.featureCount() for layer in layers)
        group = os.path.splitext(os.path.basename(output))[0]
        _load_on_completion(context, output, stored, group)
        feedback.pushInfo(f"{len(names)} layer(s), {features:,} feature(s) written to {output}")
        return {"OUTPUT": output, "LAYER_COUNT": len(names), "FEATURE_COUNT": features}


class ImportNetcadAlgorithm(_Base):
    """Netcad NCZ -> GeoPackage, one layer per tabaka and geometry."""

    FAMILY_TOKEN = {"POINT/TEXT": "POINT", "LINE": "LINE", "POLYGON": "POLYGON"}

    def name(self) -> str:
        return "importnetcad"

    def displayName(self) -> str:
        return "Import Netcad NCZ drawing to GeoPackage"

    def shortHelpString(self) -> str:
        return (
            "Decodes a Netcad NCZ / NCA drawing with 02CadGis's own decoder and writes "
            "one GeoPackage layer per tabaka and geometry (points and texts, lines, "
            "polygons), with the CAD columns of the dock import: tabaka, colour, "
            "text, text height, rotation, pen width.\n\n"
            "The CRS is read from the drawing's projection text and coordinates when "
            "the Source CRS is left empty; a drawing whose CRS cannot be worked out "
            "is refused rather than guessed. The plan-mode steps (MPYY structure, "
            "zoning values, plan notation) stay in the dock.")

    def initAlgorithm(self, config=None) -> None:
        self.addParameter(QgsProcessingParameterFile(
            "INPUT", "Netcad drawing", behavior=QgsProcessingParameterFile.Behavior.File,
            fileFilter="Netcad drawing (*.ncz *.nca *.NCZ *.NCA)"))
        self.addParameter(QgsProcessingParameterCrs(
            "SOURCE_CRS", "Drawing CRS (empty: detect)", optional=True))
        self.addParameter(QgsProcessingParameterNumber(
            "CLOSE_TOLERANCE", "Close rings left open by up to (map units)",
            QgsProcessingParameterNumber.Type.Double, defaultValue=0.10, minValue=0.0))
        _add_boundary_parameters(self)
        self.addParameter(QgsProcessingParameterFileDestination(
            "OUTPUT", "GeoPackage", fileFilter="GeoPackage (*.gpkg)"))
        self.addOutput(QgsProcessingOutputNumber("LAYER_COUNT", "Layers written"))
        self.addOutput(QgsProcessingOutputNumber("FEATURE_COUNT", "Features written"))
        self.addOutput(QgsProcessingOutputNumber("SKIPPED_COUNT", "Records left out"))

    @staticmethod
    def _layer_name(tabaka: str, family_suffix: str) -> str:
        text = re.sub(r"\W+", "_", str(tabaka).strip(), flags=re.UNICODE).strip("_").upper() or "LAYER"
        return f"{text}_{ImportNetcadAlgorithm.FAMILY_TOKEN.get(family_suffix, family_suffix)}"

    def processAlgorithm(self, parameters, context, feedback):
        from ..core import ncz_layers
        from ..core.crs_detect import detect_crs
        from ..core.export_utils import atomic_output
        from ..core.netcad_parser import NetcadLazyReader

        path = self.parameterAsFile(parameters, "INPUT", context)
        if not os.path.isfile(path):
            raise QgsProcessingException(f"Netcad drawing not found: {path}")
        output = self.parameterAsFileOutput(parameters, "OUTPUT", context)
        reader = NetcadLazyReader(path).index()

        crs = self.parameterAsCrs(parameters, "SOURCE_CRS", context)
        if not crs.isValid():
            detection = detect_crs(reader.projection_text, reader.sample_coordinates())
            if not detection.epsg:
                raise QgsProcessingException(
                    f"The drawing's CRS could not be worked out ({detection.reason}). "
                    "Set the Drawing CRS.")
            crs = QgsCoordinateReferenceSystem(detection.authid)
            feedback.pushInfo(f"CRS: {detection.authid} — {detection.reason}")

        boundary, boundary_crs = _boundary(self, parameters, context)
        clip_mode = _clip_mode(self, parameters, context, boundary)
        if boundary is not None and boundary_crs is not None and boundary_crs.isValid() \
                and boundary_crs != crs:
            boundary.transform(QgsCoordinateTransform(boundary_crs, crs, QgsProject.instance()))

        codes = {summary.layer_code for summary in reader.layer_summaries()}
        entities = reader.decode_layers(codes)
        skipped = (sum(reader.last_unsupported.values())
                   + sum(reader.last_unreadable.values()))
        note = reader.skipped_summary()
        if note:
            feedback.pushWarning(note)

        buckets: dict = {}
        for entity in entities:
            suffix, geometry_type = ncz_layers.geometry_family(
                entity.geometry_kind, entity.is_closed, entity.coordinates)
            if not suffix:
                continue
            tabaka = entity.layer_name or f"LAYER_{entity.layer_code}"
            buckets.setdefault((self._layer_name(tabaka, suffix), geometry_type), []).append(entity)

        source_name = os.path.splitext(os.path.basename(path))[0]
        tolerance = self.parameterAsDouble(parameters, "CLOSE_TOLERANCE", context)
        written, features = [], 0
        transform_context = context.transformContext()
        with atomic_output(output) as working:
            for index, ((name, geometry_type), members) in enumerate(sorted(buckets.items())):
                if feedback.isCanceled():
                    break
                feedback.setProgress(100.0 * index / max(len(buckets), 1))
                layer = ncz_layers.build_entity_layer(
                    name, geometry_type, members, crs, source_name,
                    clip_boundary=boundary, clip_mode=clip_mode,
                    close_tolerance=tolerance)
                if layer is None or layer.featureCount() == 0:
                    continue
                options = QgsVectorFileWriter.SaveVectorOptions()
                options.driverName = "GPKG"
                options.layerName = name
                options.actionOnExistingFile = (
                    QgsVectorFileWriter.ActionOnExistingFile.CreateOrOverwriteLayer if written
                    else QgsVectorFileWriter.ActionOnExistingFile.CreateOrOverwriteFile)
                error, message, _path, _layer = QgsVectorFileWriter.writeAsVectorFormatV3(
                    layer, working, transform_context, options)
                if error != QgsVectorFileWriter.WriterError.NoError:
                    raise QgsProcessingException(f"Writing {name} failed: {message}")
                written.append(name)
                features += layer.featureCount()
            if not written:
                raise QgsProcessingException(
                    "No feature of the drawing falls inside the spatial boundary."
                    if boundary is not None else "The drawing holds no decodable geometry.")
        _load_on_completion(context, output, written, source_name)
        feedback.pushInfo(f"{len(written)} layer(s), {features:,} feature(s) written to {output}")
        return {"OUTPUT": output, "LAYER_COUNT": len(written), "FEATURE_COUNT": features,
                "SKIPPED_COUNT": skipped}


class CheckPlanConsistencyAlgorithm(_Base):
    """core/plan_check over any plan-area layers."""

    def name(self) -> str:
        return "checkplan"

    def displayName(self) -> str:
        return "Check plan consistency"

    def shortHelpString(self) -> str:
        return (
            "Reports what a plan says that does not add up, without changing it: "
            "KAKS above TAKS × floors or below TAKS; values outside their physical "
            "range; land-use (PL_) areas that overlap or are stored twice; building "
            "notation outside every plan area or disagreeing inside one.\n\n"
            "Plan areas: polygon layers with the MPYY fields Taks, EmsalKaks, "
            "KatAdedi. A layer with a tabaka field (layer_name, uip_tabaka or Layer), "
            "as 02CadGis imports it, is read by tabaka; a layer without one counts "
            "as plan areas throughout. Notation (optional): a point layer with the "
            "same fields, such as 02CadGis's Building notation layer. All layers in "
            "one projected CRS.")

    def initAlgorithm(self, config=None) -> None:
        self.addParameter(QgsProcessingParameterMultipleLayers(
            "AREAS", "Plan areas", QgsProcessing.SourceType.TypeVectorPolygon))
        self.addParameter(QgsProcessingParameterVectorLayer(
            "NOTATION", "Building notation", [QgsProcessing.SourceType.TypeVectorPoint],
            optional=True))
        self.addParameter(QgsProcessingParameterNumber(
            "OVERLAP_MIN_AREA", "Overlaps count from (m²)",
            QgsProcessingParameterNumber.Type.Double, defaultValue=1.0, minValue=0.0))
        self.addParameter(QgsProcessingParameterFeatureSink(
            "OUTPUT", "Plan check", QgsProcessing.SourceType.TypeVectorPoint))
        self.addParameter(QgsProcessingParameterFeatureSink(
            "OVERLAPS", "Plan check overlaps", QgsProcessing.SourceType.TypeVectorPolygon,
            optional=True))
        for name, label in (("FINDING_COUNT", "Findings"), ("ERROR_COUNT", "Errors"),
                            ("WARNING_COUNT", "Warnings")):
            self.addOutput(QgsProcessingOutputNumber(name, label))

    def processAlgorithm(self, parameters, context, feedback):
        from ..core.plan_check import (
            check_plan, finding_area, finding_attributes, finding_fields, finding_point)
        from ..core.plan_notation import NotationPoint

        areas = self.parameterAsLayerList(parameters, "AREAS", context)
        if not areas:
            raise QgsProcessingException("Choose at least one plan-area layer.")
        crs = areas[0].crs()
        if crs.isGeographic():
            raise QgsProcessingException("Areas are measured in map units: use a projected CRS.")
        notation_layer = self.parameterAsVectorLayer(parameters, "NOTATION", context)
        for layer in areas + ([notation_layer] if notation_layer else []):
            if layer.crs() != crs:
                raise QgsProcessingException(
                    f"'{layer.name()}' is in {layer.crs().authid()}, the plan areas in "
                    f"{crs.authid()}: reproject it first.")

        points = []
        if notation_layer is not None:
            names = notation_layer.fields().names()
            wanted = [n for n in ("YapiDuzeni", "KatAdedi", "Taks", "EmsalKaks", "YapiYuksekligi",
                                  "OnBahceMesafesi", "YanBahceMesafesi") if n in names]
            for feature in notation_layer.getFeatures():
                if not feature.hasGeometry():
                    continue
                values = {n: feature[n] for n in wanted
                          if feature[n] is not None and str(feature[n]) not in ("", "NULL")}
                point = feature.geometry().asPoint()
                points.append(NotationPoint(point.x(), point.y(), values))

        result = check_plan(
            areas, points,
            overlap_min_area=self.parameterAsDouble(parameters, "OVERLAP_MIN_AREA", context))
        feedback.pushInfo(result.summary())

        fields = finding_fields()
        sink, destination = self.parameterAsSink(
            parameters, "OUTPUT", context, fields, QgsWkbTypes.Type.Point, crs)
        if sink is None:
            raise QgsProcessingException("The Plan check output could not be created.")
        overlap_sink, overlap_destination = self.parameterAsSink(
            parameters, "OVERLAPS", context, fields, QgsWkbTypes.Type.MultiPolygon, crs)
        for finding in result.findings:
            attributes = finding_attributes(finding)
            feature = QgsFeature(fields)
            feature.setAttributes(attributes)
            feature.setGeometry(finding_point(finding))
            sink.addFeature(feature, QgsFeatureSink.Flag.FastInsert)
            area = finding_area(finding)
            if area is not None and overlap_sink is not None:
                polygon = QgsFeature(fields)
                polygon.setAttributes(attributes)
                polygon.setGeometry(area)
                overlap_sink.addFeature(polygon, QgsFeatureSink.Flag.FastInsert)

        counts = result.by_severity()
        outputs = {"OUTPUT": destination, "FINDING_COUNT": len(result.findings),
                   "ERROR_COUNT": counts["error"], "WARNING_COUNT": counts["warning"]}
        if overlap_sink is not None:
            outputs["OVERLAPS"] = overlap_destination
        return outputs
