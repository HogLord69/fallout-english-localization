# File formats, and the traps in them

Each of these cost real time to find. They are written down so they cost it once.

## `.msg` — dialogue and UI strings

The format is:

```
{100}{}{You see a Mexican with long hair.}
{101}{}{I take it back.}
```

**It is `{id}{}{text}`, not `id=text`.** An installer written against `id=text`
matches nothing, changes nothing, and reports success — there is no error to
notice. This is the single most expensive mistake in this project.

The middle group is an optional audio filename and is almost always empty. It
must be preserved: `falloutloc/msg.py` substitutes only the third group and
leaves every other byte — comments, blank lines, line endings, untouched
strings — exactly as it found them.

Encoding is a single-byte codepage. English text is ASCII, so `cp1252` round
trips safely.

### Overrides must mirror the archive path

Dialogue files do not sit at the root of the text folder. They live under
`dialog\` or `game\`:

```
text\english\dialog\ABRADSNE.MSG
text\english\game\CMBATAI2.MSG
```

A loose override only wins if its path mirrors that, so
`data/text/english/dialog/ABRADSNE.MSG` works and a flat
`data/text/english/ABRADSNE.MSG` is silently ignored by the engine.

### Sonora's archive is Russian-only

| Game | `text\` roots in `master.dat` |
|---|---|
| Resurrection | `english` (629 files) |
| Nevada | `english` (947 files) |
| **Sonora** | **`russian` only (978 files)** |

Indexing by basename and taking the first hit will happily write English
revisions into `text\russian\`. The **source** may be Russian; the **target**
is always `data/text/english/`, with the subfolder preserved.

## DAT2 — the archive format

Trailer-indexed. The last 8 bytes are `<tree_size:u32><data_size:u32>`; the
tree sits immediately before them. Each entry is
`<name_len:u32><name><type:u8><real:u32><packed:u32><offset:u32>`, where type 1
means zlib-compressed.

`falloutloc/dat2.py` reads, extracts and builds. `falloutloc/dat_replace.py`
does the surgical variant: untouched entries keep their **original stored
bytes** with no recompression, so a rebuild differs only in the replaced files
and the offsets that shift after them.

**Do not rebuild `master.dat`.** Full recompression of a 198 MB archive is far
too slow to be practical. Use loose-file overrides for anything under `data/`,
and reserve surgical repack for small archives like the appearance mod's.

### Case

Sonora and Resurrection ship `.DAT`; Nevada ships `.dat`. A `*.dat` glob
silently skips half the archives on a case-sensitive filesystem. Match
case-insensitively, always.

Resurrection also ships a **0-byte `fores.dat`** placeholder, which is not a
DAT2 file at all. Skip zero-length archives before parsing.

## `.GCD` — premade characters

432 bytes. The display name is a fixed **32-byte, null-padded field at offset
`0x0174`**. Only that field is touched; stats, skills, traits and perks are
left byte-for-byte alone.

Because only one field changes, this repository ships the **names**
(`data/premade/names.json`) rather than the `.GCD` files, and the installer
patches the user's own copy.

## `.BIO` — premade character biographies

Plain text, and **the engine does not word-wrap it.** Text is hard-wrapped by
hand to:

- at most **20 characters** per line
- at most **22 lines**

A trailing newline terminates the last line; it does not add one. Counting
`split("\n")` without stripping it reports 23 lines for a valid 22-line bio.
`falloutloc/steps/premade.py:check_bio` enforces both limits before writing.

## Verification

Re-running a transform in memory proves the transform works. It does not prove
anything reached the disk. `msg.verify()` re-reads the written file and
compares, and every install step reports what actually landed rather than what
was attempted.
