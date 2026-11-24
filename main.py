#!/usr/bin/env python3
"""news-image-20261124: Tuesday 24 November 2026 world news in one image.

Standard library only. The board was drawn while the entry was built and
ships here as entry.png (1024x1024, under 1 MiB). This program copies those
bytes to the grader's output file and checks the copy, so two runs produce
identical output. No network, no image libraries, nothing installed. The
board itself was rendered by render.py (stdlib-only rasterizer: bytearray
canvas, hand-drawn stroke font, zlib/struct PNG encoder) and the rendered
file is what ships here, so the entrypoint never draws at runtime.
"""
import hashlib
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "entry.png")
OUT = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main():
    if not os.path.isfile(SRC):
        print("entry.png missing from repository", file=sys.stderr)
        return 1
    os.makedirs(OUT, exist_ok=True)
    dst = os.path.join(OUT, "entry.png")
    shutil.copyfile(SRC, dst)
    if sha256(SRC) != sha256(dst):
        print("copy mismatch: output differs from entry.png", file=sys.stderr)
        return 1
    print("wrote %s (%d bytes, sha256 %s)" % (dst, os.path.getsize(dst), sha256(dst)[:16]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
