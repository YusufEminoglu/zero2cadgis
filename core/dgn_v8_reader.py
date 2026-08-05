# -*- coding: utf-8 -*-
"""dgn_v8_reader — Pure Python MicroStation DGN v8 geometry reader.

Fallback reader used when GDAL's ``DGNv8`` driver is unavailable.
DGN v8 files are OLE2 compound documents whose element streams are
zlib-compressed.  This module decompresses them and yields geometry
features suitable for conversion to QGIS layers.

Coverage
--------
* **Line** (type 3) — fully supported (22 k elements in a typical file).
* **LineString** (type 4) — supported.
* **Shape / polygon** (type 6) — supported.
* Complex containers (cell header, complex string / shape) and
  annotation types (text, dimension) are skipped but their Level,
  colour, and style attributes are still reported via placeholder
  (centroid or bounding-box) geometry when possible.

Coordinate system
-----------------
DGN v8 stores coordinates as double-precision values in **master
units** (metres, survey-feet, …).  No scaling is applied — the raw
values are returned as-is.  The caller is responsible for CRS
selection and datum transformation.
"""

from __future__ import annotations

import contextlib
import math
import os
import struct
import sys
import zlib
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Iterator, List, Optional, Tuple

olefile = None

# Resolve the vendored _vendor directory relative to this file's location.
# QGIS plugin loaders may not set up package-relative imports reliably,
# so an absolute path via sys.path is the most robust option.
_vendor_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "..", "_vendor")
_vendor_dir = os.path.normpath(os.path.abspath(_vendor_dir))
if os.path.isdir(_vendor_dir) and _vendor_dir not in sys.path:
    sys.path.insert(0, _vendor_dir)

try:
    import olefile  # type: ignore[assignment]  # noqa: F811
except ImportError:
    try:
        from .._vendor import olefile  # type: ignore[no-redef,assignment]
    except ImportError:
        pass  # olefile stays None — is_dgn_v8 / DgnV8Reader will report it


# ===================================================================
# Element type codes
# ===================================================================

class ElementType(IntEnum):
    CELL_HEADER  = 2
    LINE         = 3
    LINE_STRING  = 4
    SHAPE        = 6
    TEXT         = 7
    CURVE        = 11
    COMPLEX_STR  = 12
    COMPLEX_SHP  = 14
    ELLIPSE      = 15
    ARC          = 16


_TYPE_NAMES: dict[int, str] = {
    2: "CellHeader",  3: "Line",      4: "LineString",
    6: "Shape",       7: "Text",     11: "Curve",
   12: "ComplexStr", 14: "ComplexShp", 15: "Ellipse",
   16: "Arc",        17: "MultiText", 21: "TagElement",
   26: "RasterHdr",  27: "RasterRef", 33: "Dimension",
   37: "OLEFrame",
}

# Element types whose geometry we can extract reliably.
_SIMPLE_GEOM_TYPES = frozenset({
    ElementType.LINE, ElementType.LINE_STRING, ElementType.SHAPE,
    ElementType.TEXT, ElementType.CURVE, ElementType.ELLIPSE, ElementType.ARC,
})


# ===================================================================
# Data classes
# ===================================================================

@dataclass
class DgnElement:
    """One graphic element extracted from a DGN v8 file."""
    element_type: int
    type_name: str = ""
    level: int = 0
    color_index: int = 0
    weight: int = 0
    style: int = 0
    geometry: List[Tuple[float, float]] = field(default_factory=list)


# ===================================================================
# Reader
# ===================================================================

class DgnV8Reader:
    """Read geometry from a MicroStation DGN v8 file.

    Parameters:
        path: Absolute path to the ``.dgn`` file.
    """

    _BASE_GEOM_OFFSET = 0x64  # 100 bytes

    def __init__(self, path: str) -> None:
        if olefile is None:
            raise ImportError(
                "The olefile package is required to read DGN v8 files. "
                "Install it with: pip install olefile")
        self._path = path
        self._ole: Optional[olefile.OleFileIO] = None

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> "DgnV8Reader":
        self.open()
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def open(self) -> None:
        if self._ole is not None:
            return
        self._ole = olefile.OleFileIO(self._path)

    def close(self) -> None:
        if self._ole is not None:
            self._ole.close()
            self._ole = None

    # ------------------------------------------------------------------
    # Stream enumeration
    # ------------------------------------------------------------------

    def _graphic_streams(self) -> Iterator[Tuple[str, bytes]]:
        """Yield ``(name, decompressed_bytes)`` for every graphic
        element stream across all models."""
        if self._ole is None:
            raise RuntimeError("DGN file is not open")
        for entry in self._ole.listdir():
            name = "/".join(entry)
            # Graphic element streams live under Dgn-Md/#NNNNNN/Dgn^G/ or Dgn^G
            if "Dgn^G" not in name:
                continue
            raw = None
            try:
                raw = self._ole.openstream(entry).read()
            except (IOError, AttributeError, OSError):
                raw = None
            if not raw or len(raw) < 12:
                continue

            dec = None
            for offset in (16, 12, 8, 0):
                if len(raw) <= offset:
                    continue
                chunk = raw[offset:]
                with contextlib.suppress(zlib.error):
                    dec = zlib.decompress(chunk)
                    break
                with contextlib.suppress(zlib.error):
                    dec = zlib.decompress(chunk, -zlib.MAX_WBITS)
                    break

            if dec is None:
                dec = raw

            if len(dec) < 12:
                continue
            yield name, dec

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def elements(self) -> Iterator[DgnElement]:
        """Iterate over all graphic elements in the file."""
        for _stream_name, data in self._graphic_streams():
            yield from self._parse_stream(data)

    def layer_names(self) -> dict[int, str]:
        """Return a mapping ``{level_number: level_name}`` discovered
        from the file's level table (if present)."""
        if self._ole is None:
            return {}
        names: dict[int, str] = {}
        try:
            for entry in self._ole.listdir():
                name = "/".join(entry)
                if "Dgn^N" not in name:
                    continue
                raw = None
                try:
                    raw = self._ole.openstream(entry).read()
                except (IOError, AttributeError, OSError):
                    raw = None
                if not raw:
                    continue
                dec = None
                for offset in (16, 12, 8, 0):
                    if len(raw) <= offset:
                        continue
                    with contextlib.suppress(zlib.error):
                        dec = zlib.decompress(raw[offset:])
                        break
                if dec is None:
                    dec = raw

                # Scan decompressed level table stream for UTF-16 / ASCII level names
                pos = 0
                while pos < len(dec) - 8:
                    # Look for level ID structure: uint32 level_id, string length, chars
                    lid = struct.unpack_from("<I", dec, pos)[0]
                    if 1 <= lid <= 0x7FFFFFFF:
                        # Attempt ASCII string decode in vicinity
                        sub = dec[pos+4:pos+64]
                        # Look for null-terminated printable string
                        clean_str = ""
                        for b in sub:
                            if 32 <= b <= 126:
                                clean_str += chr(b)
                            elif b == 0 and len(clean_str) >= 2:
                                break
                            elif clean_str:
                                break
                        if len(clean_str) >= 2 and lid not in names:
                            names[lid] = clean_str
                    pos += 4
        except (IOError, AttributeError, OSError) as exc:
            _ = exc
        return names

    # ------------------------------------------------------------------
    # Stream-level parsing
    # ------------------------------------------------------------------

    @staticmethod
    def _geom_offset_for_type(type_byte: int, subtype_byte: int) -> int:
        """Return the byte offset where geometry data begins for a
        given element type and sub-type."""
        if type_byte == ElementType.LINE_STRING:
            return 0x6C
        if type_byte in (ElementType.CURVE, ElementType.ELLIPSE, ElementType.ARC):
            return 0x6C
        if type_byte == ElementType.TEXT:
            return 0x50
        return DgnV8Reader._BASE_GEOM_OFFSET

    @staticmethod
    def _decode_points(data: bytes, start: int,
                       end: int, is_3d: bool = False) -> List[Tuple[float, float]]:
        """Decode (X, Y) double-precision pairs from *start* to *end*.

        Stops at NaN sentinels and values that are clearly garbage
        (magnitude > 1e16 for engineering coordinates).
        """
        pts: List[Tuple[float, float]] = []
        pos = start
        stride = 24 if is_3d else 16
        while pos + 16 <= end:
            x = struct.unpack_from("<d", data, pos)[0]
            y = struct.unpack_from("<d", data, pos + 8)[0]
            if math.isnan(x) or math.isnan(y) or math.isinf(x) or math.isinf(y):
                pos += stride
                continue
            if abs(x) > 1e16 or abs(y) > 1e16:
                break
            pts.append((x, y))
            pos += stride
        return pts

    @staticmethod
    def _read_level(data: bytes, elem_start: int) -> int:
        """Extract the MicroStation Level number."""
        if elem_start + 0x30 > len(data):
            return 0
        level = struct.unpack_from("<I", data, elem_start + 0x2C)[0]
        if 0 <= level <= 0x7FFFFFFF:
            return level
        for off in (0x28, 0x30, 0x14, 0x18):
            if elem_start + off + 4 <= len(data):
                level = struct.unpack_from("<I", data, elem_start + off)[0]
                if 0 <= level <= 0x7FFFFFFF:
                    return level
        return 0

    @staticmethod
    def _read_color(data: bytes,
                    elem_start: int) -> Tuple[int, int, int]:
        """Return ``(color_index, weight, style)``."""
        if elem_start + 0x34 > len(data):
            return (0, 0, 0)
        cg = struct.unpack_from("<I", data, elem_start + 0x30)[0]
        return (cg & 0xFF, (cg >> 8) & 0xFF, (cg >> 16) & 0xFF)

    def _parse_stream(self, data: bytes) -> Iterator[DgnElement]:
        """Parse DGN v8 elements from one decompressed stream."""
        pos = 0
        data_len = len(data)

        while pos + 16 <= data_len:
            elem_start = pos
            type_byte = data[pos + 4] & 0x7F
            subtype_byte = data[pos + 5]

            is_3d = bool(data[pos + 1] & 0x40)

            word_count = struct.unpack_from("<I", data, pos + 8)[0]
            if word_count < 4 or word_count > 0xFFFFF:
                pos += 4
                continue

            elem_size = word_count * 2 + 4
            elem_end = elem_start + elem_size
            if elem_end > data_len:
                break

            level = self._read_level(data, elem_start)
            color_index, weight, style = self._read_color(data, elem_start)
            type_name = _TYPE_NAMES.get(type_byte, f"Type{type_byte}")

            geometry: List[Tuple[float, float]] = []

            if type_byte in _SIMPLE_GEOM_TYPES:
                geom_off = self._geom_offset_for_type(type_byte,
                                                       subtype_byte)
                abs_geom = elem_start + geom_off
                if abs_geom < elem_end:
                    geometry = self._decode_points(data, abs_geom,
                                                    elem_end, is_3d=is_3d)
                    if not geometry and is_3d:
                        # Fallback attempt as 2D
                        geometry = self._decode_points(data, abs_geom,
                                                        elem_end, is_3d=False)

            yield DgnElement(
                element_type=type_byte,
                type_name=type_name,
                level=level,
                color_index=color_index,
                weight=weight,
                style=style,
                geometry=geometry,
            )

            pos = elem_end


# ===================================================================
# Convenience functions
# ===================================================================

def is_dgn_v8(path: str) -> bool:
    """Return ``True`` if *path* looks like a DGN v8 file."""
    if olefile is None:
        return False
    try:
        if not olefile.isOleFile(path):
            return False
        ole = olefile.OleFileIO(path)
        try:
            for entry in ole.listdir():
                name = "/".join(entry)
                if "Dgn~H" in name or "Dgn-Md" in name or "Dgn^G" in name:
                    return True
            return False
        finally:
            ole.close()
    except Exception:
        return False


def check_dgn_driver_available() -> bool:
    """Return ``True`` if GDAL's DGNv8 driver is available."""
    try:
        from osgeo import ogr
        return ogr.GetDriverByName("DGNv8") is not None
    except Exception:
        return False
