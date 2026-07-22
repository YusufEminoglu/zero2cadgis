# NCZ Binary Format Notes (02CadGis)

Facts about the Netcad `.ncz` / compatible `.nca` container as understood by
02CadGis. This document records *format knowledge* (offsets, codes, layouts)
so that engine implementations can be written and reviewed against a single
reference. It contains no code.

## Container

The file is a flat sequence of variable-length blocks with no global header.

```
offset 0: u8   block kind
offset 1: u32  stored length L (little endian)
offset 5: payload (L bytes)
```

A block therefore occupies `L + 5` bytes. Readers advance block-by-block;
when a declared block would run past the end of the file (or `L + 4 < 4`),
the reader advances one byte and tries to resynchronize.

## Block kinds

| Kind | Meaning |
| ---: | --- |
| 6  | Layer table |
| 21 | Geometry record (plain layout) |
| 22 | Geometry record (GIS layout: geometry fields shifted +28 bytes) |
| 25 | Producer version string (length-prefixed, Netcad OEM codepage) |
| 28 | Named metadata block (`MPROJ`, `TILED_XML`, `LEX.ST2`, ...) |
| 0, 5, 14, 48, 108, 111, 132, 150, 180 | Containers that may embed nested 21/22 geometry records |

Embedded geometry records inside a container are found by scanning the
container payload for a byte 21/22 whose bytes at +5 and +6 are equal
(length-prefix echo), with a valid inner length.

## Strings

Text uses an OEM byte mapping for Turkish characters:
`221→I, 222→S, 208→G, 240→g, 253→i, 254→s`; all other bytes map through
Latin-1 ordinals. Strings are usually length-prefixed (1 length byte, then
the bytes) and NUL-padded.

## Layer table (kind 6)

- `u16` layer count at block offset 16.
- Items of 29 bytes each starting at block offset 18.
- Item: name length at +4, name bytes at +5.

## Named metadata (kind 28)

Payload starts with a length-prefixed block name at offsets 5/6.

- **MPROJ** — projection code `u8` at block offset 16
  (1 Geographic, 2 UTM 6-degree, 3 UTM 3-degree), datum `u8` at 17
  (0 WGS-84, 1 ITRF, 4 ED50, 254 ED50-HGK), zone `u8` at 21.
- **TILED_XML** — contains an XML fragment with `SRS:"EPSG:xxxx"`; the EPSG
  string runs from after `SRS` to the next `>` byte (62).
- **LEX.ST2** — layer colour table: count `u8` at block offset 20; 256-byte
  items from offset 23; RGB bytes at item offset +56.

## Geometry record layout

Offsets are relative to the block start. `G` is the GIS shift: 0 for kind
21, 28 for kind 22.

Common fields:

| Offset | Field |
| ---: | --- |
| 6 | geometry type `u8` |
| 7 | layer code `u8` |
| 8, 16 | first coordinate pair, two `f64` (stored northing-first: the QGIS X is the *second* stored value) |
| 24 | `f32` elevation (some records store it at 28 instead) |
| 37 | colour code `u8` (0 = by layer, 1 = blue, 255 = red, other = undefined) |

Geometry types:

| Type | Kind | Extra fields |
| ---: | --- | --- |
| 1 | Point | name length/bytes at `G+86` / `G+87` |
| 2 | Line | second vertex at block end: `f64` pair at `size-19`/`size-11`, `f32` z at `size-3` |
| 3 | Circle | radius = half the absolute difference of the `f64`s at 50 and 66 |
| 4 | Arc | radius `f64` at `G+86`, start/end angles `f64` at `G+104` / `G+112` (radians) |
| 5 | Text | payload length/text at `G+97`/`G+98` (fallback `G+86`/`G+87`, then unshifted); height `f32` at `G+86` (fallback 86); rotation `f32` radians at `G+90` |
| 6 | Symbol | symbol code `u8` at `G+94`; size `f32` at `G+86` (default 5.0); rotation `f32` at `G+90` |
| 7 | Polyline/Polygon | label length/text at `G+86`/`G+87`; vertices of 3×`f64` (24 bytes) from `G+113`; count = `(size + 1 − 113 − G) / 24` |
| 9 | Compressed curve | origin `f64` pair at 8/16; delta records of 18 bytes from `G+122`, each starting with two `f32` deltas |
| 10 | Box | corner 2 `f64` pair at `G+104`/`G+112`; rotation `f32` radians at `G+120` |
| 11 | Map sheet | corners: `f64`s at 50/58 and 66/74; sheet name is the first printable length-prefixed string from 86 |
| 12 | Triangle | vertex A at 8/16 (+z f32 at 24), B at 86/94, C at 106/114 |
| 13 | Block reference | insertion at 8/16; name length-prefixed from `G+86`; rotation `f32` radians at `G+118` |
| 15 | Smart object | width/height/grid-x/grid-y `f64` at 169/177/185/193 (fallback corner pair at 66/74); angle `f32` in grads at 82; scale `f32` at 86; label ASCII token from 145 or literal `BASIC` |

Coordinates are accepted only when finite and with magnitude ≤ 1e8.

## Attribute tables (`@TAB`)

Attribute rows are located by scanning the whole file for the ASCII marker
`@TAB` followed by decimal digits (the table reference). If the byte before
the marker equals the reference length, the record starts there. A record
extends to the next marker (or end of file). Rows come in three variants:

- **label** — a printable length-prefixed label at offset 28/29, followed by
  style/flag bytes and up to three `f64` coordinate pairs;
- **segment** — records ≥ 119 bytes whose `f64` pairs at 17/25, 45/53,
  87/95, 103/111 look like projected coordinates (|v| in [1e3, 1e8]);
- **ascii** — anything else; all printable length-prefixed ASCII fields are
  collected.

## Producer quirks

- When a drawing contains at least one smart object, `S0` symbols on layer 0
  are producer artifacts and are dropped.
- Layer codes may be 1-based relative to the layer table; a failed direct
  lookup retries with `code − 1`.
- A layer colour of nearly pure black-blue (`R=0, G=0, B≤1`) is normalized
  to pure black.
