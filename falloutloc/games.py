"""Install discovery and per-game facts.

Nothing here is copied from a game; these are just paths and layout notes.
"""
import os

# Default install locations. Override with --path on the command line.
GAMES = {
    "resurrection": dict(
        label="Fallout: Resurrection",
        default=r"C:\Fallout Resurrection (FE)",
        marker="Resurrection.exe",
        # master.dat carries text\english\ (629 entries)
        text_root="english",
    ),
    "nevada": dict(
        label="Fallout: Nevada (Expansion Version)",
        default=r"C:\Fallout Nevada (Expansion Version)",
        marker="NEVADA_EV.exe",
        text_root="english",
    ),
    "sonora": dict(
        label="Fallout: Sonora (Extended Release)",
        default=r"C:\Fallout Sonora (Extended Release)",
        marker="FSonora+DLC.exe",
        # TRAP: Sonora's master.dat contains ONLY text\russian\ paths.
        # Reading by basename and taking the first hit writes revisions into
        # the Russian folder. Always resolve the *target* to english.
        text_root="russian",
    ),
}

# Source of the skull-suit sprites for the outfit port. This is a separate
# mod's art -- the installer copies it out of the user's own copy and the
# repository redistributes none of it.
OUTFIT_SOURCE = dict(
    label="Nevada Mod (Extended)",
    default=r"C:\Nevada Mod (Extended)",
    archive="Patch000.dat",
)


def resolve(key, override=None):
    """Return the install directory for `key`, or None if it is not there."""
    spec = GAMES[key]
    path = override or spec["default"]
    if not os.path.isdir(path):
        return None
    if not os.path.exists(os.path.join(path, spec["marker"])):
        # Marker missing -- still usable if it looks like a Fallout install.
        if not os.path.exists(os.path.join(path, "master.dat")):
            return None
    return path


def archives(path):
    """Every .dat in the install root, case-insensitively.

    Sonora and Resurrection ship `.DAT`; Nevada ships `.dat`. A `*.dat` glob
    silently skips half the archives on a case-sensitive filesystem.
    """
    out = []
    for name in sorted(os.listdir(path)):
        if not name.lower().endswith(".dat"):
            continue
        full = os.path.join(path, name)
        # Resurrection ships a 0-byte fores.dat placeholder.
        if os.path.getsize(full) == 0:
            continue
        out.append(full)
    return out


def backup(path):
    """Create `<path>.orig` once. Returns the path to use as a clean base.

    Idempotent: if the backup already exists it is left alone and returned,
    so re-running the installer never stacks edits on top of edits.
    """
    orig = path + ".orig"
    if os.path.exists(path) and not os.path.exists(orig):
        with open(path, "rb") as f:
            data = f.read()
        with open(orig, "wb") as f:
            f.write(data)
    return orig if os.path.exists(orig) else None
