# Fallout English Localization

English localization for three *Fallout 2* total conversions:
**Resurrection**, **Nevada (Expansion Version)**, and **Sonora (Extended Release)**.

Download a game, double-click, play. No install step, no configuration, no
hunting for patches.

Grab a ready-to-play archive from **[Releases](../../releases)**, or apply the
patch to an install you already have with `install.py`.

Everything here is free, and free to pass on. See [CREDITS.md](CREDITS.md) --
this work sits on top of years of other people's, and they are why it exists.

---

## What it covers

| Area | Scope |
|---|---|
| **Dialogue** | 885 revised strings across 196 `.msg` files |
| **Premade characters** | 10 rewritten bios, 7 transliterated names |
| **Character sheet** | Appearance-mod UI — Nevada and Resurrection, 102 strings |
| **Outfit port** | 317 skull-jumpsuit sprites for Nevada *(see the note below)* |

## Install

Requires Python 3.8+. Nothing else.

```bash
python install.py --list
```

```bash
python install.py --all --dry-run
```

```bash
python install.py --all
```

Target one game, or one step at a time:

```bash
python install.py --game nevada --steps dialogue,premade
```

If your installs are somewhere other than `C:\`, pass `--path`:

```bash
python install.py --game sonora --path "D:\Games\Fallout Sonora"
```

## Build a ready-to-play folder

`bundle.py` assembles your own installs into a single self-contained folder --
games copied in, patch already applied, one launcher per game:

```bash
python bundle.py --out "C:\FalloutTrilogy-English"
```

```
FalloutTrilogy-English/
  START HERE.txt
  Play Resurrection.bat
  Play Nevada.bat
  Play Sonora.bat
  games/
```

About 4.8 GB and under a minute on an SSD. The bundle is **not** committed here
and cannot be: GitHub caps files at 100 MB and each `master.dat` is roughly
double that. The script ships; the bundle is something you build.

`release.py` then turns a bundle into one archive per game for distribution,
since GitHub Releases caps a single asset at 2 GB:

```bash
python release.py --bundle "C:\FalloutTrilogy-English" --out "C:\fallout-release"
```

## Uninstall

The installer records every path it touched in `.falloutloc-manifest.json` in
the install root. `revert.py` reads it, restores replaced files from their
`.orig` backup, and deletes the files that were created outright — most
dialogue overrides and every ported sprite have no previous version to restore.

```bash
python revert.py --all
```

Verified round trip: install then revert against a copy of a Resurrection
install returns every file to a byte-identical state.

## How it installs

Dialogue and premade characters are written as **loose files** under the game's
`data/` folder, which the engine loads ahead of `master.dat`. No large archive
is ever rebuilt — full recompression of a 198 MB archive is impractically slow.

The appearance-mod archives are small, and have no loose-file override path, so
those are **repacked surgically**: the changed `.msg` is recompressed and every
other entry keeps its original stored bytes, leaving the rebuild identical apart
from the replaced files and the shifted offsets.

Re-running the installer is safe. It always patches from the `.orig` backup when
one exists, so edits never stack.

## Verified state

`install.py --all --dry-run` against the three reference installs:

```
Nevada         dialogue 266 strings / 25 files   premade 3 bios, 3 names   appearance 51 / 10 archives   outfit 317 sprites
Resurrection   dialogue 100 strings / 17 files   premade 3 bios            appearance 51 / 10 archives
Sonora         dialogue 566 strings / 160 files  premade 4 bios, 4 names
```

**884 of the 885 revisions apply.** The one exception is `cmbatai2.msg` string
`32021` (`"Aaaargh!"`), which does not exist in any of the three installs —
only Nevada ships `cmbatai2.msg` at all, and its copy has no id `32021`. The
entry is retained in the source dictionary but has no target.

Per-game totals are the count of revisions that actually match a string in that
game's copy. Eight files (`misc`, `pipboy`, `quests`, `p_party_orders`,
`containr`, `cmbatai2`, `ecbandit`, `ecdogmet`) exist in more than one game, so
the per-game figures sum to more than 885.

## The outfit port, and permission

`data/outfit/sprites.txt` is a manifest of 317 **filenames**. The sprites
themselves are **Nevada Mod (Extended)'s artwork, not ours** — the installer
copies them out of your own copy of that mod and into your own Nevada install.

The art is Nevada Mod (Extended)'s author's work and is credited as such in
[CREDITS.md](CREDITS.md). `install.py` sources it from your own copy of that
mod; the release archives have it already applied.

Known gaps, investigated and accepted:

- 10 animations have no skull counterpart and still show the blue jumpsuit:
  `hmjmpsbe`, `bh`, `bj`, `bk` (weapon poses) and `bn`, `na`, `re`, `rh`, `rj`,
  `rk` (the death set plus one special).
- The appearance mod's seven alternate models (~1,155 sprites) wear blue
  full-time. No skull art exists for them anywhere.

The skull suit is not a palette recolor — 47.3% of pixels differ, 105 of 115
palette indices map to more than one target, and 6 of 30 frames differ in
dimensions. It is separately drawn art, so no mechanical transform closes the
gap. Only hand pixel-art would.

## Layout

```
install.py               apply the patch to an install
revert.py                restore from .orig backups
bundle.py                build a self-contained ready-to-play folder
release.py               split a bundle into per-game distributable archives
falloutloc/
  msg.py                 .msg parse / patch / verify
  gcd.py                 premade character name field
  games.py               install discovery, per-game facts
  manifest.py            record of what an install touched, for exact revert
  dat2.py                DAT2 read / extract / build
  dat_replace.py         surgical repack (untouched entries keep their bytes)
  classify.py            mojibake / hand-translation classifier
  steps/                 dialogue, premade, appearance, outfit
data/
  dialogue/              master_revisions.py + the 26 source batches
  premade/               bios (text) + names.json — no .GCD binaries shipped
  appearance/            extracted English UI strings
  outfit/sprites.txt     317 filenames, no art
  reference/             per-game string classification, batch plan
docs/
  FORMATS.md             file formats and the traps in them
  NOTES.md               project history and decisions
```

## Caveats

- Sonora's per-model appearance English is stock *Fallout 2* filler
  ("Generic Default Dude"), not a translation. It is deliberately not touched.
- Resurrection's character-sheet button reads "Close" where Nevada reads
  "Done". Deliberate — only Nevada's was in scope.
- `data/reference/art_port_list_interface.txt` is 103 **interface** sprites.
  It is kept for provenance and is unrelated to the 317-file outfit manifest,
  despite what earlier notes claimed.
- `data/reference/authored_*.json` is raw classifier output and contains
  mojibake tails. `data/dialogue/master_revisions.py` is the clean source of
  truth.

## Licence and credit

The tooling and the English text here are MIT, see [LICENSE](LICENSE). Take it,
change it, pass it on.

The games, the engine and the ported art belong to the people who made them,
listed in [CREDITS.md](CREDITS.md). Credit them.
