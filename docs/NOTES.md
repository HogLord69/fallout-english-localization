# Project notes

Background and decisions behind the contents of this repository. For file
formats and their pitfalls see [FORMATS.md](FORMATS.md).

## Reference installs

The work was developed against these, all on one Windows machine:

| Game | Path |
|---|---|
| Resurrection | `C:\Fallout Resurrection (FE)` |
| Nevada (Expansion Version) | `C:\Fallout Nevada (Expansion Version)` |
| Sonora (Extended Release) | `C:\Fallout Sonora (Extended Release)` |
| Sonora, second install | `F:\Fallout Sonora (Extended Release)` |
| Nevada Mod (Extended) | `C:\Nevada Mod (Extended)` — art source only, never patched |

The two Sonora installs are different builds; their `master.dat` files differ by
about 38 KB. Both were patched.

`C:\Fallout Sonora (Extended Release)\master.dat.backup` is **truncated** — 191
MB against the real 198 MB, left over from an interrupted copy. Do not restore
from it.

## Ownership of dialogue files is resolved at install time

The `GAME` labels in `data/dialogue/batches/b*.py` are **wrong** and are kept
only as provenance. Nothing reads them.

Instead the installer asks each install which `.msg` files it actually contains
and patches only those. This is why the same revision dictionary can be pointed
at all three games without a hand-maintained ownership table, and why the eight
shared files get patched correctly in each game that has them.

Measured distribution: Sonora 160 files, Nevada 25, Resurrection 17, with eight
files (`misc`, `pipboy`, `quests`, `p_party_orders`, `containr`, `cmbatai2`,
`ecbandit`, `ecdogmet`) appearing in more than one game.

## Why the repository ships text, not files

Three of the four areas could have been shipped as finished game files. They are
not, for two reasons: the patched files are tens of megabytes of binary that
version control cannot show a useful diff of, and they are derived from
copyrighted work.

So:

- **Dialogue** ships as the revision dictionary; the installer rebuilds each
  `.msg` from the user's own copy.
- **Premade bios** ship as text, because they were written from scratch.
- **Premade names** ship as `names.json` and are patched into the user's own
  `.GCD` — the binary is not redistributed.
- **Appearance strings** were extracted back out of the patched archives into
  `data/appearance/appearance_en.json`, so the archives themselves need not ship.
- **Outfit sprites** ship as a manifest of filenames only. See the README.

## Scope decisions

- Sonora's per-model appearance text is stock *Fallout 2* filler ("Generic
  Default Dude"), not a translation. It was deliberately left alone rather than
  propagated.
- Nevada's Vault-13 jumpsuit joke is preserved in every style description.
- Resurrection's character-sheet button still reads "Close" where Nevada now
  reads "Done". Only Nevada's was in scope.
- The dialogue revisions were originally produced without being asked for, and
  were kept by explicit decision.

## Corrections to earlier notes

Two claims in the earlier handoff did not survive checking:

1. `art_port_list.txt` was described as "the 317 ported sprite names". It is
   actually 103 **interface** sprite paths (`art/intrface/*.frm`) and has
   nothing to do with the outfit port. It is preserved as
   `data/reference/art_port_list_interface.txt`; the real 317-file manifest was
   regenerated from the installed sprite set.

2. All 885 revisions were reported as verified present. In fact **884** apply —
   `cmbatai2.msg` string `32021` (`"Aaaargh!"`) has no target in any of the
   three games. Only Nevada ships `cmbatai2.msg`, and its copy has no such id.

## Reverting by hand

If `revert.py` is unavailable, the manual equivalents are:

- Dialogue and premades — restore the `.orig` beside each file.
- Character sheet — restore `appearance/*.dat.orig`.
- Outfit — delete `Fallout Nevada (Expansion Version)/data/art/critters/`.
