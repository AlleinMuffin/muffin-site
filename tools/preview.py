#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Debug helper: dump a scene grid to PNG so the artwork can be eyeballed."""
import os
import struct
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib

ga = importlib.import_module("gen-art")


def write_png(grid, path, scale=2):
    w, h = ga.W * scale, ga.H * scale
    raw = bytearray()
    for py in range(h):
        raw.append(0)
        row = grid[py // scale]
        for px in range(w):
            r, g, b = row[px // scale]
            raw.extend((int(round(r)), int(round(g)), int(round(b))))

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(png)


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools", "preview")
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    scenes = {
        "city": ga.scene_city(7),
        "mountains": ga.scene_mountains(11),
        "cave": ga.scene_cave(23),
        "fortress": ga.scene_fortress(31),
        "beacon": ga.scene_beacon(41),
        "fields": ga.scene_fields(53),
    }
    for name, grid in scenes.items():
        if which not in ("all", name):
            continue
        p = os.path.join(out, "%s.png" % name)
        write_png(grid, p, 2)
        print(p)
