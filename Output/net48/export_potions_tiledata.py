# -*- coding: utf-8 -*-
"""Legge tiledata.mul (formato >= 7.0.90) e scrive un TXT con le voci il cui nome contiene 'potion'."""
from __future__ import annotations

import struct
import sys
from pathlib import Path

LAND_GROUPS = 512
TILES_PER_GROUP = 32
NAME_LEN = 20
STATIC_TILE_BYTES = 8 + 1 + 1 + 4 + 2 + 2 + 2 + 1 + NAME_LEN  # 41


def parse_static_tile(buf: bytes) -> dict:
    o = 0
    flags = struct.unpack_from("<Q", buf, o)[0]
    o += 8
    weight, layer = struct.unpack_from("<BB", buf, o)
    o += 2
    count = struct.unpack_from("<i", buf, o)[0]
    o += 4
    anim_id, hue, light_index = struct.unpack_from("<HHH", buf, o)
    o += 6
    height = buf[o]
    o += 1
    raw = buf[o : o + NAME_LEN]
    name = raw.split(b"\x00", 1)[0].decode("utf-8", errors="replace").strip()
    return {
        "flags": flags,
        "weight": weight,
        "layer": layer,
        "count": count,
        "anim_id": anim_id,
        "hue": hue,
        "light_index": light_index,
        "height": height,
        "name": name,
    }


def main():
    uo_root = Path(r"c:\Users\MennE\Desktop\UOAlive 7.0.113.00")
    tiledata = uo_root / "tiledata.mul"
    out_path = uo_root / "potion_items_tiledata.txt"

    if len(sys.argv) >= 2:
        tiledata = Path(sys.argv[1])
    if len(sys.argv) >= 3:
        out_path = Path(sys.argv[2])

    if not tiledata.is_file():
        print(f"Manca il file: {tiledata}", file=sys.stderr)
        sys.exit(1)

    data = tiledata.read_bytes()
    pos = 0

    for _ in range(LAND_GROUPS):
        pos += 4
        pos += TILES_PER_GROUP * (8 + 2 + NAME_LEN)

    matches: list[tuple[int, dict]] = []
    static_index = 0

    while pos + 4 <= len(data):
        pos += 4
        for _j in range(TILES_PER_GROUP):
            end = pos + STATIC_TILE_BYTES
            if end > len(data):
                break
            tile = parse_static_tile(data[pos:end])
            pos = end
            n = tile["name"]
            if n and "potion" in n.lower():
                matches.append((static_index, tile))
            static_index += 1

    lines = [
        f"# Generato da tiledata: {tiledata}",
        f"# Voci con 'potion' nel nome (case-insensitive): {len(matches)}",
        "# Formato: GraphicDec\tGraphicHex\tNome",
        "",
    ]
    for idx, t in matches:
        lines.append(f"{idx}\t0x{idx:04X}\t{t['name']}")

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Scritto {out_path} ({len(matches)} righe dati)")


if __name__ == "__main__":
    main()
