#!/usr/bin/env python3
"""CS-205 - no tracked module renders a caught exception OBJECT into a message.

THE LEAK CLASS. `str()` on an OSError appends the filename the call failed on -
"[Errno 2] No such file or directory: '<a path>'" - and on this project every
path is discovered at runtime and routinely sits under a home directory, so it
carries the Windows account name. CLAUDE.md non-negotiable 12 counts an error
message as an echo path exactly like a debug dump or a hex preview. Rendering
the exception OBJECT is therefore a privacy defect; rendering a named FIELD of
it that is known to hold a reason is not.

WHY THIS IS MECHANIZED RATHER THAN A LIST. CS-202 closed this class in two
files and recorded a hand-written instance set for the rest. That set was
already STALE by the time CS-205 was worked - the roadmap named four files and
an independent AST sweep found a fifth. A hand-listed acceptance goes stale
between being written and being worked, every time. So the acceptance here
ENUMERATES: `git ls-files "*.py"`, parse each, walk the AST. Adding a leaky
module cannot escape this test by not being on a list, because there is no
list.

WHAT COUNTS AS A RENDERING. Inside an `except ... as NAME:` handler, the bound
exception is flagged when it appears as a whole object in:

    f"{NAME}", f"{NAME!r}", f"{NAME!s}", f"{NAME!a}"
    str(NAME), repr(NAME), ascii(NAME), format(NAME)
    "...".format(NAME)          positionally or as a keyword value
    "..." % NAME                bare or inside the right-hand tuple
    getattr(NAME, "field", NAME)    the object as the FALLBACK

The formatting SYNTAX is irrelevant and all of these leak identically - the
fix is at the value, not at the format string. The last shape is the subtle
one and it is a real site in this tree: `getattr(exc, "problem", exc)` reads
like a field access and silently renders the whole object whenever the field
is absent. A detector that understands fields but not defaults waves it
through.

THE SAME LEAK ONE CALL DEEPER (CS-441). A helper that RECEIVES the exception
as a parameter gets the object intact, so `str()` there appends the very same
filename it would have appended inside the handler. Until CS-441 the detector
bound names only at `except ... as NAME`, and this module asserted that a
parameter-taking helper was "the sanctioned boundary" - a sentence true of the
one helper its author had in mind and silently true of nothing else. Measured
on `clockspeed/save/workdir.py::_listing_problem`, which takes `exc: OSError`:
`detail=str(exc)` was 0 findings and green, while the same `str(exc)` moved
into a real handler was 1 finding and red.

So a parameter ANNOTATED as an exception type is bound over its function body
too - `def` and `async def` alike, because `ast.AsyncFunctionDef` is not a
subclass of `ast.FunctionDef` - and its whole-object renderings land in
`param_found`. The population is DERIVED from annotations rather than listed:
there is no set of helpers to keep up to date, so a new one cannot escape by
not being on it.

THE ONE EXEMPTION, and why it is shaped the way it is. Both real redaction
helpers render the whole object for exactly one type, and both are correct
because that type is DEFINED IN THEIR OWN MODULE - so the module builds the
message and can promise it carries no path. Each says so at the site: "built
by git_run_error() below, already argv-free" and "built in this module and is
already free of git's stderr and of every discovered path". The exemption is
therefore structural - a render under `isinstance(NAME, T)` where every T is a
class defined in this module - and NOT "a render under any isinstance test",
because `isinstance(exc, OSError): return str(exc)` wears identical syntax and
is the worst leak in the class. CS-427's privacy guards keyed on the safe
route and so never graded the unsafe one; this keys on the risky construct and
carries `test_a_render_guarded_by_a_foreign_type_does_not_earn_the_exemption`
to prove the exemption cannot reach it.

WHAT IS NOT A RENDERING, and this half is load-bearing. A NAMED FIELD is safe
and must not be flagged:

    NAME.reason, NAME.msg, NAME.lineno, NAME.colno, NAME.strerror
    getattr(NAME, "msg", None)      default is not the object
    type(NAME).__name__
    raise SomeError(...) from NAME  the cause slot, not this message's text -
                                    read the correction below before quoting it
    helper(NAME)                    handing it to a redactor is the FIX - though
                                    since CS-441 that helper's own body is
                                    scanned in its turn, see below

THE CHAINED RAISE IS OUT OF THIS CHANNEL, NOT HARMLESS, and this entry said
otherwise until CS-857. It read "chaining, not rendering", which is false as a
statement about the world: `from NAME` sets `__cause__`, and the interpreter
prints that cause's OWN message beside this one in the formatted traceback
under default flags. A carefully redacted message can therefore render clean
while the chained `OSError` renders the raw path next to it. What is true is
narrower - this detector grades whole-object renderings into TEXT and does not
model chaining at all, so the shape is TRANSPARENT to it rather than exempted
by it, and no code here decides anything about a cause. The traceback channel
has exactly one owner, `tests/chained_cause_guard.py`, which answers it by
measurement rather than by belief, and `from None` is a legitimate remedy there
rather than a loss of the traceback.

THAT CORRECTION IS PROSE, AND PROSE IS WHAT LET IT ROT. The claim survived two
CS-857 commits that edited this very file, because nothing grades a sentence.
`tests/chained_exemption_guard.py` grades the CODE form of the same belief - a
module reading an `ast.Raise` cause to decide the question for itself - and it
names this record in its own residual list as one it cannot see. If anyone ever
implements the belief here, that guard reddens; if anyone merely writes it down
again, nothing will.

`clockspeed/data/docs_extract.py` renders `exc.reason`, `exc.msg`, `exc.lineno`
and `exc.colno` and is ALREADY CORRECT. A naive detector flags it, and whoever
sees that red then either "fixes" correct code or loosens the test until it is
vacuous. `test_named_field_renderings_are_not_flagged` pins that file by name
so neither can happen quietly.

WHY THE DETECTOR IS PROVEN ABLE TO FAIL. A sweep that finds nothing is
indistinguishable from a sweep that looks for nothing. `test_detector_flags_
every_leaky_shape` runs it against a synthetic module carrying one instance of
each shape above and asserts every one is caught. Without that, a green run
here is a green light with nothing behind it.

SCOPE, and its one waiver. Every tracked `*.py` is scanned, including this
module and every tool - CONVENTIONS.md section 15.1: "a guard can be green
while self-excusing - skipping itself on the very files it is meant to
cover." The single waiver below is asserted to still be LIVE, so it cannot rot
into a silent exemption after the code it describes has gone.

TRACEBACKS ARE A SECOND CLASS WITH A DIFFERENT REMEDY. `traceback.print_exc`
renders an absolute path per frame and ends in `str(exc)`, so it leaks the same
way - but it cannot be redacted, only SUPPRESSED BY DEFAULT AND OPTED INTO,
which is the shape non-negotiable 12 already mandates for the save header
options string. The detector therefore classifies each traceback site as
guarded (inside an `os.environ` test) or unguarded, asserts both crash handlers
are guarded, and holds the unguarded remainder in a named residual list so a
NEW unconditional traceback is red rather than absorbed.
"""

from __future__ import annotations

import ast
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from tests.toolpath_guard import kit_pin_problems

REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALLER_RELATIVE = ("scripts", "install_hooks.py")
GATE = REPO_ROOT / "tools" / "precommit_gate.py"
HOOK_NAMES = ("pre-commit", "commit-msg", "pre-push")
SUBPROCESS_TIMEOUT = 120

# The oracle for "did this output leak a path", independently of the redactor
# being tested - a redactor is blind exactly where it is blind, so it can never
# be its own oracle.
#
# WIDENED 2026-08-15 (CS-406) TO COVER POSIX, AND THE REASON IS A MEASURED
# VACUITY RATHER THAN A TIDINESS ARGUMENT. This pattern was
# ``[A-Za-z]:[\\/]`` alone - a DRIVE-LETTER regex - so on the Linux CI runner it
# could not match an absolute path at all. Every ``not ABSOLUTE_PATH.search(...)``
# assertion below was therefore passing VACUOUSLY on every CI run since it was
# written: the oracle returned None for a POSIX temp-directory or home-directory
# path exactly as it would for clean output, and the two are indistinguishable
# from a green run.
#
# It was caught by the NON-VACUITY assertion in
# ``test_installer_wiring_line_renders_no_absolute_path``, which asserts the
# probe's own sandbox root is something the oracle WOULD match. That assertion
# went red on CI while every sibling stayed green, which is precisely the job it
# exists to do. `docs/LEDGER.md` had already recorded the residual - "POSIX
# behaviour of the remedy is unobserved ... settled only by a Linux runner".
#
# STATED LIMIT, because this is a heuristic and not a parser: the POSIX branch
# names the roots under which a leaked path on a runner or a developer machine
# actually lands. It will NOT match an absolute path under an unusual root, so a
# green here is weaker on POSIX than on Windows. The value-based assertions that
# accompany it - `str(root) not in text` and `root.name not in text` - are the
# platform-independent half and are what actually pin the remedy.
_WINDOWS_ABSOLUTE = r"[A-Za-z]:[\\/]"
_POSIX_ABSOLUTE = r"(?<![\w.~-])/(?:tmp|home|root|Users|var|usr|opt|mnt|media|srv)(?:/|\b)"
ABSOLUTE_PATH = re.compile(_WINDOWS_ABSOLUTE + "|" + _POSIX_ABSOLUTE)

# Builtins that render their whole argument as text.
TEXT_BUILTINS = frozenset({"str", "repr", "ascii", "format"})

# `getattr(obj, "name", default)` - three arguments is the shape with a
# fallback, and the fallback is where the object sneaks back in.
GETATTR_WITH_DEFAULT = 3

# `isinstance(obj, T)`. The two-argument form is the only one that constrains a
# name to a type; anything else is not a type guard this exemption may read.
ISINSTANCE_ARITY = 2

# ast.FormattedValue.conversion, as the source spelling it came from.
CONVERSIONS = {-1: "", 115: "!s", 114: "!r", 97: "!a"}

# The traceback-rendering calls. Same leak class, different remedy - see the
# module docstring.
TRACEBACK_CALLS = frozenset({"print_exc", "format_exc", "print_exception", "format_exception"})

# Appended to a traceback finding that sits inside an os.environ-tested branch,
# i.e. one a reader has to opt in to rather than one that prints by default.
GUARDED_SUFFIX = " (opt-in guarded)"

# Traceback sites that print unconditionally and are NOT fixed here, each with
# the reason. Anything not on this list turning up unguarded is a new defect
# and fails the test - this is a record of known residuals, not an allowlist
# that quietly absorbs the next one.
UNGUARDED_TRACEBACK_RESIDUALS = {
    "tests/save/test_properties.py": (
        "CS-963, and the one entry here whose rendered exception carries nothing "
        "from a save at all. The cause-chain frame walker skips a context that "
        "`raise ... from None` suppressed, and that skip is a claim ABOUT THE "
        "RENDERER - traceback prints neither the suppressed exception nor its "
        "frames - rather than a preference of this module's. So the renderer is "
        "run and its output asserted to omit the suppressed frame; if CPython ever "
        "began showing one, the walker would be wrong rather than merely different "
        "and the arm reddens. The exception it formats is built in this module by "
        "two helpers that raise a ValueError and a RuntimeError with literal "
        "messages, over a literal marker constant - no save, no path, no library "
        "call anywhere in its chain. Suppressing the rendering would delete the "
        "only half of that arm that makes it a measurement."
    ),
    "tests/save/test_header.py": (
        "A redaction-ASSERTION helper: _exception_surfaces() collects str, repr, "
        "args, notes and the formatted traceback precisely so the test can assert "
        "none of them carries personal data. The rendering is the subject under "
        "test, and the exception is a parameter rather than a caught object."
    ),
    "tests/save/test_objects.py": (
        "Same shape as the test_header.py entry above, and found by this sweep at "
        "the MERGE rather than by either slice alone - which is the guard working. "
        "The planted-marker test formats the traceback of every raised ObjectError "
        "so it can assert no fixture class path, instance name or root object "
        "reaches any surface. Rendering it IS the assertion; suppressing it would "
        "delete the check."
    ),
    "tests/save/test_world.py": (
        "Same shape again, and the sharpest case of the three. world.py is the "
        "layer that WRAPS its siblings with `raise ... from exc`, so the formatted "
        "traceback is the ONLY surface on which a cause's text becomes this "
        "layer's output - the channel this layer introduces and no other layer "
        "has. The planted-marker test renders it precisely to assert that no save "
        "name, options string, session name, class path, instance name or world "
        "token reaches any surface. Suppressing it would delete the only check of "
        "that channel."
    ),
    "tests/test_chained_cause.py": (
        "CS-857's rendering measurement, and the one entry here whose SUBJECT is "
        "this record's own leak class. The module formats the traceback of each "
        "shipped chained raise precisely to assert that the CAUSE carries no path "
        "the redactor would rewrite - the channel `raise ... from exc` opens and "
        "that no other surface exposes. The GRADED rendering uses limit=0 and is "
        "asserted to carry no frame line, which matters because this machine's "
        "stdlib sits under the user profile, so a frame line is itself redactable "
        "and would redden the arm with no cause present. IT ALSO RENDERS THE "
        "FRAME-BEARING DEFAULT, at two of its four format_exception calls, and that "
        "is deliberate: the faithful-subset claim is that the limit=0 lines are a "
        "subset of the default's, which is not measurable without rendering the "
        "default. Neither escapes its function on the happy path, and on a failure "
        "the CS-428 report redactor covers the locals channel - MEASURED under "
        "--showlocals. This sentence previously said no frame line is emitted at "
        "all; a CS-857 adversary measured that FALSE at both no-limit sites, on the "
        "very axis the reason invokes to justify itself. "
        "The opt-in os.environ branch this guard offers as the remedy would stop "
        "every arm running by default, which is the same as deleting them."
    ),
}

# Files that render an exception PARAMETER as a whole object and are not fixed
# here, each with the reason. Same contract as the traceback residuals above:
# a record of known sites, not an allowlist that absorbs the next one. Anything
# not listed here turning up is a new defect and fails the test, and a listing
# whose site has gone is also a failure rather than a quiet leftover.
#
# WHY THESE ARE RECORDED RATHER THAN EXEMPTED. The structural exemption reads
# ONE containment: a whole-object render under an `isinstance` test naming a
# class the module itself defines. Both of these contain the object a different
# way, and neither containment is a property this detector can read off the
# AST. Recording them keeps the site VISIBLE on a green run, which is the
# fail-closed direction - an exemption broad enough to cover them would also
# cover the leak, which is the CS-427 inversion this file must not repeat.
PARAMETER_RENDER_RESIDUALS = {
    "tests/save/test_header.py": (
        "The redaction-ASSERTION helper _exception_surfaces(), already recorded "
        "in UNGUARDED_TRACEBACK_RESIDUALS above for the traceback line of the "
        "very same function - whose entry states the shape outright: 'the "
        "exception is a parameter rather than a caught object'. It collects "
        "str, repr, args, notes and the formatted traceback precisely so the "
        "test can assert none of them carries personal data. Rendering IS the "
        "assertion; suppressing it would delete the check."
    ),
    "tools/drift_guard.py": (
        "_exc_text()'s non-OSError branch, and a THIRD redaction helper with a "
        "containment this detector cannot read. The OSError branch renders "
        "strerror - a named field - while every other type is rendered whole "
        "and then passed through _redact(), which fails closed to a withheld "
        "marker when the redactor will not import. That is a wrapper rather "
        "than a per-type allowlist, and its limit is already on record: redact "
        "rewrites a path under a HOME directory and leaves an absolute path "
        "that is not under one untouched. Bounded, deliberate and documented "
        "at the site - so it is held visible here rather than exempted."
    ),
}

# Caught-exception renders inside VENDORED fleet kit files (CS-1272), each
# keyed by (path, shape, line) and each answering EXACTLY one live site, so a
# second render in the same file is still a finding - never a blanket file
# waiver. The LINE is a stable key here and nowhere else: a row holds ONLY
# while its file is the kit's pinned bytes, so the line cannot move without
# the pin reddening first (CS-1282 added the line when kit version 10 put a
# second render of the same shape into each of the two files; kit version
# 11 repaired every row but one under CS-1287).
# FLEET item 11: a kit file is MAIN's bytes and is never edited here, so the
# repair is a kit version rather than a local edit; every site is owed to
# MAIN as a kit report (BACKLOG.md). RECORDED RATHER THAN EXEMPTED for the
# reason PARAMETER_RENDER_RESIDUALS gives: the site stays VISIBLE on a green
# run. And the moment a local byte moves,
# test_every_vendored_render_residual_is_at_its_kit_pin reddens, so a row can
# never cover a render this tree wrote.
VENDORED_RENDER_RESIDUALS = {
    ("ops/fleet_kit/fleet_headless.py", "str(exc)", 1238): (
        "CS-1282, FLEET item 11 - the kit's command-line entry, main(), renders "
        "a Refused whole into its one JSON stdout line. Reported to MAIN as kit "
        "defect 5 and REJECTED in kit version 11's ORDER (CS-1287): with the "
        "SlotTimeout render fixed, every Refused the kit raises is a kit "
        "literal, a class name, a number or the caller's own argument echoed "
        "to that caller, and the reason line is the command line's exit-3 "
        "contract. Reversed if any Refused message is found rendering text the "
        "caller did not supply. The line moved 1069 -> 1089 on the v11 bytes "
        "1089 -> 1169 on the v13 bytes (CS-1290), 1169 -> 1220 on "
        "the v14 bytes (CS-1299) and 1220 -> 1238 on the v15 bytes (CS-1303)."
    ),
    ("ops/fleet_kit/fleet_gitlock.py", "str(exc)", 494): (
        "CS-1290, FLEET item 11 - the git lock's command-line entry, main(), "
        "writes a LockRefused whole to stderr before exit 3. MEASURED on the v13 and v14 "
        "bytes: every LockRefused it raises is a kit literal, an integer (a "
        "timeout, an age, a holder pid), the caller's own option echoed back, "
        "the literal word author or committer, or a staged path made "
        "TREE-RELATIVE by fleet_claims.rel_in against the tree top - staged "
        "paths sit inside that top, so no home path reaches the line. Reversed "
        "if a LockRefused is found rendering an absolute path or text the "
        "caller did not supply."
    ),
    ("ops/fleet_kit/fleet_suite_gate.py", "str(exc)", 544): (
        "CS-1290, FLEET item 11 - the suite gate's command-line entry, main(), "
        "writes a GateRefused whole to stderr before exit 3. MEASURED on the v13 to v15 "
        "bytes: every GateRefused it raises is a kit literal, an integer (a "
        "timeout, a slot count), the caller's own option echoed back, or a "
        "dirty path made TREE-RELATIVE by fleet_claims.rel_in - the dirty paths "
        "come from this tree's own status, inside its top. Reversed if a "
        "GateRefused is found rendering an absolute path or text the caller did "
        "not supply."
    ),
    ("ops/fleet_kit/fleet_rewrite.py", "str(exc)", 497): (
        "CS-1290, FLEET item 11 - the rewrite helper's command-line entry, "
        "main(), writes a Refused whole to stderr before exit 3. MEASURED on the "
        "v13 and v14 bytes: every Refused it raises is a kit literal, an integer (an "
        "exit status, an age bound, the minimum kit version), a git verb the "
        "kit itself passed, or the config key name - no path, value or "
        "identity. Nothing in this tree runs the helper; CS-700 S7a may. "
        "Reversed if a Refused is found rendering a path or a scrubbed value."
    ),
}

# Sites the sweep flags that are NOT leaks, each with the reason, and each
# asserted live by test_every_waiver_is_still_live. A waiver that outlives the
# code it describes is a silent exemption, which is the failure CONVENTIONS.md
# section 15.1 exists to prevent.
WAIVED_FILES = {
    "tests/save/test_usmap.py": (
        "Redaction-ASSERTION module. It captures str(exc) into a local list and "
        "then asserts the text carries no secret name, no backslash and no path "
        "- the rendering is the subject under test, not an emission. Nothing is "
        "printed, raised or returned to an operator."
    ),
}


@dataclass(frozen=True)
class Rendering:
    """One place a caught exception object is rendered as a whole."""

    path: str
    lineno: int
    shape: str

    def __str__(self) -> str:
        """Render as `path:line  shape` - the form the failure message prints."""
        return f"{self.path}:{self.lineno}  {self.shape}"


def annotation_names(node: ast.expr | None) -> set[str]:
    """Every bare identifier inside an annotation, unions and strings included.

    `OSError`, `subprocess.SubprocessError`, `OSError | ValueError` and the
    quoted `"OSError"` all have to yield the same identifier, because which
    spelling an author reached for says nothing about what the value is.
    """
    if node is None:
        return set()
    names: set[str] = set()
    for sub in ast.walk(node):
        if isinstance(sub, ast.Name):
            names.add(sub.id)
        elif isinstance(sub, ast.Attribute):
            names.add(sub.attr)
        elif isinstance(sub, ast.Constant) and isinstance(sub.value, str):
            try:
                names |= annotation_names(ast.parse(sub.value, mode="eval").body)
            except SyntaxError:
                continue
    return names


def is_exception_annotation(node: ast.expr | None) -> bool:
    """Whether an annotation names an exception type, read off the SOURCE.

    Syntactic on purpose. Resolving the name would mean importing the module,
    and this sweep has to run over the gate and the installer, both of which
    must be scannable in a checkout where importing anything is not safe to
    assume. `Error` and `Exception` suffixes are what PEP 8 asks for and what
    every annotation in this tree uses.
    """
    return any(name.endswith(("Error", "Exception")) for name in annotation_names(node))


def local_class_names(tree: ast.Module) -> frozenset[str]:
    """Every class DEFINED in this module, which is the exemption's whole basis."""
    return frozenset(node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef))


def isinstance_guards(test: ast.expr) -> dict[str, frozenset[str]]:
    """Map each name an `isinstance(NAME, T)` test constrains to the types in T.

    A tuple of types yields every member, so a mixed `(LocalError, OSError)`
    cannot be exempted on the strength of its local half alone.
    """
    guards: dict[str, frozenset[str]] = {}
    for sub in ast.walk(test):
        if not isinstance(sub, ast.Call) or not isinstance(sub.func, ast.Name):
            continue
        if sub.func.id != "isinstance" or len(sub.args) != ISINSTANCE_ARITY:
            continue
        subject = sub.args[0]
        if isinstance(subject, ast.Name):
            guards[subject.id] = frozenset(annotation_names(sub.args[1]))
    return guards


class RenderVisitor(ast.NodeVisitor):
    """Flag whole-object renderings of a caught OR parameter-bound exception.

    TWO SCOPES, kept in two lists. `found` holds renderings of a name bound by
    `except ... as NAME`. `param_found` holds renderings of a parameter
    ANNOTATED as an exception type, which is the same leak one call deeper -
    the object reaches the helper intact, so `str()` appends the same filename
    it would have inside the handler. Until CS-441 only the first scope
    existed, and this docstring asserted that a helper taking the exception as
    a parameter was "the sanctioned boundary" - which described one correct
    helper and silently covered every other function with the same signature.

    THE EXEMPTION, and it is structural rather than a list of blessed names. A
    whole-object rendering is not flagged when it sits under an
    `isinstance(NAME, T)` test and every T is a class DEFINED IN THIS MODULE.
    A module that defines an exception type also builds its message, so it can
    promise the text carries no path; a type it merely imports has a `str()` it
    does not control. That is exactly what both real redaction helpers say
    about themselves in their own comments, and it deliberately does NOT reach
    `isinstance(exc, OSError): return str(exc)`, which is the worst leak in
    this class wearing the same syntax.
    """

    def __init__(self, path: str, local_classes: frozenset[str] = frozenset()) -> None:
        """Start a scan of one file, identified by its repo-relative path.

        `local_classes` defaults to empty, so a visitor built without it
        exempts nothing rather than everything - the fail-closed direction.
        """
        self.path = path
        self.local_classes = local_classes
        self.bound: list[str] = []
        self.params: list[frozenset[str]] = []
        self.type_guards: list[dict[str, frozenset[str]]] = []
        self.found: list[Rendering] = []
        self.param_found: list[Rendering] = []
        self.tracebacks: list[Rendering] = []
        self.env_guard_depth = 0

    def flag(self, node: ast.expr, shape: str) -> None:
        """Record one finding at the position of the offending expression."""
        self.found.append(Rendering(self.path, node.lineno, shape))

    def bound_name(self, node: ast.expr) -> str | None:
        """Return the name if this expression IS the caught exception itself."""
        if isinstance(node, ast.Name) and node.id in self.bound:
            return node.id
        return None

    def resolve(self, node: ast.expr) -> tuple[str, bool] | None:
        """Return (name, is_parameter) if this expression IS an exception object.

        A handler binding wins over a parameter of the same name, because
        inside the handler body that name refers to the caught object.
        """
        if not isinstance(node, ast.Name):
            return None
        if node.id in self.bound:
            return (node.id, False)
        if any(node.id in frame for frame in self.params):
            return (node.id, True)
        return None

    def record(self, node: ast.expr, name: str, is_parameter: bool, shape: str) -> None:
        """File one rendering into the scope it belongs to, honouring the exemption."""
        if not is_parameter:
            self.found.append(Rendering(self.path, node.lineno, shape))
            return
        if self.type_exempt(name):
            return
        self.param_found.append(Rendering(self.path, node.lineno, shape))

    def type_exempt(self, name: str) -> bool:
        """Whether this name sits under an isinstance test on a LOCAL class only."""
        for frame in reversed(self.type_guards):
            guarded = frame.get(name)
            if guarded is not None:
                return bool(guarded) and guarded <= self.local_classes
        return False

    def note_call(self, node: ast.expr, shape_of) -> None:
        """Resolve an expression and record it under the shape its caller names."""
        hit = self.resolve(node)
        if hit is None:
            return
        name, is_parameter = hit
        self.record(node, name, is_parameter, shape_of(name))

    def exception_parameters(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> frozenset[str]:
        """Every parameter of this function annotated as an exception type."""
        spec = node.args
        every = [*spec.posonlyargs, *spec.args, *spec.kwonlyargs]
        if spec.vararg is not None:
            every.append(spec.vararg)
        if spec.kwarg is not None:
            every.append(spec.kwarg)
        return frozenset(arg.arg for arg in every if is_exception_annotation(arg.annotation))

    def visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        """Bind exception-annotated parameters over the body, then restore."""
        self.params.append(self.exception_parameters(node))
        self.generic_visit(node)
        self.params.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Dispatch a `def` into the shared parameter-scoping body."""
        self.visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Dispatch an `async def` into the SAME body as its `def` twin.

        `ast.AsyncFunctionDef` is not a subclass of `ast.FunctionDef`, so a
        visitor carrying only the method above is blind to a byte-identical
        `async def` helper. That exact hole has shipped in this repository
        before, which is why the two dispatch to one implementation rather
        than to two that can drift apart.
        """
        self.visit_function(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        """Bind `except ... as NAME` over its body, then restore the scope."""
        if node.type is not None:
            self.visit(node.type)
        if node.name is None:
            for child in node.body:
                self.visit(child)
            return
        self.bound.append(node.name)
        for child in node.body:
            self.visit(child)
        self.bound.pop()

    def visit_JoinedStr(self, node: ast.JoinedStr) -> None:
        """An f-string interpolating the object itself - `f"{exc}"`."""
        for part in node.values:
            if not isinstance(part, ast.FormattedValue):
                continue
            conversion = CONVERSIONS.get(part.conversion, "!?")
            # `conversion` is bound as a default rather than captured: the
            # closure is called before the next iteration rebinds it, but a
            # loop-variable capture is a defect waiting for a refactor.
            self.note_call(part.value, lambda name, tag=conversion: f"f-string {{{name}{tag}}}")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        """Text builtins, `.format(...)`, `getattr` defaults and tracebacks."""
        self.check_text_builtin(node)
        self.check_str_format(node)
        self.check_getattr_default(node)
        self.note_traceback(node)
        self.generic_visit(node)

    def visit_If(self, node: ast.If) -> None:
        """Mark the body of an `os.environ`-tested branch as opt-in guarded.

        This is what separates a traceback that prints unconditionally from one
        a reader has to ask for. Only the body counts - the `else` branch of an
        environment test is the DEFAULT path, and a traceback there is exactly
        the thing being suppressed.

        The same body-only rule carries the `isinstance` type guard that the
        per-type redaction exemption reads. `else` is again the wrong side: the
        branch NOT taken when the type matched is the branch where the type is
        anything at all, which is where the object must not be rendered.
        """
        self.visit(node.test)
        guarded = any(
            isinstance(sub, ast.Name | ast.Attribute)
            and getattr(sub, "id", getattr(sub, "attr", "")) == "environ"
            for sub in ast.walk(node.test)
        )
        self.env_guard_depth += int(guarded)
        self.type_guards.append(isinstance_guards(node.test))
        for child in node.body:
            self.visit(child)
        self.type_guards.pop()
        self.env_guard_depth -= int(guarded)
        for child in node.orelse:
            self.visit(child)

    def visit_BinOp(self, node: ast.BinOp) -> None:
        """Percent formatting - `"...%s" % exc` and `"..." % (a, exc)`."""
        if isinstance(node.op, ast.Mod):
            right = node.right
            operands = right.elts if isinstance(right, ast.Tuple) else [right]
            for operand in operands:
                self.note_call(operand, lambda name: f"percent-format {name}")
        self.generic_visit(node)

    def check_text_builtin(self, node: ast.Call) -> None:
        """`str(exc)`, `repr(exc)`, `ascii(exc)`, `format(exc)`."""
        func = node.func
        if not isinstance(func, ast.Name) or func.id not in TEXT_BUILTINS:
            return
        for arg in node.args:
            self.note_call(arg, lambda name, call=func.id: f"{call}({name})")

    def check_str_format(self, node: ast.Call) -> None:
        """`"...".format(exc)`, positionally or as a keyword value."""
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr != "format":
            return
        for arg in [*node.args, *(kw.value for kw in node.keywords)]:
            self.note_call(arg, lambda name: f".format({name})")

    def check_getattr_default(self, node: ast.Call) -> None:
        """`getattr(exc, "field", exc)` - the object as the FALLBACK value."""
        func = node.func
        if not isinstance(func, ast.Name) or func.id != "getattr":
            return
        if len(node.args) != GETATTR_WITH_DEFAULT:
            return
        self.note_call(node.args[2], lambda name: f"getattr default {name}")

    def note_traceback(self, node: ast.Call) -> None:
        """Record a traceback rendering, and whether it is opt-in guarded."""
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr in TRACEBACK_CALLS:
            suffix = GUARDED_SUFFIX if self.env_guard_depth else ""
            self.tracebacks.append(
                Rendering(self.path, node.lineno, f"traceback.{func.attr}{suffix}")
            )


def tracked_python_files() -> list[str]:
    """Every `*.py` path git can see, from git - never a hardcoded module list.

    `--cached` is the tracked set. `--others --exclude-standard` adds the files
    that are written but not yet committed, minus anything gitignored. Both are
    needed: a detector enumerating only `--cached` cannot see a module until it
    has been committed, which includes THIS module on the commit that adds it,
    and a new leaky file would get one free pass. Checking what is on disk is
    also what the PostToolUse guard and the commit gate already do.
    """
    completed = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "*.py"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=True,
        timeout=SUBPROCESS_TIMEOUT,
    )
    seen = {line.strip() for line in completed.stdout.splitlines() if line.strip()}
    return sorted(seen)


def scan_source(path: str, source: str) -> RenderVisitor:
    """Scan one module's source and return the visitor holding its findings."""
    tree = ast.parse(source)
    visitor = RenderVisitor(path, local_class_names(tree))
    visitor.visit(tree)
    return visitor


def scan_repo() -> tuple[list[Rendering], list[Rendering]]:
    """Scan every tracked module. Returns (object renderings, traceback sites)."""
    found: list[Rendering] = []
    tracebacks: list[Rendering] = []
    for relative in tracked_python_files():
        text = (REPO_ROOT / relative).read_text(encoding="utf-8")
        visitor = scan_source(relative, text)
        found.extend(visitor.found)
        tracebacks.extend(visitor.tracebacks)
    return found, tracebacks


def scan_repo_parameters() -> list[Rendering]:
    """Every whole-object rendering of an exception PARAMETER across the tree."""
    found: list[Rendering] = []
    for relative in tracked_python_files():
        text = (REPO_ROOT / relative).read_text(encoding="utf-8")
        found.extend(scan_source(relative, text).param_found)
    return found


def describe(findings: list[Rendering]) -> str:
    """Render findings one per line for a failure message that names each site."""
    return "\n".join(f"  {finding}" for finding in findings)


def imported_roots(source: str) -> set[str]:
    """Every package a module imports AT MODULE SCOPE, from its AST.

    Read from the source rather than by importing it: importing would run the
    module, and one of the two modules checked with this is the gate, which
    must be provably startable in a checkout where nothing else imports.

    MODULE SCOPE is the whole point, and this is not a loophole. A module-level
    import must resolve for the program to start at all; a function-local one
    wrapped in `try: ... except ImportError:` is a PROBE, and the gate has
    exactly one - `import ruff` inside ruff_command(), which degrades to
    "ruff was not found" instead of refusing to run. Counting that as a
    dependency would report a startup failure that cannot happen.
    """
    roots: set[str] = set()
    for node in ast.parse(source).body:
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def guarded_import_probes(source: str) -> set[str]:
    """Packages imported only inside a `try:` that catches ImportError."""
    probes: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Try):
            continue
        catches_import = any(
            isinstance(handler.type, ast.Name) and handler.type.id == "ImportError"
            for handler in node.handlers
        )
        if not catches_import:
            continue
        for inner in ast.walk(node):
            if isinstance(inner, ast.Import):
                probes.update(alias.name.split(".")[0] for alias in inner.names)
    return probes


# ---------------------------------------------------------------------------
# The sweep
# ---------------------------------------------------------------------------


def test_no_tracked_module_renders_a_caught_exception_object():
    found, _ = scan_repo()
    leaks = [
        finding
        for finding in found
        if finding.path not in WAIVED_FILES
        and (finding.path, finding.shape, finding.lineno) not in VENDORED_RENDER_RESIDUALS
    ]
    assert not leaks, (
        f"{len(leaks)} site(s) render a caught exception OBJECT into a message. "
        "str() on an OSError appends the path it failed on, which carries the "
        "account name (CLAUDE.md non-negotiable 12). Render a named FIELD, or "
        "a per-TYPE redaction allowlist - never the object:\n" + describe(leaks)
    )


def test_every_tracked_python_file_was_actually_parsed():
    # A sweep that silently skipped a file it could not parse would be green
    # for the wrong reason. Assert the enumeration is non-trivial and that
    # every file in it parsed.
    tracked = tracked_python_files()
    assert len(tracked) > 1, "git ls-files returned almost nothing; the sweep would be vacuous"
    unparsed = []
    for relative in tracked:
        try:
            ast.parse((REPO_ROOT / relative).read_text(encoding="utf-8"))
        except SyntaxError:
            unparsed.append(relative)
    assert not unparsed, f"tracked files that did not parse: {unparsed}"


def test_the_sweep_enumerates_rather_than_hardcoding_a_module_list():
    # Condition 3 of the grant. The instance set CS-202 recorded by hand went
    # stale before CS-205 was worked; the fix is that no list exists.
    tracked = set(tracked_python_files())
    assert "tests/test_exception_rendering.py" in tracked, "the detector must scan itself"
    tools = {path for path in tracked if path.startswith("tools/")}
    assert len(tools) > 1, "every tool must be in scope, not a chosen subset"
    for expected in (
        "tools/precommit_gate.py",
        "tools/edit_lint_check.py",
        "tools/memory_sync.py",
        "scripts/install_hooks.py",
    ):
        assert expected in tracked, f"{expected} is tracked but was not enumerated"


# ---------------------------------------------------------------------------
# Controls - the detector must be able to fail, and must not over-fire
# ---------------------------------------------------------------------------

# Assembled as SOURCE TEXT rather than written as real code, so this module's
# own AST carries no `except ... as exc:` handler that renders `exc` - the
# detector scans this file like any other and would otherwise flag itself.
LEAKY_SOURCE = '''
import subprocess


def each_shape(path):
    """One instance of every shape the detector must catch."""
    try:
        return open(path).read()
    except OSError as exc:
        a = f"fstring: {exc}"
        b = f"fstring repr: {exc!r}"
        c = f"fstring str: {exc!s}"
        d = str(exc)
        e = repr(exc)
        f = "dotformat: {}".format(exc)
        g = "dotformat kw: {why}".format(why=exc)
        h = "percent: %s" % exc
        i = "percent tuple: %s %s" % (path, exc)
        j = "getattr fallback: {}".format(getattr(exc, "problem", exc))
        raise RuntimeError(a + b + c + d + e + f + g + h + i + j) from exc
'''

# Every flagged site in LEAKY_SOURCE above, counted by hand from the source.
LEAKY_SITE_COUNT = 10

FIELD_ONLY_SOURCE = '''
def named_fields_only(raw, codec):
    """The docs_extract.py shape - named fields, and already correct."""
    try:
        return raw.decode(codec)
    except UnicodeDecodeError as exc:
        message = f"did not decode: {exc.reason} at byte {exc.start} of {len(raw)}"
        raise ValueError(message) from exc
    except ValueError as exc:
        detail = getattr(exc, "msg", None) or type(exc).__name__
        line = getattr(exc, "lineno", 0)
        message = "not valid: {} at line {}".format(detail, line)
        raise ValueError(message) from exc


def helper(exc):
    """A per-type redaction allowlist. Its own str() is NOT inside a handler."""
    if isinstance(exc, OSError):
        return exc.strerror or type(exc).__name__
    return type(exc).__name__


def routed_through_the_helper(path):
    """Passing the object to a redactor is the fix, not the defect."""
    try:
        return open(path).read()
    except OSError as exc:
        raise ValueError(f"could not read: {helper(exc)}") from exc
'''


def test_detector_flags_every_leaky_shape():
    # THE POSITIVE CONTROL. Without this, a green sweep proves nothing: a
    # detector that looks for nothing finds nothing and passes.
    visitor = scan_source("synthetic_leaky.py", LEAKY_SOURCE)
    shapes = sorted({finding.shape for finding in visitor.found})
    expected = sorted(
        [
            "f-string {exc}",
            "f-string {exc!r}",
            "f-string {exc!s}",
            "str(exc)",
            "repr(exc)",
            ".format(exc)",
            "percent-format exc",
            "getattr default exc",
        ]
    )
    assert shapes == expected, (
        "the detector missed a leaky shape it must catch.\n"
        f"  caught:  {shapes}\n  expected: {expected}"
    )
    # More sites than shapes: two f-string {exc} and two .format(exc) spellings
    # each collapse to one shape string. Pin the count so a shape cannot be
    # caught at one spelling and missed at a second.
    assert len(visitor.found) == LEAKY_SITE_COUNT, describe(visitor.found)


def test_named_field_renderings_are_not_flagged():
    # THE NEGATIVE CONTROL. A detector that cannot tell `exc.reason` from
    # `exc` sends someone to "fix" correct code or to loosen this test.
    visitor = scan_source("synthetic_fields.py", FIELD_ONLY_SOURCE)
    assert not visitor.found, (
        "the detector flagged a NAMED FIELD or a redaction helper as a leak. "
        "These shapes are correct and must stay unflagged:\n" + describe(visitor.found)
    )


def test_the_real_docs_extract_module_is_not_flagged():
    # The negative control pinned to the actual file, by name. docs_extract.py
    # renders exc.reason, exc.msg, exc.lineno and exc.colno and is correct.
    relative = "clockspeed/data/docs_extract.py"
    source = (REPO_ROOT / relative).read_text(encoding="utf-8")
    visitor = scan_source(relative, source)
    assert not visitor.found, (
        f"{relative} renders NAMED FIELDS and is already correct. If this is "
        "red, the detector regressed - do not 'fix' that file and do not "
        "loosen this test:\n" + describe(visitor.found)
    )
    # Non-vacuous: prove the file really does carry the field shape, so this
    # test cannot pass merely because the module stopped catching anything.
    assert "exc.reason" in source, "the negative control no longer covers what it claims to"


# ---------------------------------------------------------------------------
# CS-441 - the same leak class one call deeper, in a helper that receives the
# exception as a PARAMETER instead of binding it with `except ... as NAME`
# ---------------------------------------------------------------------------

# Assembled as SOURCE TEXT for the same reason LEAKY_SOURCE above is: the sweep
# scans this module like every other, so a real `def f(exc: OSError)` rendering
# `exc` written here would be a finding against this file.
PARAM_LEAKY_SOURCE = '''
def render_the_object(exc: OSError, label: str) -> str:
    """Every shape above, on an exception received as a PARAMETER."""
    a = f"fstring: {exc}"
    b = f"fstring repr: {exc!r}"
    c = f"fstring str: {exc!s}"
    d = str(exc)
    e = repr(exc)
    f = "dotformat: {}".format(exc)
    g = "dotformat kw: {why}".format(why=exc)
    h = "percent: %s" % exc
    i = "percent tuple: %s %s" % (label, exc)
    j = "getattr fallback: {}".format(getattr(exc, "problem", exc))
    return a + b + c + d + e + f + g + h + i + j
'''

# `ast.AsyncFunctionDef` IS NOT a subclass of `ast.FunctionDef`. A visitor that
# handles only the sync node is blind to a byte-identical async body, and this
# repository has shipped exactly that hole before - so the async twin is a
# control rather than a footnote.
PARAM_LEAKY_ASYNC_SOURCE = PARAM_LEAKY_SOURCE.replace(
    "def render_the_object", "async def render_the_object"
)


def test_detector_flags_every_leaky_shape_on_an_exception_parameter():
    # THE POSITIVE CONTROL for the parameter scope. Before CS-441 the detector
    # bound names only at `except ... as NAME`, so a helper handed the very same
    # object one frame deeper rendered it with nothing watching.
    visitor = scan_source("synthetic_param_leaky.py", PARAM_LEAKY_SOURCE)
    shapes = sorted({finding.shape for finding in visitor.param_found})
    expected = sorted(
        [
            "f-string {exc}",
            "f-string {exc!r}",
            "f-string {exc!s}",
            "str(exc)",
            "repr(exc)",
            ".format(exc)",
            "percent-format exc",
            "getattr default exc",
        ]
    )
    assert shapes == expected, (
        "the detector missed a leaky shape on a parameter-bound exception.\n"
        f"  caught:   {shapes}\n  expected: {expected}"
    )
    assert len(visitor.param_found) == LEAKY_SITE_COUNT, describe(visitor.param_found)


def test_the_async_twin_of_the_leaky_helper_is_flagged_identically():
    # `async def` is a different AST node, not a subclass. Compared site for
    # site against the sync twin so a partial async implementation is red.
    sync = scan_source("synthetic_param_leaky.py", PARAM_LEAKY_SOURCE)
    asynchronous = scan_source("synthetic_param_leaky_async.py", PARAM_LEAKY_ASYNC_SOURCE)
    assert [finding.shape for finding in asynchronous.param_found] == [
        finding.shape for finding in sync.param_found
    ], (
        "an `async def` helper is not scanned like its `def` twin. "
        "ast.AsyncFunctionDef is NOT a subclass of ast.FunctionDef:\n"
        + describe(asynchronous.param_found)
    )
    # Non-vacuous: a twin comparison passes trivially if BOTH sides are empty.
    assert asynchronous.param_found, "the async control compared two empty lists"


# ---------------------------------------------------------------------------
# The exemption, and the control that stops it becoming an inversion
# ---------------------------------------------------------------------------

# THE SANCTIONED SHAPE, copied structurally from the two real redaction helpers
# (`tools/precommit_gate.py::safe_exc_text` and its deliberate duplicate in
# `scripts/install_hooks.py`). Both render the whole object for ONE type and
# both are correct, because that type is DEFINED IN THE SAME MODULE - so the
# module builds the message itself and can promise it carries no path. Both
# say so in their own comments: "built by git_run_error() below, already
# argv-free" and "built in this module and is already free of git's stderr and
# of every discovered path". That is the exemption, and it is read off the AST
# rather than off a list of blessed function names.
PARAM_SAFE_SOURCE = '''
import subprocess


class LocalError(RuntimeError):
    """Defined HERE. This module builds its message, so it can promise its text."""


def safe_exc_text(exc: BaseException) -> str:
    """The per-type redaction allowlist. A field is rendered only per type."""
    if isinstance(exc, LocalError):
        return str(exc) or type(exc).__name__
    if isinstance(exc, OSError):
        return exc.strerror or type(exc).__name__
    if isinstance(exc, SyntaxError):
        return exc.msg or type(exc).__name__
    if isinstance(exc, subprocess.TimeoutExpired):
        return "%s after %s seconds" % (type(exc).__name__, exc.timeout)
    if isinstance(exc, subprocess.CalledProcessError):
        return "%s exit %d" % (type(exc).__name__, exc.returncode)
    return type(exc).__name__
'''

# THE ANTI-INVERSION CONTROL, and the reason the exemption is keyed to a
# LOCALLY DEFINED type rather than to "sits under an isinstance test". CS-427's
# privacy guards keyed on the SAFE route and so never graded the unsafe one;
# an exemption for any type-guarded render would repeat that exactly, because
# `isinstance(exc, OSError): return str(exc)` is the WORST case in this whole
# class - str() on an OSError is what appends the filename - and it wears the
# same syntax as the sanctioned helper. OSError is not defined in the module,
# so its str() is not the module's to promise, so the exemption must not reach.
PARAM_FOREIGN_GUARD_SOURCE = '''
class LocalError(RuntimeError):
    """Defined here, and deliberately NOT the type guarding the render below."""


def wears_the_allowlist_syntax(exc: BaseException) -> str:
    """Structurally identical to the sanctioned helper, and a real leak."""
    if isinstance(exc, OSError):
        return str(exc)
    return type(exc).__name__
'''


def test_the_per_type_redaction_allowlist_is_not_flagged():
    # THE NEGATIVE CONTROL, and the hard half of the acceptance. A detector
    # that cannot tell the sanctioned redactor from the leak sends someone to
    # "fix" the two helpers this project's entire redaction path runs through.
    visitor = scan_source("synthetic_param_safe.py", PARAM_SAFE_SOURCE)
    assert not visitor.param_found, (
        "the detector flagged the per-type redaction allowlist. This shape is "
        "correct and is the sanctioned boundary:\n" + describe(visitor.param_found)
    )


def test_a_render_guarded_by_a_foreign_type_does_not_earn_the_exemption():
    # The exemption's OWN executable control. Without this the negative control
    # above could be passing because the detector exempts every isinstance-
    # guarded render, which would wave through the worst leak in the class.
    visitor = scan_source("synthetic_param_foreign.py", PARAM_FOREIGN_GUARD_SOURCE)
    assert [finding.shape for finding in visitor.param_found] == ["str(exc)"], (
        "an isinstance-guarded render of a type the module does NOT define was "
        "exempted. str() on an OSError appends the filename it failed on, so "
        "this is the leak the exemption exists to stay clear of:\n" + describe(visitor.param_found)
    )


def test_the_real_redaction_helpers_are_not_flagged():
    # The negative control pinned to the actual files, by name - the acceptance
    # clause that costs the most to satisfy. These two ARE the project's
    # redaction path; a detector that reddens them sends the next reader to
    # "fix" the helpers every other guard renders its exceptions through.
    for relative in ("tools/precommit_gate.py", "scripts/install_hooks.py"):
        source = (REPO_ROOT / relative).read_text(encoding="utf-8")
        flagged = scan_source(relative, source).param_found
        assert not flagged, (
            f"{relative} is a per-type redaction allowlist and is already "
            "correct. If this is red the detector regressed - do not 'fix' "
            "that file and do not loosen this test:\n" + describe(flagged)
        )
        # NON-VACUOUS, and this is the half that matters. Re-scan the same file
        # with the exemption WITHHELD - a visitor built without local classes
        # exempts nothing - and require it to be flagged. A green above is then
        # the exemption doing work at a live site, rather than the helper
        # having been deleted or its annotation dropped.
        blind = RenderVisitor(relative)
        blind.visit(ast.parse(source))
        assert blind.param_found, (
            f"{relative} no longer renders an exception parameter at all, so "
            "the exemption is being proved against nothing. Re-point this "
            "control at whatever the redaction helper became."
        )


def test_the_parameter_sweep_scans_a_population_that_is_not_empty():
    # A sweep over zero exception-annotated parameters is green for the wrong
    # reason. Assert the derivation actually finds some, and that it finds them
    # in the two files whose helpers the exemption is written around.
    populated = []
    for relative in tracked_python_files():
        tree = ast.parse((REPO_ROOT / relative).read_text(encoding="utf-8"))
        visitor = RenderVisitor(relative)
        if any(
            visitor.exception_parameters(node)
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        ):
            populated.append(relative)
    assert len(populated) > 1, (
        "the derived population is empty or trivial, so the sweep proves "
        f"nothing. Files carrying an exception parameter: {populated}"
    )
    for expected in ("tools/precommit_gate.py", "scripts/install_hooks.py"):
        assert expected in populated, f"{expected} carries a redaction helper but was not derived"


def test_parameter_renders_are_only_the_recorded_residuals():
    # THE SWEEP. This is what a mutant lands on: rendering the exception object
    # inside a function that receives it as an argument turns this red anywhere
    # in the tree, with no list of modules to be absent from.
    found = scan_repo_parameters()
    unexpected = [site for site in found if site.path not in PARAMETER_RENDER_RESIDUALS]
    assert not unexpected, (
        "a function renders an exception it received as a PARAMETER. The object "
        "reached it intact, so str() appends the same filename it would have "
        "inside the handler (CLAUDE.md non-negotiable 12). Render a named "
        "FIELD, or route it through a per-type redaction allowlist:\n" + describe(unexpected)
    )
    # Non-vacuous: every recorded residual must still be a real, live site.
    live = {site.path for site in found}
    stale = sorted(path for path in PARAMETER_RENDER_RESIDUALS if path not in live)
    assert not stale, f"these residuals were fixed; delete their entries: {stale}"


# ---------------------------------------------------------------------------
# The waiver, and the residual the sweep does not assert on
# ---------------------------------------------------------------------------


def test_every_vendored_render_residual_answers_exactly_one_live_site():
    # Non-vacuous AND not a blanket: a row whose site has gone is stale, and a
    # row matching two sites would cover one nobody argued for.
    found, _ = scan_repo()
    counts = {
        key: sum(1 for finding in found if (finding.path, finding.shape, finding.lineno) == key)
        for key in VENDORED_RENDER_RESIDUALS
    }
    wrong = {key: count for key, count in counts.items() if count != 1}
    assert not wrong, f"vendored render residuals not matching exactly one site: {wrong}"


def test_every_vendored_render_residual_is_at_its_kit_pin():
    # CS-1272, FLEET item 11: the row is excused only while the file is MAIN's
    # bytes, checked against ops/fleet_kit/MANIFEST.json by the same oracle the
    # CS-910 census uses for its VENDORED exemption kind.
    paths = sorted({path for (path, _shape, _line) in VENDORED_RENDER_RESIDUALS})
    problems = kit_pin_problems(paths)
    assert (len(paths) > 0, problems) == (True, []), "\n".join(problems)


def test_every_waiver_is_still_live():
    found, _ = scan_repo()
    by_path = {finding.path for finding in found}
    stale = sorted(path for path in WAIVED_FILES if path not in by_path)
    assert not stale, (
        "a waiver outlived the code it describes, which turns it into a silent "
        "exemption. Delete these entries from WAIVED_FILES:\n"
        + "\n".join(f"  {path}" for path in stale)
    )


def test_every_crash_handler_suppresses_its_traceback_by_default():
    # GRANT B's pattern, asserted structurally at every place it applies. A
    # traceback renders an absolute path per frame and ends in str(exc), so it
    # can only be suppressed, never redacted.
    #
    # The installer joined this list under CS-406, which is why the name counts
    # no longer says "both": a count in a test's NAME is a restated fact, and a
    # restated fact drifts (CLAUDE.md section 4). The tuple is the record.
    for relative in (
        "tools/precommit_gate.py",
        "tools/edit_lint_check.py",
        "scripts/install_hooks.py",
    ):
        source = (REPO_ROOT / relative).read_text(encoding="utf-8")
        visitor = scan_source(relative, source)
        assert visitor.tracebacks, f"{relative} lost its crash handler entirely"
        unguarded = [site for site in visitor.tracebacks if GUARDED_SUFFIX not in site.shape]
        assert not unguarded, f"{relative} prints a traceback on the DEFAULT path:\n" + describe(
            unguarded
        )


def test_unguarded_traceback_sites_are_only_the_recorded_residuals():
    # The residual stays visible on a green run instead of absent from one, and
    # a NEW unconditional traceback anywhere in the tree turns this red.
    _, tracebacks = scan_repo()
    unguarded = [site for site in tracebacks if GUARDED_SUFFIX not in site.shape]
    unexpected = [site for site in unguarded if site.path not in UNGUARDED_TRACEBACK_RESIDUALS]
    assert not unexpected, (
        "a traceback prints unconditionally at a site with no recorded reason. "
        "It renders an absolute path per frame and ends in str(exc) - suppress "
        "it behind an opt-in flag, or record why it is safe:\n" + describe(unexpected)
    )
    # Non-vacuous: every recorded residual must still be a real, live site.
    live = {site.path for site in unguarded}
    stale = sorted(path for path in UNGUARDED_TRACEBACK_RESIDUALS if path not in live)
    assert not stale, f"these residuals were fixed; delete their entries: {stale}"


# ---------------------------------------------------------------------------
# scripts/install_hooks.py - grant A conditions 2, 7 and 8
# ---------------------------------------------------------------------------


def run_process(
    args: list[str], cwd: Path, env_extra: dict[str, str] | None = None
) -> subprocess.CompletedProcess[bytes]:
    """Run a command with a bounded timeout and captured output."""
    env = dict(os.environ)
    # Stop git walking above the sandbox into a real repository, so what the
    # installer sees is what this test constructed and nothing else.
    env["GIT_CEILING_DIRECTORIES"] = str(cwd.parent)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        args,
        cwd=str(cwd),
        capture_output=True,
        env=env,
        timeout=SUBPROCESS_TIMEOUT,
        check=False,
    )


def combined(result: subprocess.CompletedProcess[bytes]) -> str:
    """Both streams as one string - a leak on either one is a leak."""
    out = result.stdout.decode("utf-8", "replace")
    err = result.stderr.decode("utf-8", "replace")
    return out + err


def build_sandbox(tmp_path: Path, *, with_hooks: bool = True, as_repo: bool = True) -> Path:
    """Build a throwaway clone carrying ONLY the installer and the hooks.

    Deliberately no `clockspeed/` and no `tools/`. The installer is the first
    thing a fresh clone runs, so it has to work before either exists.

    Bytes are copied rather than text: `write_text` turns LF into CRLF on
    Windows and `read_text` hides it again, and the installer FAILS a hook that
    carries CRLF - so a text copy would fake a failure that is an artifact of
    the harness.
    """
    root = tmp_path / "clone"
    (root / "scripts").mkdir(parents=True)
    source = REPO_ROOT.joinpath(*INSTALLER_RELATIVE)
    root.joinpath(*INSTALLER_RELATIVE).write_bytes(source.read_bytes())
    if with_hooks:
        (root / ".githooks").mkdir()
        for name in HOOK_NAMES:
            (root / ".githooks" / name).write_bytes((REPO_ROOT / ".githooks" / name).read_bytes())
    if as_repo:
        run_process(["git", "init", "-q"], root)
    return root


def run_installer(root: Path, env_extra: dict[str, str] | None = None):
    """Invoke the sandboxed installer exactly as a fresh clone would."""
    return run_process([sys.executable, str(root.joinpath(*INSTALLER_RELATIVE))], root, env_extra)


def test_installer_runs_with_the_package_and_the_tools_absent(tmp_path):
    # GRANT A CONDITION 2. The installer must not acquire a dependency on the
    # code it exists to protect - it runs before any of it is there.
    root = build_sandbox(tmp_path)
    assert not (root / "clockspeed").exists()
    assert not (root / "tools").exists()

    result = run_installer(root)
    assert result.returncode == 0, combined(result)

    readback = run_process(["git", "config", "--get", "core.hooksPath"], root)
    assert readback.stdout.decode("utf-8", "replace").strip() == ".githooks"


def test_installer_runs_with_the_package_and_the_tools_syntactically_broken(tmp_path):
    # The other half of condition 2. Absent is the easy case; present and
    # UNPARSEABLE is what actually catches an import that was added later.
    root = build_sandbox(tmp_path)
    broken = "def (:\n  this is not python\n"
    for package in ("clockspeed", "tools"):
        (root / package).mkdir()
        (root / package / "__init__.py").write_bytes(broken.encode("ascii"))
    (root / "tools" / "precommit_gate.py").write_bytes(broken.encode("ascii"))

    result = run_installer(root)
    assert result.returncode == 0, combined(result)


def test_installer_second_run_prints_byte_identical_output(tmp_path):
    # GRANT A CONDITION 7. Idempotence the operator can SEE. Compared on raw
    # bytes, not decoded text, so a line-ending change cannot hide here.
    root = build_sandbox(tmp_path)
    first = run_installer(root)
    second = run_installer(root)
    assert first.returncode == second.returncode == 0, combined(first) + combined(second)
    assert first.stdout == second.stdout, "stdout differed between two runs"
    assert first.stderr == second.stderr, "stderr differed between two runs"


def test_installer_missing_hooks_directory_renders_no_absolute_path(tmp_path):
    # GRANT A CONDITION 8, first of the two adjacent non-exception leaks. This
    # message used to interpolate the absolute hooks directory.
    root = build_sandbox(tmp_path, with_hooks=False)
    result = run_installer(root)

    assert result.returncode == 1
    text = combined(result)
    assert "nothing to wire" in text, text
    assert not ABSOLUTE_PATH.search(text), f"an absolute path reached the output:\n{text}"
    assert str(tmp_path) not in text


def test_installer_outside_a_work_tree_withholds_git_stderr(tmp_path):
    # GRANT A CONDITION 8, second leak: git's decoded stderr was rendered
    # verbatim, and git reports absolute paths in it. Also exercises the
    # chained-InstallError renderings that were at :85 and :240.
    root = build_sandbox(tmp_path, as_repo=False)
    result = run_installer(root)

    assert result.returncode == 1
    text = combined(result)
    # Assert what IS there, not merely that something is absent.
    assert "not inside a git work tree" in text, text
    assert "stderr is withheld" in text, text
    # git's own wording must no longer appear anywhere in the output.
    assert "not a git repository" not in text, text
    assert not ABSOLUTE_PATH.search(text), f"an absolute path reached the output:\n{text}"


def test_the_hookspath_readback_check_is_untouched():
    # GRANT A CONDITION 7. Setting a value is not evidence the value took, and
    # this grant does not permit weakening the proof that it did.
    source = REPO_ROOT.joinpath(*INSTALLER_RELATIVE).read_text(encoding="utf-8")
    assert 'readback = run_git_optional(["config", "--get", CONFIG_KEY], root)' in source
    assert "if readback != HOOKS_DIR_NAME:" in source
    assert "did not take: wrote" in source
    assert "The hooks are NOT wired." in source


def test_the_installer_imports_only_the_standard_library():
    # GRANT A CONDITION 2, checked statically as well as by execution: the
    # runtime tests above pass trivially if an import is added but never
    # reached on the happy path.
    source = REPO_ROOT.joinpath(*INSTALLER_RELATIVE).read_text(encoding="utf-8")
    foreign = sorted(name for name in imported_roots(source) if name not in sys.stdlib_module_names)
    assert not foreign, f"the installer must stay dependency-free; it imports {foreign}"


# ---------------------------------------------------------------------------
# tools/precommit_gate.py - grant B conditions 1 to 4
# ---------------------------------------------------------------------------

# Assembled from fragments at runtime. A spelled-out home path in a tracked
# file is itself a violation and the gate would block the commit adding it.
CRASH_MARKER = "C:" + chr(92) + "Users" + chr(92) + "synthetic" + chr(92) + "probe.txt"

# Crashes the gate from OUTSIDE, without adding a test hook to a frozen file.
# The gate does `import argparse` at module level and calls
# argparse.ArgumentParser() inside build_parser(), so replacing that attribute
# on the shared sys.modules entry before runpy re-executes the gate makes
# main() raise before it can do anything else.
CRASH_WRAPPER = """
import argparse
import runpy
import sys

MARKER = {marker!r}


def boom(*args, **kwargs):
    raise RuntimeError("synthetic crash reading " + MARKER)


argparse.ArgumentParser = boom
sys.argv = ["precommit_gate", "--files", "nothing"]
runpy.run_path({gate!r}, run_name="__main__")
"""


def provoke_gate_crash(tmp_path: Path, env_extra: dict[str, str] | None = None):
    """Make the real gate raise a non-SystemExit inside main(), and run it."""
    wrapper = tmp_path / "crash_probe.py"
    wrapper.write_bytes(CRASH_WRAPPER.format(marker=CRASH_MARKER, gate=str(GATE)).encode("ascii"))
    return run_process([sys.executable, str(wrapper)], tmp_path, env_extra)


def test_gate_crash_default_output_carries_no_absolute_path(tmp_path):
    # GRANT B CONDITION 1.
    result = provoke_gate_crash(tmp_path)
    text = combined(result)

    assert "RuntimeError" in text, text
    assert CRASH_MARKER not in text, "the suppressed traceback still reached the output"
    assert not ABSOLUTE_PATH.search(text), f"an absolute path reached the output:\n{text}"
    assert "CLOCKSPEED_CRASH_TRACEBACK" in text, "the default output must NAME the opt-in flag"


def test_gate_crash_exits_one_and_says_it_failed_closed(tmp_path):
    # GRANT B CONDITION 2. A gate that crashes open is worse than no gate.
    result = provoke_gate_crash(tmp_path)
    assert result.returncode == 1, combined(result)
    text = combined(result)
    assert "the gate itself raised" in text, text
    assert "Failing CLOSED with exit 1" in text, text


def test_gate_crash_traceback_opt_in_still_exits_one(tmp_path):
    # GRANT B CONDITION 3. The flag changes what is PRINTED, never whether the
    # gate fails. Asserting the marker DOES appear here is what proves the
    # default above genuinely suppressed something rather than nothing.
    result = provoke_gate_crash(tmp_path, {"CLOCKSPEED_CRASH_TRACEBACK": "1"})
    text = combined(result)

    assert result.returncode == 1, text
    assert CRASH_MARKER in text, "the opt-in did not reveal the traceback"
    assert "Traceback (most recent call last)" in text, text
    assert "the gate itself raised" in text, text


def test_the_crash_traceback_flag_defaults_off_and_is_documented(tmp_path):
    # GRANT B CONDITION 3, the rest of it: a CLOCKSPEED_-prefixed name, in the
    # module docstring, off unless explicitly set to 1.
    source = GATE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    docstring = ast.get_docstring(tree) or ""
    assert "CLOCKSPEED_CRASH_TRACEBACK" in docstring, "the flag is not in the module docstring"
    assert 'ENV_CRASH_TRACEBACK = "CLOCKSPEED_CRASH_TRACEBACK"' in source

    # Off means off: any value other than "1" leaves it suppressed.
    result = provoke_gate_crash(tmp_path, {"CLOCKSPEED_CRASH_TRACEBACK": "0"})
    assert result.returncode == 1
    assert CRASH_MARKER not in combined(result)


def test_the_gate_gained_no_new_import():
    # GRANT B CONDITION 4. The gate has to start in a checkout where the
    # package is mid-edit and not importable, so it is stdlib-only.
    source = GATE.read_text(encoding="utf-8")
    roots = imported_roots(source)
    foreign = sorted(name for name in roots if name not in sys.stdlib_module_names)
    assert not foreign, f"the gate must stay stdlib-only; it imports {foreign}"
    # The rewritten crash handler uses these two. Both were already imported,
    # which is why condition 4 costs nothing.
    assert {"os", "traceback"} <= roots
    # The one non-stdlib name in the file is a guarded probe, not a dependency.
    # Pinned so that turning a probe into a module-level import is a red test
    # rather than a silent new startup requirement.
    assert "ruff" not in roots
    assert "ruff" in guarded_import_probes(source)


# ---------------------------------------------------------------------------
# scripts/install_hooks.py - CS-406, the two leaks grant A and grant B missed
# ---------------------------------------------------------------------------

# Assembled from fragments for the same reason CRASH_MARKER above is: a
# spelled-out home path in a tracked file is itself a violation, and the commit
# gate would block the commit that added it.
INSTALLER_CRASH_MARKER = "C:" + chr(92) + "Users" + chr(92) + "synthetic" + chr(92) + "wire.txt"

# Crashes the installer from OUTSIDE, without adding a test hook to a frozen
# file. The installer does `import subprocess` at module level and calls
# subprocess.run() inside run_git(); run_git() catches only FileNotFoundError,
# OSError and SubprocessError, and both require_work_tree() and main() catch
# only InstallError - so a RuntimeError raised by a replaced subprocess.run
# travels all the way to the __main__ crash handler, which is the site under
# test. Replacing the attribute on the shared sys.modules entry before runpy
# re-executes the installer is what makes this work with the frozen file
# untouched.
INSTALLER_CRASH_WRAPPER = """
import runpy
import subprocess

MARKER = {marker!r}


def boom(*args, **kwargs):
    raise RuntimeError("synthetic crash wiring " + MARKER)


subprocess.run = boom
runpy.run_path({installer!r}, run_name="__main__")
"""


def provoke_installer_crash(tmp_path: Path, env_extra: dict[str, str] | None = None):
    """Make the real installer raise a non-SystemExit inside main(), and run it."""
    wrapper = tmp_path / "installer_crash_probe.py"
    installer = str(REPO_ROOT.joinpath(*INSTALLER_RELATIVE))
    body = INSTALLER_CRASH_WRAPPER.format(marker=INSTALLER_CRASH_MARKER, installer=installer)
    wrapper.write_bytes(body.encode("ascii"))
    return run_process([sys.executable, str(wrapper)], tmp_path, env_extra)


def test_installer_crash_default_output_carries_no_absolute_path(tmp_path):
    # CS-406 CONDITION 1. The crash handler used to call traceback.print_exc()
    # unconditionally, which prints an absolute path PER FRAME - on a clone
    # under a user profile that is the account name, once per frame.
    result = provoke_installer_crash(tmp_path)
    text = combined(result)

    # Assert what IS there, not merely that something is absent.
    assert "RuntimeError" in text, text
    assert "The traceback is suppressed" in text, text
    assert "CLOCKSPEED_CRASH_TRACEBACK" in text, "the default output must NAME the opt-in flag"
    assert INSTALLER_CRASH_MARKER not in text, "the suppressed traceback still reached the output"
    assert not ABSOLUTE_PATH.search(text), f"an absolute path reached the output:\n{text}"


def test_installer_crash_exits_one_and_says_the_hooks_are_not_wired(tmp_path):
    # CS-406 CONDITION 2, the default half. The worst outcome this file has is
    # a fresh clone believing it is protected when it is not, so the crash is
    # reformatted and never swallowed.
    result = provoke_installer_crash(tmp_path)
    assert result.returncode == 1, combined(result)
    assert "the hooks are NOT wired" in combined(result), combined(result)


def test_installer_crash_traceback_opt_in_still_exits_one(tmp_path):
    # CS-406 CONDITION 2, the opt-in half, and the proof that the default above
    # suppressed something rather than nothing: the marker is only reachable
    # through the traceback, and here it must appear.
    result = provoke_installer_crash(tmp_path, {"CLOCKSPEED_CRASH_TRACEBACK": "1"})
    text = combined(result)

    assert result.returncode == 1, text
    assert INSTALLER_CRASH_MARKER in text, "the opt-in did not reveal the traceback"
    assert "Traceback (most recent call last)" in text, text
    assert "the hooks are NOT wired" in text, text


def test_the_installer_crash_flag_defaults_off_and_is_documented(tmp_path):
    # CS-406 CONDITION 3. ONE flag for one concept. The installer cannot import
    # the gate - it is the first thing a fresh clone runs, before tools/ is
    # guaranteed to exist or to parse (grant A condition 2) - so the shared
    # spelling is pinned by this test instead of by an import. Two differently
    # spelled flags for one concept is the drift class CLAUDE.md section 4
    # exists to stop.
    source = REPO_ROOT.joinpath(*INSTALLER_RELATIVE).read_text(encoding="utf-8")
    docstring = ast.get_docstring(ast.parse(source)) or ""
    assert "CLOCKSPEED_CRASH_TRACEBACK" in docstring, "the flag is not in the module docstring"
    assert 'ENV_CRASH_TRACEBACK = "CLOCKSPEED_CRASH_TRACEBACK"' in source
    assert 'ENV_CRASH_TRACEBACK = "CLOCKSPEED_CRASH_TRACEBACK"' in GATE.read_text(encoding="utf-8")

    # Off means off: any value other than "1" leaves it suppressed.
    result = provoke_installer_crash(tmp_path, {"CLOCKSPEED_CRASH_TRACEBACK": "0"})
    assert result.returncode == 1
    assert INSTALLER_CRASH_MARKER not in combined(result)


def test_the_installer_gained_no_new_import():
    # CS-406 CONDITION 4. os and traceback were already imported, which is why
    # the env guard costs nothing. Pinned so that acquiring a dependency to
    # implement the guard would be red rather than silent.
    source = REPO_ROOT.joinpath(*INSTALLER_RELATIVE).read_text(encoding="utf-8")
    roots = imported_roots(source)
    assert {"os", "traceback"} <= roots


# The wiring line, printed at the top of install(). The mechanized sweep above
# is structurally BLIND to this site - it keys on traceback calls and on
# renderings of a caught exception, and this is neither - so these two tests
# are the only thing that guards it. Do not lean on the sweep here.
WIRING_LINE = "wiring .githooks/ at the repository root"

# The installer's closing WARNING block teaches that C:\X and C:/x are
# DIFFERENT config keys. That example is a string LITERAL in the installer's
# source, not a path discovered at runtime, and the oracle above is a
# deliberately dumb "any drive-letter path" regex that cannot tell the two
# apart. It is removed here by EXACT FRAGMENT rather than by loosening the
# regex, so the oracle keeps its full strength over every other byte of the
# report - which is the whole point of having an oracle the remedy does not
# get to define. Assembled from fragments like the markers above.
PATH_KEYING_EXAMPLE = "path-string keying (C:" + chr(92) + "X and C:/x are"


def test_installer_wiring_line_renders_no_absolute_path(tmp_path):
    # CS-406 CONDITIONS 7 TO 10, the exit-0 path. This line used to interpolate
    # the discovered repository root. redact() is NOT the remedy and would be a
    # no-op that looks like a fix: it rewrites a path under a home directory
    # and leaves one that is not under a home directory untouched and still
    # absolute, which is exactly the operator's own pinned root.
    root = build_sandbox(tmp_path)
    result = run_installer(root)
    text = combined(result)

    assert result.returncode == 0, text
    # Assert what IS printed, not merely that something is absent.
    assert WIRING_LINE in text, text
    # If this goes red the warning text moved, and what is stripped below has
    # to be re-examined before it is trusted again.
    assert PATH_KEYING_EXAMPLE in text, "the pedagogical example moved; re-check the strip"
    report = text.replace(PATH_KEYING_EXAMPLE, "")
    assert not ABSOLUTE_PATH.search(report), f"an absolute path reached the output:\n{text}"

    # No DISCOVERED path in any form: the root, its parent, or its basename.
    # The basename is named explicitly because it is the shortcut that looks
    # safe and is not - a clone made directly in a home directory makes
    # root.name the account name.
    assert str(root) not in text
    assert str(tmp_path) not in text
    assert root.name not in text, "the basename is not a safe abbreviation of the root"
    # Non-vacuous: the sandbox root really is a path the oracle WOULD match, so
    # a green here is the remedy rather than a harness that cannot fail.
    assert ABSOLUTE_PATH.search(str(root)), "the sandbox root is not absolute; this proves nothing"


def test_installer_wiring_line_renders_no_absolute_path_on_the_bad_hook_path(tmp_path):
    # CS-406 CONDITION 10, the other half. ROADMAP.md calls this line "the
    # SUCCESS path"; it is not only that. It executes BEFORE the `if failures:`
    # branch, so the exit-1 unusable-hook path prints it too - and that path is
    # where an operator is most likely to paste the output somewhere.
    root = build_sandbox(tmp_path)
    # CRLF is one of the conditions inspect_hook() rejects, and it leaves
    # core.hooksPath set - so the installer reaches the wiring line, prints it,
    # reports the bad hook and exits 1.
    bad = root / ".githooks" / "pre-commit"
    bad.write_bytes(bad.read_bytes().replace(b"\n", b"\r\n"))

    result = run_installer(root)
    text = combined(result)

    assert result.returncode == 1, text
    assert WIRING_LINE in text, text
    assert "FAILED - unusable hook file(s)" in text, text
    assert not ABSOLUTE_PATH.search(text), f"an absolute path reached the output:\n{text}"
    assert str(root) not in text
