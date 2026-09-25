# 0023 - whether a filename is personal data

## Status

`accepted` - 2026-09-24

**ACCEPTED BY ADJUDICATOR RULING 2026-09-24**, session 113, on CS-1158. The ruling was
made by an agent that authored none of the slice, which is the condition `CLAUDE.md`
section 5 puts on grading; the builder that wrote this file did not grade it. The
question is RATIFIED rather than newly decided - shipped code already answered it, as the
Context records.

This ADR is IN FORCE and binding. Cite it freely.

## Context

`CLAUDE.md` section 2 classifies the account id, the world name, the Windows account name
and any absolute path under a home directory as personal data, and keeps every one of
them out of a tracked file, a commit message and a log; non-negotiable 3 forbids
hardcoding them. Section 3 adds the player display name, through non-negotiables 11 and
12, and makes every rendered output an echo path.
What none of those rules says, in either direction, is whether a FILENAME is personal data
in its own right. The question became load-bearing under CS-1155: the directory walk in
`tools/drift_guard.py` began pruning save files, logs and credential files by the shapes
in `WALK_SKIP_FILE_PATTERNS`, and every pruned path was appended to a skip record that
`_skip_lines` prints on every run and `--json` serialises whole. An adjudicator measured a
synthetic tree's save filename rendering under the `PII-bearing` heading. Pruning stopped
the CONTENT being read; the NAME is a separate surface.

**THE QUESTION WAS ALREADY ANSWERED IN SHIPPED CODE.** `clockspeed/data/locate.py::redact`
strips "the save filename that carries the world name" from anything about to be printed
or raised, and its module docstring lists the world name beside the account id as data
that must never be printed raw. A save filename carries the world name, so it is a value
in a section 2 class. An ADR answering NO would contradict code this repository already
ships and relies on.

**THE ALTERNATIVES, AND WHAT EACH COST.**

- *Answer NO - a filename is metadata, not data.* Rejected: it contradicts
  `clockspeed/data/locate.py::redact`, and it would make a save filename printable
  anywhere, which re-opens the world name to every log line section 2 closes.
- *Answer by a LIST of paths or a name regex - redact `*.sav` and whatever else is
  written down.* Rejected: that is a denylist, and a denylist leaks the next shape nobody
  listed. The class of the THING is what makes a name sensitive, not its spelling.
- *Mask the leaf - print a prefix, a truncation or a hash of it.* Rejected: world names
  are low-entropy, so a digest is confirmed by guessing and remains an identifier; a
  masked leaf is the same leak at lower resolution.
- *Drop withheld records entirely.* Rejected: `CONVENTIONS.md` section 15.1 names a guard
  that is green while self-excusing as a failure class. A verdict needs the list of what
  was never looked at, so the COUNT must survive the redaction.

## Decision

A filename CAN be personal data, and the rule is stated by REASON CLASS, never by a list
of paths:

1. **A path component IS personal data when it is, contains, or is derived from a value
   in a `CLAUDE.md` section 2 or non-negotiable 3 class** - the account id, the world
   name, the Windows account name, the player display name, or a home directory. A save
   filename is therefore personal data, because it carries the world name.
2. **Every path under a directory named for the player is personal data IN WHOLE,
   whatever its leaf**, because the parent component names the account.
3. **A name that LOCATES an artifact skipped BECAUSE its contents are PII-bearing or
   credential-bearing is withheld from rendered output, even when the name alone is
   innocuous.** Non-negotiable 12 makes rendered output an echo path, and the reason a
   record carries is what says the artifact is sensitive - so the reason decides, not the
   spelling.
4. **The withheld form is the reason plus a count** - no leaf, no masked leaf, no hash.
   The count stays, per `CONVENTIONS.md` section 15.1.
5. **Not personal data: a fixed name this repository chose itself** - for example
   `ops/loop/config.json` or a `*.local.json` override - when it is skipped for a reason
   outside the two withheld classes. Those names render, and they serve as the control
   that proves the renderer still prints paths at all.

## Consequences

- **The directory named for the player.** The save directory's account subdirectory is a
  platform account id (`CLAUDE.md` section 2), so every path beneath it - every save,
  every autosave, every backup, whatever its leaf - is personal data under rule 2. No
  renderer, log line, fixture, test id or skip record may carry such a path in any form
  that names a component below the save root. `clockspeed/data/locate.py::redact` already
  tokenises that component by position; this ADR makes that behaviour a rule rather than
  an implementation detail.
- **CS-1158 must make `tools/drift_guard.py` withhold by reason class:** a skip record
  whose reason is in the `PII-bearing` or `credential material` class renders as its
  reason and a count, in both the text report and the `--json` payload. A new table entry
  in either class joins the withheld set by its reason alone, with no second list to
  update.
- **A generic reason cannot carry this rule, so no path is left under one when a class
  applies.** AMENDED 2026-09-25 under CS-1158, after an adversary refuted the first
  change: a path skipped only because git ignores it carried no class, and three leaks
  followed. The rule is closed in the same item rather than deferred, three ways:
  - **The class comes from `.gitignore`, where it is declared.** A pattern `.gitignore`
    files under its `PII-BEARING` banner gives the path a `PII-bearing` reason, matched
    case-insensitively as git does on this platform, so a rotated or upper-cased save
    shape is not left to a floor that restated one spelling of it. A pruned root that
    `.gitignore` files as PII-bearing carries a PII-bearing reason in the walk's table
    too, and a test holds the two in agreement.
  - **A directory git collapses to one ignored entry is withheld when it holds a
    PII-bearing or credential file anywhere beneath it** - it locates one, so rule 3
    applies to its name.
  - **Rule 2 is enforced by shape at the render seam.** A skip record whose path has a
    component shaped like a platform account id - the digit-run floor
    `clockspeed/data/locate.py::redact` already uses - is withheld whatever it was
    skipped for, and counted under its own reason. This is the one shape test, and it
    is the account-id classification itself, not a list of names.
  **Still not closed, stated rather than implied:** a directory named for the player by a
  NON-numeric name - a world name, a hex or GUID account token - holding no withheld-class
  file is indistinguishable by name from any other directory, and renders.
- **Any other renderer found printing a withheld-class name is a new item**, not a fix
  folded into the change that found it.
- **Harder:** a reader debugging a pruned save or key file cannot learn WHICH file from
  the report. That is the intended cost; the file is on the reader's own disk.
- **Revisit if** the classification in `CLAUDE.md` section 2 changes, or if a reason
  class is added beside `PII-bearing` and `credential material` that also marks content
  as sensitive - that class joins the withheld set by amending this ADR.
