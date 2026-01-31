#!/usr/bin/env python3
"""
Early test for iso extraction... doesn't work on BIN files yet. 

Extract every file from game.iso into ./extracted/.
Also writes a manifest.txt listing all paths and sizes (bytes).

DEPRECATED! Use dumpsxiso!
"""

import os
from pathlib import Path
import pycdlib

SRC_BIN   = "iso-extract-test/Metal Gear Solid (JPN) Disc 1.bin"
SRC_ISO   = "iso-extract-test/mgs-jpn-d1.iso"
OUT_DIR   = Path("iso-extract-test/extracted")
MANIFEST  = OUT_DIR / "iso-extract-test/manifest.txt"

def walk_iso(iso, dir_path="/"):
    """
    Recursively yield (path_on_disk, pycdlib_file_obj)
    for every file under dir_path.
    """
    entries = iso.list_children(dirpath=dir_path)
    for e in entries:
        name   = e.file_identifier().decode("utf-8").rstrip(";1")
        full_path = os.path.join(dir_path, name)
        if e.is_directory():
            yield from walk_iso(iso, full_path + "/")
        else:
            yield full_path, e

def bin_to_iso(bin_path, iso_path):
    with open(bin_path, "rb") as src, open(iso_path, "wb") as dst:
        while True:
            sector = src.read(2048)          # ISO9660 sector size
            if not sector:
                break
            dst.write(sector)

def main():
    iso = pycdlib.PyCdlib()

    # Necessary to move bin format to iso
    bin_to_iso(SRC_BIN, SRC_ISO)
    
    iso.open(SRC_ISO)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with MANIFEST.open("w", encoding="utf-8") as mf:
        for disk_path, pycd_file in walk_iso(iso):
            # build local file path
            rel_path = Path(disk_path.lstrip("/"))
            local_file = OUT_DIR / rel_path
            local_file.parent.mkdir(parents=True, exist_ok=True)

            # extract the file data
            with local_file.open("wb") as f:
                iso.get_file_from_iso_fp(f, fileid=pycd_file.file_identifier(),
                                         path=disk_path)

            size = local_file.stat().st_size
            mf.write(f"{disk_path}\t{size} bytes\n")

    iso.close()
    print(f"Extraction finished. Manifest written to {MANIFEST}")

# if __name__ == "__main__":
#     main()