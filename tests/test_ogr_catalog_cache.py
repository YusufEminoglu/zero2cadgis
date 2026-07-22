# -*- coding: utf-8 -*-
"""Pure-Python tests for the OGR source-catalog cache.

The cache module has no QGIS/GDAL dependency, so these run without a QGIS
install. They cover the fingerprint (file and directory), the save/load
roundtrip, invalidation on change, the disable switch, and clearing.
"""
import os
import tempfile
import unittest
from pathlib import Path

from zero2cadgis.core import ogr_catalog_cache as cache


class TestOgrCatalogCache(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self._orig_root = cache._cache_root
        self._cache_dir = self.tmp / "_cache"
        cache._cache_root = lambda: self._cache_dir
        os.environ.pop(cache._DISABLE_ENV, None)

    def tearDown(self):
        cache._cache_root = self._orig_root
        os.environ.pop(cache._DISABLE_ENV, None)
        self._tmp.cleanup()

    def _make_file(self, name="src.gml", content=b"abc"):
        path = self.tmp / name
        path.write_bytes(content)
        return str(path)

    def _make_dir_dataset(self, name="src.gdb"):
        d = self.tmp / name
        d.mkdir()
        (d / "a.gdbtable").write_bytes(b"0000")
        (d / "b.gdbtable").write_bytes(b"1111")
        return str(d)

    def test_fingerprint_file(self):
        path = self._make_file()
        fp = cache.fingerprint(path)
        self.assertEqual(fp["kind"], "file")
        self.assertEqual(fp["size"], 3)
        self.assertIn("mtime_ns", fp)

    def test_fingerprint_dir_aggregates(self):
        path = self._make_dir_dataset()
        fp = cache.fingerprint(path)
        self.assertEqual(fp["kind"], "dir")
        self.assertEqual(fp["files"], 2)
        self.assertEqual(fp["size"], 8)

    def test_save_load_roundtrip(self):
        path = self._make_file()
        layers = [{"name": "L1", "geometry": "Point", "feature_count": 5}]
        cache.save(path, layers)
        loaded = cache.load(path)
        self.assertEqual(loaded, layers)

    def test_miss_when_absent(self):
        path = self._make_file()
        self.assertIsNone(cache.load(path))

    def test_invalidates_on_content_change(self):
        path = self._make_file(content=b"abc")
        cache.save(path, [{"name": "L", "geometry": "Point",
                           "feature_count": 1}])
        self.assertIsNotNone(cache.load(path))
        # Change size -> fingerprint mismatch -> miss.
        Path(path).write_bytes(b"abcd")
        self.assertIsNone(cache.load(path))

    def test_invalidates_on_version_bump(self):
        path = self._make_file()
        cache.save(path, [{"name": "L", "geometry": "Point",
                           "feature_count": 1}])
        original = cache.CACHE_VERSION
        try:
            cache.CACHE_VERSION = original + 99
            self.assertIsNone(cache.load(path))
        finally:
            cache.CACHE_VERSION = original

    def test_disable_env(self):
        path = self._make_file()
        cache.save(path, [{"name": "L", "geometry": "Point",
                           "feature_count": 1}])
        os.environ[cache._DISABLE_ENV] = "1"
        self.assertIsNone(cache.load(path))

    def test_clear(self):
        p1 = self._make_file("a.gml")
        p2 = self._make_file("b.gml")
        cache.save(p1, [{"name": "A", "geometry": "Point",
                         "feature_count": 1}])
        cache.save(p2, [{"name": "B", "geometry": "Point",
                         "feature_count": 1}])
        self.assertEqual(cache.clear(), 2)
        self.assertIsNone(cache.load(p1))


if __name__ == "__main__":
    unittest.main()
