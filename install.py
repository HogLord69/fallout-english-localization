#!/usr/bin/env python3
"""Apply the English localization to your own Fallout mod installs.

Nothing here modifies master.dat. Dialogue and premade characters install as
loose files under data/, which the engine loads first; the appearance archives
are repacked surgically. Every file this touches gets a `.orig` backup, and
re-running is idempotent because those backups are used as the base.

  python install.py --list
  python install.py --game nevada --dry-run
  python install.py --game nevada
  python install.py --all
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from falloutloc import games
from falloutloc.manifest import Manifest
from falloutloc.steps import dialogue, premade, appearance, outfit

REPO = os.path.dirname(os.path.abspath(__file__))
STEPS = ("dialogue", "premade", "appearance", "outfit")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--game", choices=sorted(games.GAMES), help="which install to patch")
    ap.add_argument("--all", action="store_true", help="every install found")
    ap.add_argument("--list", action="store_true", help="show detected installs and exit")
    ap.add_argument("--path", help="override the install directory for --game")
    ap.add_argument("--outfit-source", help="path to your Nevada Mod (Extended) copy")
    ap.add_argument("--steps", default=",".join(STEPS),
                    help=f"comma-separated subset of: {', '.join(STEPS)}")
    ap.add_argument("--dry-run", action="store_true", help="report without writing")
    args = ap.parse_args()

    if args.list:
        for key in sorted(games.GAMES):
            found = games.resolve(key)
            print(f"  {'OK  ' if found else 'MISS'} {key:14} {found or games.GAMES[key]['default']}")
        src = games.OUTFIT_SOURCE
        ok = os.path.exists(os.path.join(src["default"], src["archive"]))
        print(f"  {'OK  ' if ok else 'MISS'} {'outfit-source':14} {src['default']}")
        return 0

    if not args.game and not args.all:
        ap.error("pass --game <name>, --all, or --list")

    selected = sorted(games.GAMES) if args.all else [args.game]
    steps = [s.strip() for s in args.steps.split(",") if s.strip()]
    for s in steps:
        if s not in STEPS:
            ap.error(f"unknown step {s!r}; choose from {', '.join(STEPS)}")

    tag = "[dry run] " if args.dry_run else ""
    failures = 0

    for key in selected:
        install = games.resolve(key, args.path if args.game == key else None)
        if install is None:
            print(f"\n{games.GAMES[key]['label']}: not found, skipping")
            continue
        print(f"\n{tag}{games.GAMES[key]['label']}\n  {install}")
        record = None if args.dry_run else Manifest(install)

        if "dialogue" in steps:
            files, strings = dialogue.run(REPO, key, install, args.dry_run, record=record)
            print(f"  dialogue    {strings:4} strings across {files} files")

        if "premade" in steps:
            bios, names = premade.run(REPO, key, install, args.dry_run, record=record)
            print(f"  premade     {bios} bios, {names} names")

        if "appearance" in steps:
            archives, strings = appearance.run(REPO, key, install, args.dry_run, record=record)
            print(f"  appearance  {strings:4} strings across {archives} archives")

        if "outfit" in steps and key == "nevada":
            count, size = outfit.run(REPO, install, args.outfit_source, args.dry_run, record=record)
            print(f"  outfit      {count} sprites ({size / 1048576:.1f} MB)")

        if record is not None:
            record.save()

    print(f"\n{tag}done." + ("" if args.dry_run else "  Restore with revert.py."))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
