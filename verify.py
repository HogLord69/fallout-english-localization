#!/usr/bin/env python3
"""Check an install or a built bundle for text that is still Russian.

Run this before shipping anything. v1.0 went out with three games' worth of
Russian dialogue because nothing checked the output -- the installer reported
success for every string it wrote, which was true and useless, since the
strings it did not write were the problem.

    python verify.py --path "C:\\FalloutTrilogy-English\\games\\Sonora"
    python verify.py --bundle "C:\\FalloutTrilogy-English"
    python verify.py --all                 # every detected install

Exit code is non-zero if any game exceeds the baseline, so it works in a
build script.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from falloutloc import games, msg

# Strings these games ship untranslated regardless of anything we do. Measured
# against pristine installs, with headroom. Exceeding these means we broke it.
BASELINE = {"Resurrection": 20, "Nevada": 10, "Sonora": 300}


def scan(root):
    """-> (files, strings, cyrillic_strings, worst_offenders)"""
    files = total = bad = 0
    worst = []
    for base, _, names in os.walk(root):
        for name in names:
            if not name.lower().endswith(".msg"):
                continue
            path = os.path.join(base, name)
            try:
                raw = open(path, "rb").read()
            except OSError:
                continue
            strings = len(msg.ENTRY.findall(raw))
            if not strings:
                continue
            cyr = msg.cyrillic_count(raw)
            files += 1
            total += strings
            bad += cyr
            if cyr:
                worst.append((cyr, strings, os.path.relpath(path, root)))
    return files, total, bad, sorted(worst, reverse=True)


def report(label, root, limit, log=print):
    if not os.path.isdir(root):
        log(f"{label:16} MISSING  {root}")
        return None
    files, total, bad, worst = scan(root)
    pct = 100 * bad / total if total else 0
    verdict = "OK  " if bad <= limit else "FAIL"
    log(f"{verdict} {label:16} {files:4} files  {total:6} strings  "
        f"{bad:6} Russian ({pct:.1f}%)  baseline {limit}")
    if bad > limit:
        for cyr, strings, rel in worst[:6]:
            log(f"       {cyr:5}/{strings:<5} {rel}")
    return bad <= limit


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--path", help="a single game folder")
    ap.add_argument("--bundle", help="a folder built by bundle.py")
    ap.add_argument("--all", action="store_true", help="every detected install")
    args = ap.parse_args()

    if not (args.path or args.bundle or args.all):
        ap.error("pass --path, --bundle, or --all")

    results = []
    text = os.path.join("data", "text", "english")

    if args.path:
        label = os.path.basename(os.path.normpath(args.path))
        results.append(report(label, os.path.join(args.path, text),
                              BASELINE.get(label, 0)))
    if args.bundle:
        for name in sorted(BASELINE):
            results.append(report(name,
                                  os.path.join(args.bundle, "games", name, text),
                                  BASELINE[name]))
    if args.all:
        for key in sorted(games.GAMES):
            install = games.resolve(key)
            if install is None:
                continue
            label = games.GAMES[key]["label"].split(":")[-1].strip().split()[0]
            results.append(report(label, os.path.join(install, text),
                                  BASELINE.get(label, 0)))

    results = [r for r in results if r is not None]
    failed = results.count(False)
    print()
    if failed:
        print(f"{failed} of {len(results)} FAILED -- do not ship this")
    else:
        print(f"all {len(results)} within baseline")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
