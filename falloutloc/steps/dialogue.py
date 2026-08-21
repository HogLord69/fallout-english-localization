"""Dialogue revisions -> loose `.msg` overrides.

885 revised strings live in data/dialogue/master_revisions.py, keyed by
(filename, string_id). Ownership is NOT declared anywhere: the `GAME` labels
in data/dialogue/batches/b*.py are wrong and must not be trusted. Instead we
resolve ownership at install time by asking each install which .msg files it
actually contains.

Output goes to `<install>/data/text/english/` as loose files, which the engine
loads ahead of master.dat. No archive is rebuilt.
"""
import os
import sys

from .. import dat_replace as dr, msg, games


def load_revisions(repo_root):
    """{filename: {id: text}} from the master dictionary."""
    data_dir = os.path.join(repo_root, "data", "dialogue")
    sys.path.insert(0, data_dir)
    try:
        import master_revisions
    finally:
        sys.path.remove(data_dir)
    by_file = {}
    for (filename, sid), text in master_revisions.REVISIONS.items():
        by_file.setdefault(filename.lower(), {})[sid] = text
    return by_file


def index_archive(path, text_root):
    """basename -> (entry, subdir, cased_name), for entries under text\\<root>\\.

    The subdirectory matters: every dialogue file lives under `dialog\\` or
    `game\\`, never at the root of the text folder. A loose override only wins
    if its path mirrors the archive path, so a flat
    `data/text/english/foo.msg` is silently ignored by the engine.
    """
    raw, entries = dr.read_entries(path)
    found = {}
    for e in entries:
        name = e["name"].replace("/", "\\")
        parts = name.split("\\")
        lower = [p.lower() for p in parts]
        if len(parts) >= 3 and lower[0] == "text" and lower[1] == text_root:
            subdir = os.path.join(*parts[2:-1]) if len(parts) > 3 else ""
            found[lower[-1]] = (e, subdir, parts[-1])
    return raw, found


def run(repo_root, game_key, install, dry_run=False, log=print, record=None):
    spec = games.GAMES[game_key]
    by_file = load_revisions(repo_root)

    master = os.path.join(install, "master.dat")
    if not os.path.exists(master):
        log(f"  ! no master.dat in {install}")
        return 0, 0

    raw, index = index_archive(master, spec["text_root"])
    log(f"  archive: {len(index)} .msg under text\\{spec['text_root']}\\")

    # TRAP: the target is ALWAYS english, even when the source is russian.
    out_dir = os.path.join(install, "data", "text", "english")

    files_done = strings_done = 0
    for filename, revisions in sorted(by_file.items()):
        found = index.get(filename)
        if found is None:
            continue  # this game does not have this file -- not its dialogue
        entry, subdir, cased = found

        # Mirror the archive's subdirectory, but always land in english/.
        target_dir = os.path.join(out_dir, subdir) if subdir else out_dir
        target = os.path.join(target_dir, cased)

        # Pick a clean base: a previous run's .orig, else the archive copy.
        # Using .orig keeps re-runs idempotent instead of stacking edits.
        orig = target + ".orig"
        if os.path.exists(orig):
            base = open(orig, "rb").read()
        else:
            base = dr.content(raw, entry)

        patched, applied, _ = msg.patch(base, revisions)
        if not applied:
            continue

        if dry_run:
            files_done += 1
            strings_done += len(applied)
            continue

        os.makedirs(target_dir, exist_ok=True)
        existed = os.path.exists(target)
        if existed and not os.path.exists(orig):
            games.backup(target)
        if record is not None:
            record.note(target, existed)
        with open(target, "wb") as f:
            f.write(patched)

        # Verify by reading back off disk, not by re-running the transform.
        bad = msg.verify(target, {k: revisions[k] for k in applied})
        if bad:
            log(f"  ! {filename}: {len(bad)} strings did not land")
            continue

        files_done += 1
        strings_done += len(applied)

    return files_done, strings_done
