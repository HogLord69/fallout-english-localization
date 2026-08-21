#!/usr/bin/env python3
"""Build a self-contained, pre-patched, ready-to-play folder from your own installs.

This produces the "one folder, double-click and play" layout:

    FalloutTrilogy-English/
      START HERE.txt
      Play Resurrection.bat
      Play Nevada.bat
      Play Sonora.bat
      games/
        Resurrection/   full install, English patch already applied
        Nevada/
        Sonora/

The bundle is roughly 5-6 GB, so it is NEVER committed to this repository --
GitHub caps individual files at 100 MB, and a game install is far past that.
The script is what ships; the bundle is what you build.

    python bundle.py --out "C:\\FalloutTrilogy-English"
    python bundle.py --out "D:\\Bundle" --game nevada      # just one

NOTE ON SHARING: these games are free to download, but "free" is not the same
as "free to redistribute". The bundle you build here is fine for your own use.
Handing it to other people needs the permission of each game's team, and of
Nevada Mod (Extended)'s author for the ported outfit art.
"""
import argparse
import os
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from falloutloc import games
from falloutloc.manifest import Manifest
from falloutloc.steps import dialogue, premade, appearance, outfit, crossfill

REPO = os.path.dirname(os.path.abspath(__file__))

# Folder name inside the bundle, and the executable its launcher runs.
BUNDLE = {
    "resurrection": ("Resurrection", "Resurrection.exe", "Fallout: Resurrection"),
    "nevada": ("Nevada", "NEVADA_EV.exe", "Fallout: Nevada"),
    "sonora": ("Sonora", "FSonora+DLC.exe", "Fallout: Sonora"),
}

# Working files, crash dumps and installer leftovers that a player never needs.
SKIP_FILES = ["*.orig", "*.dmp", "master.dat.backup", "sfall-log*.txt",
              ".falloutloc-manifest.json"]
SKIP_DIRS = ["_localization-project", "_english_port", "uninstall"]

LAUNCHER = """@echo off
rem {title} -- launcher. The game must run from its own folder.
cd /d "%~dp0games\\{folder}"
start "" "{exe}"
"""

BLURB = {
    "resurrection": "Fallout: Resurrection    A Czech total conversion. New story, new world map.",
    "nevada": "Fallout: Nevada          A prequel set before the events of Fallout 1.",
    "sonora": "Fallout: Sonora          Set in the Sonoran desert, by the Nevada team.",
}

READ_ME = """FALLOUT - ENGLISH EDITION
=========================

{count} complete Fallout 2 total conversions, in English, ready to play.
Nothing to install. Nothing to configure.

  1. Double-click one of these:

{launchers}

  2. That's it.


WHAT'S HERE
-----------

  {blurbs}

Every one of them runs on the original Fallout 2 engine, so they play exactly
the way you remember.


ENGLISH LOCALIZATION
--------------------

  * {revisions} dialogue lines revised across {files} files
  * {bios} premade character biographies rewritten
  * Character sheet and appearance menus translated
{outfit_line}
Saves live inside each game's own folder, under games\\.

If a game opens with a black screen, right-click its .exe, choose
Properties -> Compatibility, and tick "Disable fullscreen optimizations".


A NOTE ON SHARING
-----------------

These games are free to download from their developers, and this English
work is free too. That still is not the same as permission to re-upload
them. If you want to pass this on, link people to each team's own download
page rather than copying the folder.

Built {date}.
"""


def copy_install(src, dst, log=print):
    """Copy a game install, skipping working files. Uses robocopy on Windows."""
    os.makedirs(dst, exist_ok=True)
    if os.name == "nt":
        cmd = ["robocopy", src, dst, "/E", "/MT:16", "/R:1", "/W:1",
               "/NFL", "/NDL", "/NJH", "/NJS", "/NP"]
        cmd += ["/XF"] + SKIP_FILES
        cmd += ["/XD"] + [os.path.join(src, d) for d in SKIP_DIRS]
        result = subprocess.run(cmd, capture_output=True, text=True)
        # robocopy: 0-7 are success, 8+ are real failures
        if result.returncode >= 8:
            raise RuntimeError(f"robocopy failed ({result.returncode})\n{result.stdout}")
        return
    ignore = shutil.ignore_patterns(*(SKIP_FILES + SKIP_DIRS))
    shutil.copytree(src, dst, dirs_exist_ok=True, ignore=ignore)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True, help="folder to build the bundle in")
    ap.add_argument("--game", choices=sorted(BUNDLE), help="only bundle this one")
    ap.add_argument("--outfit-source", help="path to your Nevada Mod (Extended) copy")
    ap.add_argument("--skip-copy", action="store_true",
                    help="re-patch an already-copied bundle without copying again")
    ap.add_argument("--keep-backups", action="store_true",
                    help="keep the .orig patch backups (adds ~150 MB per game)")
    args = ap.parse_args()

    out = os.path.abspath(args.out)
    os.makedirs(os.path.join(out, "games"), exist_ok=True)
    selected = [args.game] if args.game else sorted(BUNDLE)

    totals = {"revisions": 0, "files": 0, "bios": 0}
    built = []

    for key in selected:
        folder, exe, title = BUNDLE[key]
        src = games.resolve(key)
        if src is None:
            print(f"{title}: install not found, skipping")
            continue
        dst = os.path.join(out, "games", folder)

        if not args.skip_copy:
            print(f"\n{title}\n  copying {src}")
            t0 = time.time()
            copy_install(src, dst)
            size = sum(os.path.getsize(os.path.join(r, f))
                       for r, _, fs in os.walk(dst) for f in fs)
            print(f"  copied {size / 2**30:.1f} GB in {time.time() - t0:.0f}s")
        else:
            print(f"\n{title}\n  reusing {dst}")

        print("  applying English patch")
        record = Manifest(dst)
        f, s = dialogue.run(REPO, key, dst, record=record)
        cf, cs = crossfill.run(REPO, key, dst, record=record)
        b, n = premade.run(REPO, key, dst, record=record)
        a, ast = appearance.run(REPO, key, dst, record=record, log=lambda *_: None)
        print(f"    dialogue   {s} strings / {f} files")
        if cs:
            print(f"    crossfill  {cs} strings / {cf} files")
        print(f"    premade    {b} bios, {n} names")
        if a:
            print(f"    appearance {ast} strings / {a} archives")
        if key == "nevada":
            c, bts = outfit.run(REPO, dst, args.outfit_source, record=record)
            if c:
                print(f"    outfit     {c} sprites ({bts / 2**20:.1f} MB)")
        record.save()

        totals["revisions"] += s
        totals["files"] += f
        totals["bios"] += b
        built.append(key)

        with open(os.path.join(out, f"Play {folder}.bat"), "w", newline="\r\n") as fh:
            fh.write(LAUNCHER.format(title=title, folder=folder, exe=exe))

    if not built:
        print("\nNothing built.")
        return 1

    if not args.keep_backups:
        # A play-ready bundle is not a revertible install. The .orig copies of
        # the appearance archives alone are ~150 MB per game.
        freed = 0
        for key in built:
            root = os.path.join(out, "games", BUNDLE[key][0])
            for base, _, files in os.walk(root):
                for name in files:
                    if name.endswith(".orig") or name == ".falloutloc-manifest.json":
                        path = os.path.join(base, name)
                        freed += os.path.getsize(path)
                        os.remove(path)
        if freed:
            print(f"\nremoved {freed / 2**20:.0f} MB of patch backups")

    words = {1: "One", 2: "Two", 3: "Three"}
    with open(os.path.join(out, "START HERE.txt"), "w", newline="\r\n") as fh:
        fh.write(READ_ME.format(
            date=time.strftime("%B %Y"),
            count=words.get(len(built), str(len(built))),
            launchers="\n".join(f"       Play {BUNDLE[k][0]}.bat" for k in built),
            blurbs="\n  ".join(BLURB[k] for k in built),
            outfit_line="  * Nevada's alternate outfit sprites installed\n"
                        if "nevada" in built else "",
            **totals))

    size = sum(os.path.getsize(os.path.join(r, f))
               for r, _, fs in os.walk(out) for f in fs)
    print(f"\nBundle ready: {out}  ({size / 2**30:.1f} GB)")
    print("Double-click a 'Play ....bat' to start.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
