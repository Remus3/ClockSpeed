# 0012 - The dashboard's refusal vocabulary and its exact-rational wire form

## Status

`accepted` - 2026-08-29

## Context

`BOOTSTRAP.md` section 7.1 names nine endpoints. Four of them have a layer beneath them
today - `clockspeed/save/` and `clockspeed/solve/` both ship - and five sit on
`clockspeed/advisor/`, `clockspeed/audit/` and `clockspeed/progress/`, which currently
hold a package docstring and nothing else. A surface that ships before those five exist
has to say something honest about each, and there are four ways it could have gone wrong.

**Two absences look the same from the outside.** "Pillar 3 has not been written" and
"there is no game installed on this machine, so there is no registry" are both a request
that produced no data. Rendering them identically - as one 503, or as one 501, or as a
200 carrying an empty list - teaches an operator that a refusal means nothing and to stop
reading it. Only one of them has a remedy the operator can act on, and only one of them
will stop being true when work lands.

**A refusal wants to explain itself, and the explanation is where personal data leaks.**
The natural spelling of a detail line interpolates what was refused. On this machine the
things being refused are a save path under a numeric platform account directory, a world
name the operator chose, and an install path containing the Windows account name -
non-negotiable 3 and non-negotiable 12. An error body is an echo path exactly like a log
line or a hex dump.

**JSON has one number type and it is an IEEE double.** Non-negotiable 6 requires exact
rational arithmetic in the solve path and asserts the absence of floats. A rate that is
exact as a `Fraction` all the way through `clockspeed/solve/` and is then written into a
response as a bare JSON number has been silently converted at the last hop, by the
serializer, where no test in the solve layer is looking. The dashboard is what a person
reads the number off.

**`/api/world` was genuinely ambiguous.** CS-400 is open, so a reading exists under which
the whole save layer is unfinished and `/api/world` should refuse with a 501 naming it.
That reading was put to an adjudicator this session and rejected.

## Decision

**The 501/503 split is load-bearing and does not collapse.** `501` says the layer beneath
does not exist yet, and it is REQUIRED to name the open item that would build it. `503`
says the layer exists and its input is absent on this machine. A 501 with no `blocked_by`
is a contract violation; a `blocked_by` on anything other than a 501 is too.

**A 501 cannot outlive its reason.** `blocked_by` is validated for the `CS-nnn` form and
for membership in a closed set this repository authors, and that set is pinned to the OPEN
item lines of `ROADMAP.md` by a test. When the named item closes and its line leaves the
roadmap, the arm goes red and the refusal has to be revisited.

**`detail` is looked up by reason code and is never built from content.** Every line comes
whole out of one table keyed by a closed vocabulary. The contract module holds no
f-string, no `str.format` call and no percent-formatting anywhere, so there is no
interpolation site for a save path or a world name to land in - and that is asserted on
the module's AST rather than promised in prose.

**An exact ratio goes on the wire as `{"num": <numerator>, "den": <denominator>}`.** A
bare JSON number is forbidden: the encoder walks the payload to any depth, keys included,
and raises rather than emitting a float. The renderer transcribes and does not divide,
which is asserted by showing its body holds no binary operation at all.

**`/api/world` is BACKED. It answers 200 or 503, never 501.** CS-400 is open on DEPTH, not
on coverage: `docs/item_notes/phase4.md` records the session-6 ruling that "phase 4 can
now enumerate a world but not inspect it", and the clauses still outstanding are
inventory, clock speed and connection state. `/api/world` serves enumeration only and
touches none of the three. A 501 there would be a false statement about a shipped layer of
roughly eleven thousand lines, and there is no honest `blocked_by` for it - CS-400 does
not block what `/api/world` actually serves.

## Consequences

- The five unbuilt endpoints all name one blocking item rather than one each. A single
  phase gate is what actually blocks them; naming a different item on each would imply
  five independent unlocks and would be four claims this repository cannot support.
- Moving an endpoint out of the unbuilt half is a deliberate edit to a declared literal in
  `tests/surface/test_acceptance.py`, not a silent change of behaviour. That arm goes red
  when a layer becomes real, which is the intended signal.
- Every endpoint that renders a rate must call the rational renderer. A new endpoint that
  forgets fails at encode time rather than shipping a rounded number, so the failure is
  loud and local.
- A reason code cannot be added by writing a detail line at the call site. Adding one is
  an edit to the published table, which is where the closed vocabulary is enforceable.
- **If `/api/world` is ever extended past enumeration** - inventory, clock speed or
  connection state - the premise of the ruling above changes and the endpoint's status has
  to be re-decided rather than inherited. Extending it is what would make CS-400's open
  clauses reachable from the wire, and only then would a refusal be honest.
- Because `detail` cannot be built from content, a refusal can never say WHICH value it
  refused. That is a deliberate loss of diagnostic precision, paid once, in exchange for
  there being no interpolation site at all. A debugging session that needs the value reads
  it from the request it made, not from the answer.
