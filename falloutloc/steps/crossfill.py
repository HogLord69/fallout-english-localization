"""Fill leftover Russian strings from another game's English.

All three games sit on the same Fallout 2 engine and share a large body of
generic text -- container descriptions, misc UI messages, party orders,
random encounter chatter. Nevada ships clean English for all of it. Sonora and
Resurrection ship some of the same files still in Russian.

So: donate. For every string that is still Russian in the target, if Nevada's
English has the same file and the same string id, use it.

Measured coverage of the target's Russian ids:

    CONTAINR.MSG  Resurrection   111/111   100%
    MISC.MSG      Resurrection   120/120   100%
    MISC.MSG      Sonora          67/69     97%
    PIPBOY.MSG    Sonora         281/518    54%

Only strings that are *already Russian* are touched. English is never
overwritten, so this cannot regress a working translation, and running it
twice changes nothing the second time.

The remainder -- mostly Sonora's Pip-Boy, which carries game-specific quest
and date text with no counterpart in Nevada -- needs real translation and is
deliberately left alone rather than filled with something that reads right but
means the wrong thing.
"""
import json
import os

from .. import msg, games

DONOR = "data/crossfill/engine_en.json"


def load_donor(repo_root):
    path = os.path.join(repo_root, *DONOR.split("/"))
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def run(repo_root, game_key, install, dry_run=False, log=print, record=None):
    donor = load_donor(repo_root)
    if not donor:
        return 0, 0

    text_root = os.path.join(install, "data", "text", "english")
    if not os.path.isdir(text_root):
        return 0, 0

    files_done = strings_done = 0
    for base, _, names in os.walk(text_root):
        for name in names:
            if not name.lower().endswith(".msg"):
                continue
            give = donor.get(name.lower())
            if not give:
                continue
            path = os.path.join(base, name)
            raw = open(path, "rb").read()
            if not msg.cyrillic_count(raw):
                continue

            current = msg.parse(raw)
            fill = {}
            for sid, text in current.items():
                if not any(ord(c) > 127 for c in text):
                    continue  # already English, leave it
                if sid in give:
                    fill[sid] = give[sid]
            if not fill:
                continue

            if dry_run:
                files_done += 1
                strings_done += len(fill)
                continue

            patched, applied, _ = msg.patch(raw, fill)
            existed = os.path.exists(path)
            if existed and not os.path.exists(path + ".orig"):
                games.backup(path)
            if record is not None:
                record.note(path, existed)
            with open(path, "wb") as f:
                f.write(patched)

            bad = msg.verify(path, {k: fill[k] for k in applied})
            if bad:
                log(f"  ! {name}: {len(bad)} filled strings did not land")
                continue
            files_done += 1
            strings_done += len(applied)

    return files_done, strings_done
