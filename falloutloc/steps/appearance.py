"""Character sheet (appearance mod) translation.

These strings live inside .dat archives, so there is no loose-file override.
Instead each archive is repacked surgically: the changed .msg is recompressed
and every other entry keeps its ORIGINAL stored bytes, so the rebuild is
identical apart from the replaced files and the shifted offsets.

Do NOT rebuild master.dat this way -- full recompression of a 198 MB archive
is far too slow. These appearance archives are small enough.

Sonora is deliberately absent: its per-model English is stock Fallout 2 filler
("Generic Default Dude"), not a translation. Do not propagate it.
"""
import json
import os

from .. import dat_replace as dr, msg, games

TAGS = {"resurrection": "RES", "nevada": "NEV"}


def run(repo_root, game_key, install, dry_run=False, log=print, record=None):
    tag = TAGS.get(game_key)
    if tag is None:
        log("  - no appearance translation for this game (see module docstring)")
        return 0, 0

    data = json.load(open(os.path.join(repo_root, "data", "appearance",
                                       "appearance_en.json"), encoding="utf-8"))
    wanted = data.get(tag, {})
    folder = os.path.join(install, "appearance")
    if not os.path.isdir(folder):
        log(f"  ! no appearance/ folder in {install}")
        return 0, 0

    # Match archives case-insensitively; the three games disagree on .dat/.DAT.
    on_disk = {n.lower(): n for n in os.listdir(folder) if n.lower().endswith(".dat")}

    archives_done = strings_done = 0
    for archive_name, files in sorted(wanted.items()):
        actual = on_disk.get(archive_name.lower())
        if actual is None:
            log(f"  ! {archive_name}: not present")
            continue
        path = os.path.join(folder, actual)

        # Work from the pristine archive when we have one, so re-runs do not
        # stack repacks on top of repacks.
        orig = path + ".orig"
        source = orig if os.path.exists(orig) else path

        raw, entries = dr.read_entries(source)
        current = {}
        for e in entries:
            base = e["name"].split("\\")[-1].lower()
            if base in files:
                current[base] = dr.content(raw, e)

        replacements = {}
        count = 0
        for base, strings in files.items():
            if base not in current:
                continue
            patched, applied, _ = msg.patch(current[base], strings)
            if applied:
                replacements[base] = patched
                count += len(applied)

        if not replacements:
            continue
        if dry_run:
            archives_done += 1
            strings_done += count
            continue

        games.backup(path)
        if record is not None:
            record.note(path, True)
        changed = dr.replace(source, path, replacements)

        # Confirm nothing but the intended entries moved.
        diff = dr.verify(orig if os.path.exists(orig) else source, path, changed)
        unexpected = [n for n in diff if n.split("\\")[-1].lower() not in replacements]
        if unexpected:
            log(f"  ! {actual}: {len(unexpected)} unexpected entries changed")
            continue

        archives_done += 1
        strings_done += count

    return archives_done, strings_done
