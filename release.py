#!/usr/bin/env python3
"""Turn a built bundle into one distributable archive per game.

Each archive extracts to a single self-contained folder that plays as-is:

    Fallout-Sonora-English/
      Play Sonora.bat
      READ ME FIRST.txt
      CREDITS.txt
      <the game>

One game per archive, because GitHub Releases caps a single asset at 2 GB and
the three together are ~4.8 GB. Staging is built and deleted one game at a
time, so the extra disk needed is only the largest game plus its archive.

    python release.py --bundle "C:\\FalloutTrilogy-English" --out "C:\\release"
    python release.py --bundle ... --out ... --game sonora

Requires 7-Zip. Archives are written as .zip so Windows can open them with no
extra software.
"""
import argparse
import os
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bundle import BUNDLE

REPO = os.path.dirname(os.path.abspath(__file__))

SEVENZIP = [r"C:\Program Files\7-Zip\7z.exe", r"C:\Program Files (x86)\7-Zip\7z.exe",
            "7z", "7za"]

# GitHub Releases refuses a single asset over 2 GB.
ASSET_LIMIT = 2 * 1000 ** 3

LAUNCHER = """@echo off
rem {title} -- English edition.
cd /d "%~dp0"
start "" "{exe}"
"""

READ_ME = """{title} -- ENGLISH EDITION
{rule}

TO PLAY
-------

  Double-click:  Play {folder}.bat

That's all. Nothing to install, nothing to configure. Your saves stay in
this folder.


WHAT'S BEEN TRANSLATED
----------------------

{summary}

If the game opens to a black screen, right-click {exe}, choose
Properties -> Compatibility, and tick "Disable fullscreen optimizations".


CREDITS
-------

See CREDITS.txt. This English work stands on top of years of other
people's, and they are the reason it exists at all.
"""


def find_7z():
    for candidate in SEVENZIP:
        if os.path.exists(candidate):
            return candidate
        found = shutil.which(candidate)
        if found:
            return found
    raise RuntimeError("7-Zip not found; install it or add 7z to PATH")


SUMMARY = {
    "resurrection": "  * 100 dialogue lines revised across 17 files\n"
                    "  * 3 premade character biographies rewritten\n"
                    "  * Character sheet and appearance menus translated",
    "nevada": "  * 266 dialogue lines revised across 25 files\n"
              "  * 3 premade character biographies rewritten, 3 names\n"
              "  * Character sheet and appearance menus translated\n"
              "  * Alternate outfit sprites installed",
    "sonora": "  * 566 dialogue lines revised across 160 files\n"
              "  * 4 premade character biographies rewritten, 4 names",
}


def build(key, bundle, out, sevenzip, log=print):
    folder, exe, title = BUNDLE[key]
    src = os.path.join(bundle, "games", folder)
    if not os.path.isdir(src):
        log(f"{title}: not in bundle, skipping")
        return None

    name = f"Fallout-{folder}-English"
    staging = os.path.join(out, "_staging", name)
    archive = os.path.join(out, name + ".zip")

    if os.path.exists(staging):
        shutil.rmtree(staging)
    os.makedirs(staging, exist_ok=True)

    log(f"\n{title}\n  staging")
    t0 = time.time()
    if os.name == "nt":
        r = subprocess.run(["robocopy", src, staging, "/E", "/MT:16", "/R:1", "/W:1",
                            "/NFL", "/NDL", "/NJH", "/NJS", "/NP"],
                           capture_output=True, text=True)
        if r.returncode >= 8:
            raise RuntimeError(f"robocopy failed ({r.returncode})")
    else:
        shutil.copytree(src, staging, dirs_exist_ok=True)

    with open(os.path.join(staging, f"Play {folder}.bat"), "w", newline="\r\n") as f:
        f.write(LAUNCHER.format(title=title, exe=exe))
    with open(os.path.join(staging, "READ ME FIRST.txt"), "w", newline="\r\n") as f:
        f.write(READ_ME.format(title=title.upper(), rule="=" * (len(title) + 18),
                               folder=folder, exe=exe, summary=SUMMARY[key]))
    credits_src = os.path.join(REPO, "CREDITS.md")
    if os.path.exists(credits_src):
        with open(credits_src, encoding="utf-8") as f:
            text = f.read()
        with open(os.path.join(staging, "CREDITS.txt"), "w", newline="\r\n",
                  encoding="utf-8") as f:
            f.write(text)

    log(f"  staged in {time.time() - t0:.0f}s, compressing")
    if os.path.exists(archive):
        os.remove(archive)
    t0 = time.time()
    # -mx=3: the .dat payloads are already deflated, so heavy settings buy
    # almost nothing and cost minutes.
    r = subprocess.run([sevenzip, "a", "-tzip", "-mx=3", "-mmt=on", "-bso0", "-bsp0",
                        archive, staging], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"7z failed ({r.returncode})\n{r.stdout}\n{r.stderr}")

    shutil.rmtree(staging, ignore_errors=True)
    size = os.path.getsize(archive)
    raw = sum(os.path.getsize(os.path.join(b, n))
              for b, _, fs in os.walk(src) for n in fs)
    log(f"  {size / 2**30:.2f} GB in {time.time() - t0:.0f}s "
        f"({100 * size / raw:.0f}% of raw)")
    if size > ASSET_LIMIT:
        log(f"  !! OVER the {ASSET_LIMIT / 1000**3:.0f} GB GitHub asset limit")
    return archive, size


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bundle", required=True, help="folder built by bundle.py")
    ap.add_argument("--out", required=True, help="where to write the archives")
    ap.add_argument("--game", choices=sorted(BUNDLE))
    args = ap.parse_args()

    sevenzip = find_7z()
    os.makedirs(args.out, exist_ok=True)
    results = []
    for key in ([args.game] if args.game else sorted(BUNDLE)):
        got = build(key, os.path.abspath(args.bundle), os.path.abspath(args.out), sevenzip)
        if got:
            results.append(got)

    staging_root = os.path.join(args.out, "_staging")
    if os.path.isdir(staging_root):
        shutil.rmtree(staging_root, ignore_errors=True)

    print("\nArchives:")
    over = 0
    for path, size in results:
        flag = "  OVER LIMIT" if size > ASSET_LIMIT else ""
        print(f"  {size / 2**30:6.2f} GB  {os.path.basename(path)}{flag}")
        over += size > ASSET_LIMIT
    return 1 if over else 0


if __name__ == "__main__":
    sys.exit(main())
