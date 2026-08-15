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

WHAT IS NOT A RENDERING, and this half is load-bearing. A NAMED FIELD is safe
and must not be flagged:

    NAME.reason, NAME.msg, NAME.lineno, NAME.colno, NAME.strerror
    getattr(NAME, "msg", None)      default is not the object
    type(NAME).__name__
    raise SomeError(...) from NAME  chaining, not rendering
    helper(NAME)                    a per-type redaction allowlist

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

REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALLER_RELATIVE = ("scripts", "install_hooks.py")
GATE = REPO_ROOT / "tools" / "precommit_gate.py"
HOOK_NAMES = ("pre-commit", "commit-msg", "pre-push")
SUBPROCESS_TIMEOUT = 120

# Any Windows absolute path, in either slash direction. Used as the oracle for
# "did this output leak a path", independently of the redactor being tested -
# a redactor is blind exactly where it is blind, so it can never be its own
# oracle.
ABSOLUTE_PATH = re.compile(r"[A-Za-z]:[\\/]")

# Builtins that render their whole argument as text.
TEXT_BUILTINS = frozenset({"str", "repr", "ascii", "format"})

# `getattr(obj, "name", default)` - three arguments is the shape with a
# fallback, and the fallback is where the object sneaks back in.
GETATTR_WITH_DEFAULT = 3

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
    "scripts/install_hooks.py": (
        "CS-205 grant A covers that file's exception RENDERINGS. The adjudicator "
        "granted the suppress-by-default remedy for the gate's traceback under a "
        "SEPARATE grant B, on the reasoning that a traceback is a different "
        "remedy from a redaction - so the installer's crash handler needs its own "
        "grant and is not self-granted here. Named, not silently left."
    ),
    "tests/save/test_header.py": (
        "A redaction-ASSERTION helper: _exception_surfaces() collects str, repr, "
        "args, notes and the formatted traceback precisely so the test can assert "
        "none of them carries personal data. The rendering is the subject under "
        "test, and the exception is a parameter rather than a caught object."
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


class RenderVisitor(ast.NodeVisitor):
    """Flag whole-object renderings of a name bound by `except ... as NAME`.

    Scoping to the handler body is what separates a leak from the redaction
    helpers themselves: `safe_exc_text(exc)` takes the exception as a
    PARAMETER, so its own `str(exc)` is outside every handler and is the
    sanctioned boundary rather than an exemption written into this detector.
    """

    def __init__(self, path: str) -> None:
        """Start a scan of one file, identified by its repo-relative path."""
        self.path = path
        self.bound: list[str] = []
        self.found: list[Rendering] = []
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
            name = self.bound_name(part.value)
            if name is not None:
                conversion = CONVERSIONS.get(part.conversion, "!?")
                self.flag(part.value, f"f-string {{{name}{conversion}}}")
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
        """
        self.visit(node.test)
        guarded = any(
            isinstance(sub, ast.Name | ast.Attribute)
            and getattr(sub, "id", getattr(sub, "attr", "")) == "environ"
            for sub in ast.walk(node.test)
        )
        self.env_guard_depth += int(guarded)
        for child in node.body:
            self.visit(child)
        self.env_guard_depth -= int(guarded)
        for child in node.orelse:
            self.visit(child)

    def visit_BinOp(self, node: ast.BinOp) -> None:
        """Percent formatting - `"...%s" % exc` and `"..." % (a, exc)`."""
        if isinstance(node.op, ast.Mod):
            right = node.right
            operands = right.elts if isinstance(right, ast.Tuple) else [right]
            for operand in operands:
                name = self.bound_name(operand)
                if name is not None:
                    self.flag(operand, f"percent-format {name}")
        self.generic_visit(node)

    def check_text_builtin(self, node: ast.Call) -> None:
        """`str(exc)`, `repr(exc)`, `ascii(exc)`, `format(exc)`."""
        func = node.func
        if not isinstance(func, ast.Name) or func.id not in TEXT_BUILTINS:
            return
        for arg in node.args:
            name = self.bound_name(arg)
            if name is not None:
                self.flag(arg, f"{func.id}({name})")

    def check_str_format(self, node: ast.Call) -> None:
        """`"...".format(exc)`, positionally or as a keyword value."""
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr != "format":
            return
        for arg in [*node.args, *(kw.value for kw in node.keywords)]:
            name = self.bound_name(arg)
            if name is not None:
                self.flag(arg, f".format({name})")

    def check_getattr_default(self, node: ast.Call) -> None:
        """`getattr(exc, "field", exc)` - the object as the FALLBACK value."""
        func = node.func
        if not isinstance(func, ast.Name) or func.id != "getattr":
            return
        if len(node.args) != GETATTR_WITH_DEFAULT:
            return
        name = self.bound_name(node.args[2])
        if name is not None:
            self.flag(node.args[2], f"getattr default {name}")

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
    )
    seen = {line.strip() for line in completed.stdout.splitlines() if line.strip()}
    return sorted(seen)


def scan_source(path: str, source: str) -> RenderVisitor:
    """Scan one module's source and return the visitor holding its findings."""
    visitor = RenderVisitor(path)
    visitor.visit(ast.parse(source))
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
    leaks = [finding for finding in found if finding.path not in WAIVED_FILES]
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
# The waiver, and the residual the sweep does not assert on
# ---------------------------------------------------------------------------


def test_every_waiver_is_still_live():
    found, _ = scan_repo()
    by_path = {finding.path for finding in found}
    stale = sorted(path for path in WAIVED_FILES if path not in by_path)
    assert not stale, (
        "a waiver outlived the code it describes, which turns it into a silent "
        "exemption. Delete these entries from WAIVED_FILES:\n"
        + "\n".join(f"  {path}" for path in stale)
    )


def test_both_crash_handlers_suppress_their_traceback_by_default():
    # GRANT B's pattern, asserted structurally at both places it applies. A
    # traceback renders an absolute path per frame and ends in str(exc), so it
    # can only be suppressed, never redacted.
    for relative in ("tools/precommit_gate.py", "tools/edit_lint_check.py"):
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
