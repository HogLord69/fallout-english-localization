"""Fallout 2 `.msg` parsing and patching.

The format is `{id}{}{text}` -- NOT `id=text`. An installer written against
`id=text` matches nothing and reports success anyway; see docs/FORMATS.md.

Patching is done by byte-level regex substitution of the third brace group
only, so every other byte of the file (comments, blank lines, line endings,
untouched strings) survives verbatim.
"""
import re

ENTRY = re.compile(rb"\{(\d+)\}\{([^}]*)\}\{([^}]*)\}", re.S)

# Text is ASCII after localization; cp1252 keeps any stray byte round-tripping.
ENCODING = "cp1252"


def parse(raw):
    """bytes -> {id: text}."""
    return {m.group(1).decode(): m.group(3).decode(ENCODING, "replace")
            for m in ENTRY.finditer(raw)}


def patch(raw, revisions):
    """Replace the text of every id in `revisions`.

    Returns (new_bytes, applied_ids, missing_ids).
    """
    applied = set()

    def sub(m):
        sid = m.group(1).decode()
        if sid not in revisions:
            return m.group(0)
        applied.add(sid)
        new = revisions[sid].encode(ENCODING, "replace")
        return b"{" + m.group(1) + b"}{" + m.group(2) + b"}{" + new + b"}"

    out = ENTRY.sub(sub, raw)
    return out, applied, set(revisions) - applied


def verify(path, revisions):
    """Read back off disk and confirm each revision is really present.

    Re-running the transform in memory proves the transform works, not that
    anything was written. This reads the file.
    """
    got = parse(open(path, "rb").read())
    return {sid: text for sid, text in revisions.items() if got.get(sid) != text}
