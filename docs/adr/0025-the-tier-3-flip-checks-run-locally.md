# 0025 - the tier-3 flip checks run locally

## Status

`accepted` - 2026-09-25

**ACCEPTED BY ADJUDICATOR RULING 2026-09-25**, session 113, ruling D-T3 on CS-1183. The
ruling was made by an agent that authored none of the slice that wrote this file, which is
the condition `CLAUDE.md` section 5 puts on grading. The decision text below is the
ruling's, recorded here rather than re-argued.

This ADR is IN FORCE and binding. Cite it freely.

## Context

**THE ITEM.** CS-1183's acceptance permits either shape - "CI workflow_dispatch or a tools
script" - for one manually dispatched entry point that runs the seven `CONVENTIONS.md`
section 17 flip checks against a named ref, and it adds the CS-1180 trailer axis because
the entry point is the S1/S8 executor of the CS-700 plan. So the shape had to be chosen
before any code existed.

**WHAT DECIDED IT - WHERE THE NEEDLES LIVE.** Check 2 is the PII scan. Its needles are the
platform account id, the Windows account name, the machine name, absolute home paths, and
the display name and account id decoded out of a save header (`BOOTSTRAP.md` section 2.2).
Every one of them is derived from THIS machine: the account directory from
`clockspeed/data/locate.py`, the decoded header strings from
`clockspeed/save/header.py::reveal_strings` behind its explicit opt-in. A CI runner holds
none of them. A CI job could run check 2 only if the needles were uploaded as repository
secrets - and that uploads exactly the personal data the check exists to keep off the
forge, breaking the Local property in `CLAUDE.md` section 1.

**THE ALTERNATIVES, AND WHAT EACH COST.**

- **A `workflow_dispatch` job - the runner-up.** Its best argument: a runner is independent
  of this box's state, and a run leaves an auditable record on the forge. It LOST for three
  reasons. The needle source exists only here. The independence it offers is exactly what
  check 7's human half - a machine that has never seen the project - supplies properly,
  and a runner is not that machine, because the workflow itself supplies the interpreter
  and the toolchain (the `clean-checkout-probe` job in `.github/workflows/tier2.yml` says
  so of itself). And a run record on the forge is not what clears the gate - see decision
  item 8.
- **A hybrid - CI for checks 1, 3, 4 and 6, local for 2.** It breaks the acceptance's "one
  entry point", and it produces two verdicts that can disagree about one ref.

**THE FENCES CHECKED.** No `CLAUDE.md` section 7 Settled entry and no `BOOTSTRAP.md`
section 11 entry covers the tier-3 executor. Two spec wordings do conflict with this
decision. `CONVENTIONS.md` section 17 says "(CI tier 3)", but its own section 8 already
labels tier 3 "manual, pre-flip", so this ADR reads "CI tier 3" as NAMING THE TIER, not the
executor. `CONVENTIONS.md` is portable doctrine and is NOT edited. `BOOTSTRAP.md` section
2.2 says "tier-3 CI PII scan patterns"; that wording IS amended, under `CLAUDE.md` section
8, with a ledger record.

**THE WARNING THIS HAS TO ANSWER.** The tier-3 tail comment in
`.github/workflows/tier2.yml` said there was no tier-3 job on purpose, because a job built
early invites being run, passed synthetically and treated as satisfied. Decision items 7
and 8 are the answer: a green run of the tool is never the gate clearing.

## Decision

1. **ONE ENTRY POINT, `python tools/flip_checks.py <ref>`, run by hand on this machine.** No
   workflow, hook, scheduled task or lane invokes it, and no tier-3 workflow file (a
   `tier3.yml` beside `tier2.yml`) exists. "Never runs on push" holds by construction, and an arm pins that no workflow or
   hook names the tool.
2. **`<ref>` IS REQUIRED.** It is resolved once to a full SHA, which is printed first. Every
   check's population is that ref's tree and its reachable history - never the working
   tree, the index or other refs. An unresolvable ref exits 2.
3. **NEEDLES ARE DERIVED IN-PROCESS AT RUN TIME** from `clockspeed/data/locate.py` and
   `clockspeed/save/header.py::reveal_strings`, with its explicit opt-in used at the render
   site only. A needle is never written to disk. It never reaches a log, an exception, an
   assertion message or a test id, and no NEEDLE ever enters a child process's argv or
   environment. A child's argv[0] may carry the interpreter's own path, which can sit
   under a home directory, and a child inherits the operator's environment unchanged;
   the tool never renders an argv, a child's output or a child's stderr, and no
   traceback is ever rendered - the last-resort handler prints the phase and the
   exception's type only. Matching is done in-process over `git cat-file --batch`
   output, or a needle goes to a child on stdin. Output is counts, commit SHAs and blob
   SHAs only.

   *Amended 2026-09-25, before merge, after the adversary pass on CS-1183: the first text
   said "never a child process's argv", which the interpreter path in argv[0]
   contradicted. The rule was always about needles; the wording now says so.*
4. **A NEEDLE SOURCE THAT DOES NOT RESOLVE FAILS CHECK 2.** It is never a skip, because a
   PII scan with no needles is vacuous.
5. **EVERY CHECK CARRIES A POSITIVE CONTROL** in its own command family: a planted hit in a
   throwaway repository in a temp directory, found by the same code path. A control that
   is not found fails the run. Every check reports its skip count, and any skip in an
   automated half fails the run.
6. **CHECKS 5 AND 7 run their automatable halves**, each with a control. Their human halves
   are reported as NOT-RUN-HERE, citing CS-1186 and CS-1187 or the gated successor,
   CS-G08 - never as PASS.
7. **EXIT CODES:** 0 only when every automated half passed, every control was found and
   there were zero automated skips. 1 on any failure or missing control. 2 when the run
   could not run, including any exception no check absorbed. 130 on an interrupt. The final line is NEVER a bare PASS. It states the automated verdict,
   the number of human halves NOT-RUN-HERE, and that this run does not clear CS-G03.
8. **CS-G03 CLEARS ONLY on an adjudicated `docs/LEDGER.md` record at the flip SHA.** That
   record must cite a run of this tool at that SHA plus the recorded human-half walks. An
   exit of 0 alone never clears it. This is the answer to the tier-2 tail comment's warning
   that an early tier-3 job invites synthetic satisfaction.
9. **The tool includes the CS-1180 trailer axis** through `tools/trailer_census.py`, the
   S1/S8 executor.
10. **CHECK 6 PINS TWO EXACT URL SETS AND NOTHING ELSE.** Added 2026-09-25 by the wave-3
    closing adjudicator, before merge.
    a. `NO_FETCH_PINNED`: the exact set of distinct URLs on a doc_sweep no-fetch host that
       the swept tree may carry. Today it holds one member, the wiki.gg Copyrights page URL
       cited in `docs/LEDGER.md` under CS-485. PERMANENT - CS-485 forbids any automated
       fetch, a one-off included - so it holds at S1, at S8 and after the flip. A pinned
       URL is reported "policy-excluded", never "passed", and is not counted in the
       automated skip count of points 5 and 7.
    b. `PRE_PUBLICATION_DEAD`: the exact set of distinct own-repository URLs that 404
       because the repository is not public. Today: the README tier1 workflow page and its
       badge.svg, both on `README.md`. It excuses a 404 ONLY while an unauthenticated GET
       of the repository's own root URL also answers 404, measured in the same run. When
       the repository answers publicly, the pin is inert and a 404 on either URL FAILS. So
       the pin expires by itself at publication and nobody has to remember to drop it. It
       is deleted from the tool in the first commit after S12.
    c. MATCHED BY URL, NEVER BY COUNT. Check 6 knows every skipped and every dead URL by
       identity. It FAILS on: any skipped or dead URL outside its pin; any skip kind other
       than no-fetch-host; any pinned URL no longer found in the tree (a stale pin); any
       `PRE_PUBLICATION_DEAD` URL answering other than 404 or 200.
    d. REPORTED, NEVER SILENT. The check line prints policy-excluded N and
       pre-publication-dead N, apart from skips and findings. Point 7's final line names
       both counts. Point 8's flip record cites the post-S12 re-run in which
       pre-publication-dead is 0.

    *Amended 2026-10-20 by CS-700: point 10b was executed in the first commit after S12, the
    S12a act (ii) ledger commit of 2026-10-18, which deleted `PRE_PUBLICATION_DEAD` and its
    excuse path from `tools/flip_checks.py` (`docs/LEDGER.md`, the 2026-10-18 record "ADR 0025
    point 10b executed"). Check 6 now pins ONE exact URL set, 10a's, so every dead URL FAILS,
    README's tier1 badge included. 10c's last clause, on a `PRE_PUBLICATION_DEAD` URL
    answering other than 404 or 200, lapsed with it, and so did 10d's pre-publication-dead
    count and its term in point 7's final line. The post-S12 re-run that 10d names for point
    8's flip record is the A-S12a step 5 reading at T2, in that same ledger record, which read
    pre-publication-dead 0.*

    *Amended 2026-10-20 by CS-1332, in the fix shape the CS-700 S8 ruling ordered: check 6
    pins the exact URL set of 10a, 10b's having been deleted after S12 as it ordered, and ONE
    EXACT BINARY SET, and nothing else. A file doc_sweep's own reader returns nothing for is
    learned by path, never by count, and is excused only when its path AND the SHA-256 of its
    bytes match a pin in the ref's `tools/sha_citation_binaries.json`, matched by
    `tools/sha_citation_gate.py`'s own `is_known_binary`. It is reported known-binary on the
    check line, never a skip, and is not counted in points 5 and 7. 10c also FAILS on: any
    unreadable-or-binary-file skip no pin excuses; any unread markdown file; a pinned path
    whose bytes drifted; a pin source that cannot be read or trusted; a pin source with a
    repeated key; an unread count the learned paths do not match.*

## Consequences

- **Easier:** the seven checks exist as one runnable job long before the flip, which is
  CS-G03's PREP half, and the PII needles never leave this machine to make that possible.
- **Harder:** there is no forge-side record of a run. The record is the adjudicated ledger
  entry of decision item 8, which is stricter than a run log, not weaker.
- **Foreclosed:** a tier-3 workflow of any trigger, repository secrets holding PII needles,
  and a hybrid split of the checks across two executors. Re-opening any of them needs a
  new ADR that answers the needle-source argument above.
- **Follow-on edits, owned by the merger, not this file:** the tier-3 tail comment in
  `.github/workflows/tier2.yml` is replaced with text pointing here; `BOOTSTRAP.md` section
  2.2's "tier-3 CI PII scan patterns" becomes "tier-3 PII scan patterns (run locally - ADR
  0025)" with a `docs/LEDGER.md` record; and this ADR is indexed in `docs/adr/README.md`.
  No tier-3 workflow file is created.
- **Revisit if** a needle source that is not machine-local becomes the whole of check 2 -
  then the needle-source argument no longer holds and the runner-up's independence argument
  should be weighed again.
