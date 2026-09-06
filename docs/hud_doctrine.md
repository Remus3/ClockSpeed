# Clockspeed - HUD doctrine for the companion and the overlay

**Section status: LIVE.** A dated heading in this file records provenance - when the text
was filed, adapted or measured - and never that the section itself is historical.

**Owner file for:** the operating law of the two user-facing surfaces, the companion
dashboard and the in-game overlay. What each is for, what may be encoded in which channel,
and which of this repository's existing arms an overlay will collide with.

**This file never contains:** palette VALUES - `clockspeed/surface/web/app.css` owns those
and they are measured there - nor build detail, nor open work. Open work lives in
`ROADMAP.md`.

---

## Provenance, filed 2026-09-05

**ADAPTED, NOT LIFTED.** The operator supplied a UI/UX doctrine from a different project on
this machine - a companion-plus-overlay pair for a competitive game. It is tailored to that
project. This file keeps what transfers, records what does not, and names the collisions.
Where the two disagree, this repository's settled decisions win, because the other project
does not share this one's licence, its zero-language-model rule, or its arms.

Two of its laws arrived at conclusions this project reached independently on the same day,
which is the reason to take the rest of it seriously: **no colour literal outside one
table**, and a five-phase audit ritual whose phases are the five in `CONVENTIONS.md`
section 13.2.

---

## 1. The two surfaces are not the same surface

`CLAUDE.md` already settles the shape: the companion window ships in v1, and the in-game
overlay is a later flagged mode of the same shell, default off, degrading to the companion
on bind failure. This file adds what each surface is FOR.

- **The companion** is read at leisure, out of game, on its own ground. It may use text
  freely, may scroll, and may ask the reader to look for more than a moment.
- **The overlay** is read in one glance while the reader is doing something else, over a
  ground this project does not control and cannot sample. Everything it paints competes
  with the game.

**A one-line rule that follows:** the companion may spend the reader's attention; the
overlay may only borrow it.

---

## 2. What transfers unchanged

- **One primary element, two or three supporting, and nothing else persistent.** More than
  that and the reader has to search rather than glance.
- **Exactly one pop-out at any instant.** If two things are the only red thing, neither is.
  This binds `--status-starved` in particular: it is the loudest colour in the palette and
  a screen carrying three of them carries none.
- **Fixed, learnable positions beat smart-but-moving.** The reader drags once, it saves, it
  never moves itself.
- **Quantities as bar length or position; categories as colour.** Never magnitude in hue.
- **Never obstruct the centre, and never require a dismissal mid-task.** An alert that must
  be clicked away is an alert that will be clicked away at the wrong moment.
- **No reflow when data is absent.** Reserve the slot and render a dim sentinel; a layout
  that jumps moves the reader's muscle-memory targets. The dashboard's "reading ..." rows
  already do this - the rule is stated here because it was previously only a habit.
- **Every renderer idempotent.** The page repaints wholesale today, which is correct for a
  button-driven dashboard and becomes a flicker bug the moment anything polls.

---

## 3. What does NOT transfer, and why

- **The palette values.** The source doctrine's palette is another game's brand. This
  project's palette is measured in `clockspeed/surface/web/app.css` against this page's own
  grounds, in both schemes, and is not up for substitution by a table from elsewhere.
- **"Preattentive only, no text to read".** Correct for a five-second teamfight; it would
  forbid this project's entire product, which is one line of terse advice. The adaptation:
  the verb stays text, and preattentive encoding carries STATUS only. Colour is the second
  channel and never the first - `.hud-status` writes the state as text in the same colour
  the border uses, so the border alone never carries it.

**A colour-channel conflict to settle before the overlay is built.** The game gives every
item its own colour. If a throughput readout is tinted by its item's colour, then colour is
already spent encoding IDENTITY, and production status wants the same channel. Two category
axes, one channel. This project has already had to separate two such axes once - the
endpoint-status pills and the production-status tokens are deliberately different
vocabularies - and a third contender needs the same treatment rather than a merge.

**An accent question the environment raises.** The game's world is warm; a sunset biome is
magenta and coral. An industrial-orange accent sits inside that hue family, so what reads
as a strong accent on the companion's dark slate may read as camouflage over the game.
Whether the overlay keeps the companion's accent or takes a cool one is unresolved and
should be measured against real frames rather than argued.

---

## 4. The arms an overlay will collide with

Each of these is a shipped, enforced test. None of them is wrong; each was written about
the DASHBOARD and will need scoping rather than deleting.

- `tests/surface/test_web_assets.py::test_the_page_repaints_on_a_button_and_never_on_a_timer`
  An overlay cannot be refresh-button-driven. The arm's stated reason - "a timer-rebuilt
  panel becomes mouse-only, invisibly" - is a claim about a POINTER surface, and a
  click-through overlay has none, so the reason does not reach it.
- `tests/surface/test_web_assets.py::test_the_page_offers_exactly_one_kind_of_clickable_target`
  A draggable widget body is a second interaction model this bans outright.
- `tests/surface/test_web_assets.py::test_every_asset_byte_is_seven_bit_ascii`
  The source doctrine carves out functional glyphs as code rather than punctuation.
  Non-negotiable 4 has no such carve-out, and the CSP publishes no `img-src`, so an overlay
  today may use neither a glyph nor an image. **Text only, or an operator ruling.**

---

## 5. Traps measured elsewhere that this project has not yet paid for

Recorded so they are not re-derived. None has been reproduced here.

- A global shortcut registered by the shell is not delivered while the game holds the
  foreground; the working shape was an OS-level hotkey writing a stamp file that the shell
  polls.
- Synthesised keys leak into the game.
- A mixed-content request from an HTTPS origin can abort boot before any fallback runs.
  This surface is HTTPS with a pinned self-signed certificate, so the shape applies
  directly - and a loopback address is exempt from the rule that catches it, which means
  testing on loopback MASKS it.
- A layered click-through window is not captured by an ordinary screen grab.
- Absolute pixel placement authored at one resolution lands wrong at another; position by
  window fraction.
- The game must be in borderless mode; exclusive fullscreen hides an overlay entirely.

---

## 6. Open, and deliberately not decided here

- The accent question in section 3.
- The colour-channel conflict in section 3.
- Whether overlay tokens live in their own sheet rather than as redefinitions of `:root` on
  one element. The source doctrine scopes them separately and never puts them on `:root`,
  which would structurally prevent the fault seven audit rounds chased in this repository.
  It is the better shape IF the overlay is a separate document, which a flagged mode would
  make it. That is an ADR when the overlay is built, not a change to make now.
