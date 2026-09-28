# `mpyy/` — third-party and source notices

This folder is MPYY Studio's MPYY UİP / NİP / ÇDP styling pipeline, copied
unchanged into 02CadGis by `tools/sync_mpyy_styles.py` so the plugin runs on
its own. `SYNC_MANIFEST.json` lists every file with its sha256. The code
(`core/`) and the compiled tables (`styles/*.json`: MPYY 1.1.7 schema, CAD
tabaka → MPYY type crosswalk, detail-catalog decisions, renderer hierarchy) are
Copyright (C) 2026 Yusuf Eminoğlu, GPL-2.0-or-later.

## Ministry e-Plan SLD styles — `styles/mpyy_sld/{UIP,NIP,CDP}`

One SLD per MPYY feature type, from the plan gösterimleri SLD style set
published on the e-Plan portal of the T.C. Çevre, Şehircilik ve İklim
Değişikliği Bakanlığı — Coğrafi Bilgi Sistemleri Genel Müdürlüğü
(<https://eplan.csb.gov.tr/>), with their filters rewritten to the MPYY 1.1.7
schema fields. The gösterim is the Ministry's and is not claimed as original
work. No Ministry endorsement or statutory compliance is claimed.

## Tarama tiles and annex artwork — `resources/`

- `resources/*.png`: the tarama (hatch) tiles the SLDs above reference,
  byte for byte as the Ministry publishes them (most are BMP bytes under a
  `.png` name). Only referenced tiles are copied.
- `resources/katalog_sembol/*.png`: point symbols cut from **Ek-1e Mekânsal
  Planlar Detay Katalogları** (annex to the Mekânsal Planlar Yapım
  Yönetmeliği), replacing symbols the Ministry SLDs take from unpublished SVGs
  or unshipped fonts.

No redistribution term has been established for these images; this notice
records what the package contains and does not assert a right to redistribute it.

## Embedded SVGs — `styles/`

- `water.svg`: Font Awesome Free 6.7.2, Copyright 2024 Fonticons, Inc.,
  CC BY 4.0 (<https://creativecommons.org/licenses/by/4.0/>). Source:
  <https://github.com/FortAwesome/Font-Awesome/blob/6.x/svgs/solid/water.svg>
- `Cross4.svg`: from the QGIS SVG library (`svg/crosses/Cross4.svg`),
  GPL-2.0-or-later.

## Bundled fonts — `resources/fonts/`

131 TTF files in 58 families, registered in the QGIS process when a MPYY
import runs.

- 22 files in 4 families are DejaVu (DejaVu Sans, Sans Mono, Serif, Math TeX
  Gyre), redistributed under the DejaVu / Bitstream Vera licence, which
  permits it.
- The other **109 files in 54 families** are plan-notation and marker fonts:
  the UİP / NİP / ÇDP series and their M / ME variants, `OG_V_*`,
  `uygulama_imar_*`, `nazim_imar_*`, `yerlesim`, `cevre_duzeni_plani_*`,
  `mekansal_strateji_planlari_*`, `mulga_*`, and three named after unrelated
  third parties: `ESRI Default Marker`, `Intelli Eplan Extra`, `ISKI`.
  **No licence file, licence header or attribution record accompanies any of
  them, and no redistribution term has been established.** They are bundled by
  the author's decision (2026-09-28). This notice records what the package
  contains; it does not assert a right to redistribute them.
