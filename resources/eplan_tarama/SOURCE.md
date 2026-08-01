# Source of these files

These 131 tarama (hatch pattern) tiles are **not** original 02CadGis artwork.
They are redistributed **byte for byte, unmodified**, under their original file
names, from the plan gösterimleri SLD style set published on the e-Plan portal
of the **T.C. Çevre, Şehircilik ve İklim Değişikliği Bakanlığı — Coğrafi Bilgi
Sistemleri Genel Müdürlüğü**: <https://eplan.csb.gov.tr/>

They carry the official planning symbology defined in **Ek-2 of the Mekânsal
Planlar Yapım Yönetmeliği**, so that an imar plan imported from CAD is drawn the
way the regulation requires.

Two things worth knowing before touching them:

- Despite the `.png` extension, 119 of the 131 files are **BMP** bytes — that is
  how the Ministry ships them. Qt detects the format from content, so they are
  left exactly as published rather than being re-encoded.
- The file names are the Ministry's own UUIDs and are referenced by
  `core/eplan_catalog.py`. Renaming one breaks the catalog; regenerate with
  `tools/compile_eplan_catalog.py` instead.

Copyright and the basis for redistribution are recorded in
[`THIRD_PARTY_NOTICES.md`](../../THIRD_PARTY_NOTICES.md).
