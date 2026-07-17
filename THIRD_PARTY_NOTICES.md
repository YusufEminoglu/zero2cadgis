# Third-Party Notices

This file records third-party source code incorporated into 02CadGis. The
02CadGis plugin as a whole is distributed under GPL-2.0-or-later; see
`LICENSE` for the complete license text.

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
