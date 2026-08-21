"""Nevada outfit port -- dark-grey white-skull jumpsuit.

IMPORTANT: the sprites are Nevada Mod (Extended)'s art, not ours. This
repository contains NO art. data/outfit/sprites.txt is a manifest of 317
filenames; the installer copies those entries out of the user's own
`Nevada Mod (Extended)\\Patch000.dat` into their own Nevada install.

Known gaps, investigated and accepted -- do not treat as bugs:

  * 10 animations exist only in the live build with no skull counterpart:
    hmjmpsbe, bh, bj, bk (weapon poses) and bn, na, re, rh, rj, rk
    (the death set plus one special). These still show blue.
  * The appearance mod's seven alternate models (~1,155 sprites) wear blue
    full-time. No skull art exists for them anywhere.

The skull suit is not a palette recolor -- 47.3% of pixels differ, 105 of 115
palette indices map to more than one target, and 6 of 30 frames differ in
dimensions. It is separately drawn art, so no mechanical transform closes the
gap; only hand pixel-art would.
"""
import os

from .. import dat_replace as dr, games


def load_manifest(repo_root):
    path = os.path.join(repo_root, "data", "outfit", "sprites.txt")
    with open(path) as f:
        return {line.strip().lower() for line in f if line.strip()}


def run(repo_root, install, source_dir=None, dry_run=False, log=print, record=None):
    spec = games.OUTFIT_SOURCE
    source_dir = source_dir or spec["default"]
    archive = os.path.join(source_dir, spec["archive"])
    if not os.path.exists(archive):
        log(f"  ! {spec['label']} not found at {source_dir}")
        log(f"    This step needs your own copy; no art ships with this repo.")
        return 0, 0

    wanted = load_manifest(repo_root)
    raw, entries = dr.read_entries(archive)
    out_dir = os.path.join(install, "data", "art", "critters")

    copied = written_bytes = 0
    for e in entries:
        base = e["name"].split("\\")[-1].lower()
        if base not in wanted:
            continue
        data = dr.content(raw, e)
        if dry_run:
            copied += 1
            written_bytes += len(data)
            continue
        os.makedirs(out_dir, exist_ok=True)
        sprite = os.path.join(out_dir, e["name"].split("\\")[-1])
        if record is not None:
            record.note(sprite, os.path.exists(sprite))
        with open(sprite, "wb") as f:
            f.write(data)
        copied += 1
        written_bytes += len(data)

    missing = len(wanted) - copied
    if missing > 0:
        log(f"  - {missing} manifest entries not in {spec['archive']}")
    return copied, written_bytes
