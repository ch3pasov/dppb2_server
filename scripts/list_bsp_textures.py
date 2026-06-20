#!/usr/bin/env python3
"""
List unique texture names from a Quake II IBSP v38 map (LUMP_TEXINFO .texture fields).
Used by docker-compose map init to fetch external assets without hardcoding per-map lists.
"""
from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path

# id qfiles.h
IBSP_MAGIC = 0x50534249  # little-endian "IBSP"
BSP_VERSION = 38
HEADER_LUMPS = 19
HEADER_SIZE = 8 + HEADER_LUMPS * 8
LUMP_TEXINFO = 5
TEXINFO_SIZE = 76
# texinfo_t: vecs[2][4] float (32) + flags (4) + value (4) + texture[32]
TEXTURE_FIELD_OFFSET = 40


def list_textures(path: Path) -> list[str]:
    data = path.read_bytes()
    if len(data) < HEADER_SIZE:
        raise ValueError("file too small for BSP header")

    ident, version = struct.unpack_from("<ii", data, 0)
    if ident != IBSP_MAGIC:
        raise ValueError(f"not an IBSP file (magic {ident:#010x})")
    if version != BSP_VERSION:
        raise ValueError(f"unsupported BSP version {version} (expected {BSP_VERSION})")

    lump_off = 8 + LUMP_TEXINFO * 8
    ofs, length = struct.unpack_from("<ii", data, lump_off)
    if ofs < 0 or length < 0 or ofs + length > len(data):
        raise ValueError("invalid texinfo lump bounds")

    chunk = data[ofs : ofs + length]
    seen: set[str] = set()
    out: list[str] = []
    for i in range(0, len(chunk), TEXINFO_SIZE):
        row = chunk[i : i + TEXINFO_SIZE]
        if len(row) < TEXINFO_SIZE:
            break
        raw = row[TEXTURE_FIELD_OFFSET : TEXTURE_FIELD_OFFSET + 32]
        name = raw.split(b"\0", 1)[0].decode("latin1", "replace").strip()
        if not name or name in seen:
            continue
        seen.add(name)
        out.append(name)
    out.sort()
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Print texture paths from a Q2 IBSP map (one per line).")
    ap.add_argument("bsp", type=Path, help="Path to .bsp file")
    args = ap.parse_args()
    try:
        for name in list_textures(args.bsp):
            print(name)
    except (OSError, ValueError) as e:
        print(f"list_bsp_textures: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
