"""Clockspeed: a deterministic, local, terse, read-only build advisor.

Clockspeed reads a single-player factory-building game's own shipped data files
and the player's save file, computes exact production mathematics, and issues
terse, context-aware, actionable advice about what to build next.

Four properties define it, and each one is a constraint on every module below
this package (BOOTSTRAP.md section 1):

Deterministic:
    No language model, no cloud service and no API key anywhere in the advice
    path. Every recommendation is reproducible from the same inputs. Two runs
    over the same save that disagree is a bug, not variance. Advice arithmetic
    is exact rational arithmetic (fractions.Fraction), never floating point.

Local:
    Everything runs on this machine. Nothing is uploaded, ever.

Terse:
    One line of advice by default. The complete derivation is available on
    demand and is genuinely complete when asked for. Three tiers, not two and
    not four: headline, one-line reason, full derivation.

Read-only against the game:
    Clockspeed never writes to the game install and never modifies a save
    file. Not once, not for anything. A save is also a personal-data-bearing
    artifact: its header embeds a platform account identifier and the player's
    display name in plaintext, so no save, and nothing derived from a save
    header, is ever committed, logged unredacted or placed in a fixture.

What Clockspeed is NOT: a mod, a cheat, a wiki, a chat interface, or anything
that injects into or reads the game process memory.

Version:
    ``__version__`` below is the single source of truth for the project
    version. pyproject.toml declares ``dynamic = ["version"]`` and reads this
    attribute at build time, so the number exists in exactly one place - a
    restated number is a number that will drift (CONVENTIONS.md section 2).
    tests/test_scaffold.py asserts that wiring in both directions.
"""

# SEAM DISCIPLINE (BOOTSTRAP.md section 6).
# Each layer consumes only the layer below it through a stated model.
# solve/ never reads a save. advisor/ never reads the raw docs file.
# surface/ never computes. A layer that reaches past its neighbor is a
# design bug.
#
# The stack, lowest first:
#   data/      the game install, read-only  -> the normalized registry
#   save/      a COPY of a save file        -> the world model
#   solve/     registry                     -> exact production mathematics
#   audit/     world model + solve          -> findings
#   progress/  world model + registry       -> a dependency-ordered plan
#   advisor/   audit + progress + solve     -> traced advice cards
#   surface/   cards and models             -> JSON and pixels, nothing more
#
# This package's own __init__ imports nothing. Importing "clockspeed" must
# stay free: it must not read a file, touch the game install, or pull in a
# subpackage. Anything that costs is imported by the caller that needs it.

__all__ = ["__version__"]

__version__ = "0.1.0"
