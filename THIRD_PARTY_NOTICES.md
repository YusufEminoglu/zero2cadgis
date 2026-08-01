# Third-Party Notices

This file records third-party source code and third-party material
incorporated into 02CadGis. The 02CadGis plugin as a whole is distributed
under GPL-2.0-or-later; see `LICENSE` for the complete license text.

## e-Plan Plan Gösterimleri (official planning symbology)

`core/eplan_catalog.py` and the 131 tarama (hatch pattern) tiles under
`resources/eplan_tarama/` reproduce the **official Turkish planning
symbology**, so that an imar plan imported from CAD is drawn the way the
regulation requires.

- Source: the e-Plan portal of the **T.C. Çevre, Şehircilik ve İklim
  Değişikliği Bakanlığı — Coğrafi Bilgi Sistemleri Genel Müdürlüğü**,
  <https://eplan.csb.gov.tr/>, from its published GeoServer SLD style set.
- Standard: the plan gösterimleri are **Ek-2 of the Mekânsal Planlar Yapım
  Yönetmeliği**. They are a mandated legend: a plan that does not reproduce
  them exactly is not a valid plan.

What is reproduced:

- The tarama tiles are redistributed **byte for byte, unmodified**, under
  their original file names.
- The gösterim values in `core/eplan_catalog.py` — fill colors, stroke colors
  and widths, dash arrays, and the official rule names — are extracted
  mechanically from the published SLD files by
  `tools/compile_eplan_catalog.py`.

What is **not** included:

- The symbol fonts the SLD set references for point symbolizers
  (`uygulama_imar_*`, `OG_V_*`, `UIP_*`, `Intelli Eplan`,
  `ESRI Default Marker`, `Calibri`). **No font file is redistributed**, and
  the point symbolizers that depend on them are not implemented.

Copyright:

- The underlying gösterim — the colors, patterns and legend of the official
  standard — is the Ministry's and is **not claimed** as original work here.
  As legislative and official material it falls under FSEK Art. 31; as of
  2026-08-01 the portal publishes no separate terms-of-use or licence
  statement alongside the style set.
- The compiler, the CAD tabaka to official rule mapping, the plan-type
  resolution, and the translation into native QGIS symbol layers are:
  Copyright (C) 2026 Yusuf Eminoğlu.

02CadGis is an independent project and is not endorsed by, affiliated with,
or produced in cooperation with the Ministry or any of its directorates.

## MPYY UİP Tabaka Catalog (official planning codes)

`core/mpyy_catalog.py` reproduces the **official UİP tabaka catalog**: for each
tabaka, its upper group and code and its function and code, so that the
PlanGML schema columns of an imported plan carry the Ministry's own values.

- Source: the **Mekânsal Planlar Yapım Yönetmeliği UİP database** published by
  the **T.C. Çevre, Şehircilik ve İklim Değişikliği Bakanlığı** (a GeoPackage,
  e.g. `MpyyUipDb_2026_02_27.gpkg`), tables `uipPolygonTable` and
  `uipLineTable`.
- Standard: the same Mekânsal Planlar Yapım Yönetmeliği as the plan
  gösterimleri above. The codes are the ones a plan is validated against.

What is reproduced: the tabaka names, upper group names and codes, and
function names and codes — 256 tabaka across 25 upper groups — extracted by
`tools/compile_mpyy_catalog.py`. No geometry and no drawing data from the
database is included.

Copyright: the catalog is the Ministry's and is **not claimed** as original
work here, on the same basis as the plan gösterimleri above. The compiler, the
`MPYY_ALIASES` list mapping local tabaka spellings onto official ones, and the
lookup in `core/plangml_schema.py` are Copyright (C) 2026 Yusuf Eminoğlu.

## Jeomatik NCZ Reader

The NCZ decoding implementation in `core/netcad_parser.py` and its result
model in `core/ncz_engine/model.py`, together with NCZ-specific
layer-building and geometry-conversion portions of `dialogs/dock.py`,
incorporates and is derived from **Jeomatik NCZ Reader**.

- Copyright (C) 2026 Erdinç Örsan ÜNAL
- Upstream source: <https://github.com/erdincunal/Jeomatik-NCZ-Reader>
- Project page: <https://jeomatik.com/ncz-reader.html>
- Upstream license: GNU General Public License v2.0 or later
  (`GPL-2.0-or-later`)

The derived code was adapted and extended for 02CadGis beginning on
2026-07-04. Those modifications and the surrounding 02CadGis integration are:

- Copyright (C) 2026 Yusuf Eminoğlu

02CadGis versions 0.1.0 through 0.2.3 contained the derived NCZ
implementation. This notice documents that historical lineage and restores
the upstream copyright, source, and license information beginning with
02CadGis 0.2.4.

The Jeomatik name, logo, and associated trademarks are not used under the
GPL and remain the property of their respective owner. 02CadGis is an
independent project and is not endorsed by or affiliated with Jeomatik.
