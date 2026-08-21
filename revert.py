#!/usr/bin/env python3
"""Undo what install.py did.

Files that were replaced are restored from their `.orig` backup. Files the
installer created outright -- most dialogue overrides, and every ported sprite
-- have no backup, so they are deleted instead. Both sets are read from the
manifest install.py leaves in the install root.

  python revert.py --game nevada --dry-run
  python revert.py --all
"""
import argparse
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from falloutloc import games
from falloutloc.manifest import Manifest, NAME as MANIFEST_NAME


def prune_empty(root, install):
    """Remove directories the install left behind, deepest first."""
    for base, dirs, files in os.walk(root, topdown=False):
        if os.path.abspath(base) == os.path.abspath(install):
            continue
        try:
            if not os.listdir(base):
                os.rmdir(base)
        except OSError:
            pass


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--game", choices=sorted(games.GAMES))
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--path")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not args.game and not args.all:
        ap.error("pass --game <name> or --all")

    tag = "[dry run] " if args.dry_run else ""
    for key in (sorted(games.GAMES) if args.all else [args.game]):
        install = games.resolve(key, args.path if args.game == key else None)
        if install is None:
            continue
        print(f"\n{tag}{games.GAMES[key]['label']}")

        m = Manifest(install)
        if not m.created and not m.replaced:
            print("  no manifest -- nothing recorded to undo")
            continue

        restored = deleted = missing = 0

        for rel in sorted(m.replaced):
            target = os.path.join(install, rel.replace("/", os.sep))
            orig = target + ".orig"
            if not os.path.exists(orig):
                missing += 1
                continue
            if not args.dry_run:
                shutil.copyfile(orig, target)
                os.remove(orig)
            restored += 1

        for rel in sorted(m.created):
            target = os.path.join(install, rel.replace("/", os.sep))
            if not os.path.exists(target):
                continue
            if not args.dry_run:
                os.remove(target)
            deleted += 1

        print(f"  restored {restored:5} replaced files")
        print(f"  deleted  {deleted:5} created files")
        if missing:
            print(f"  ! {missing} backups missing, those files left as-is")

        if not args.dry_run:
            prune_empty(os.path.join(install, "data"), install)
            manifest_path = os.path.join(install, MANIFEST_NAME)
            if os.path.exists(manifest_path):
                os.remove(manifest_path)

    print(f"\n{tag}done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
