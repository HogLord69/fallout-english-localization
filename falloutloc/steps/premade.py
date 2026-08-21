"""Premade characters: rewritten bios and transliterated names.

Bios are plain text and ship in this repo (data/premade/<TAG>/*.BIO) because
they were written from scratch. The .GCD character files are NOT shipped --
only the name string is, in data/premade/names.json. The installer patches the
32-byte name field of the user's own GCD in place.

The engine does NOT word-wrap bio text. It is hard-wrapped by hand to a
maximum of 20 characters per line and 22 lines; run check_bio() before editing.
"""
import json
import os
import shutil

from .. import dat_replace as dr, gcd, games

TAGS = {"resurrection": "RES", "nevada": "NEV", "sonora": "SON"}

MAX_COLS = 20
MAX_ROWS = 22


def check_bio(text):
    """Return a list of constraint violations, empty if the bio fits."""
    # A single trailing newline terminates the last line, it does not add one.
    lines = text.replace("\r\n", "\n").rstrip("\n").split("\n")
    problems = []
    if len(lines) > MAX_ROWS:
        problems.append(f"{len(lines)} lines (max {MAX_ROWS})")
    for i, line in enumerate(lines, 1):
        if len(line) > MAX_COLS:
            problems.append(f"line {i} is {len(line)} chars (max {MAX_COLS})")
    return problems


def _gcd_from_archives(install, basename):
    """Pull an untouched .GCD out of the install's archives."""
    for archive in games.archives(install):
        try:
            raw, entries = dr.read_entries(archive)
        except Exception:
            continue
        for e in entries:
            parts = e["name"].lower().replace("/", "\\").split("\\")
            if parts[-1] == basename.lower() and "premade" in parts:
                return dr.content(raw, e)
    return None


def run(repo_root, game_key, install, dry_run=False, log=print, record=None):
    tag = TAGS[game_key]
    src = os.path.join(repo_root, "data", "premade", tag)
    if not os.path.isdir(src):
        return 0, 0

    names = json.load(open(os.path.join(repo_root, "data", "premade", "names.json")))
    names = names.get(tag, {})
    out_dir = os.path.join(install, "data", "premade")

    bios = renamed = 0

    for bio in sorted(os.listdir(src)):
        if not bio.lower().endswith(".bio"):
            continue
        text = open(os.path.join(src, bio), encoding="cp1252").read()
        problems = check_bio(text)
        if problems:
            log(f"  ! {bio}: {'; '.join(problems)}")
            continue
        if dry_run:
            bios += 1
            continue
        os.makedirs(out_dir, exist_ok=True)
        target = os.path.join(out_dir, bio)
        existed = os.path.exists(target)
        if existed:
            games.backup(target)
        if record is not None:
            record.note(target, existed)
        shutil.copyfile(os.path.join(src, bio), target)
        bios += 1

    for basename, name in sorted(names.items()):
        target = os.path.join(out_dir, basename)
        orig = target + ".orig"
        if os.path.exists(orig):
            base = open(orig, "rb").read()
        elif os.path.exists(target):
            base = open(target, "rb").read()
        else:
            base = _gcd_from_archives(install, basename)
        if base is None:
            log(f"  ! {basename}: not found in install or archives")
            continue
        if dry_run:
            renamed += 1
            continue
        os.makedirs(out_dir, exist_ok=True)
        existed = os.path.exists(target)
        if existed:
            games.backup(target)
        if record is not None:
            record.note(target, existed)
        with open(target, "wb") as f:
            f.write(gcd.set_name(base, name))
        if gcd.get_name(open(target, "rb").read()) != name:
            log(f"  ! {basename}: name did not land")
            continue
        renamed += 1

    return bios, renamed
