"""Registry provenance for the doors that price a figure from the registry (CS-1315).

Owns: the ``build_state`` and ``warnings`` members ``/api/power``,
``/api/solve`` and ``/api/optimize`` add to their 200 bodies - the CS-1315
slice B contract recorded in ``docs/LEDGER.md`` before the code, served under
the CS-1316 shape that ``clockspeed/surface/api/map.py`` serves.

WHY THESE THREE DOORS. Every figure each of them answers with - a nameplate
draw, a machine count, a score - is priced from the registry, and the registry
is built from the INSTALLED docs file, which a game patch can change before the
pin moves. The acceptance of CS-1315 ends "nothing prices a figure from an
unverified registry silently", so each body says whether its registry was
verified against the pinned docs hash, and serves the audit's own code when it
was not.

THE SURFACE COMPARES NOTHING. The one comparison is
``clockspeed.audit.build.registry_check_of``, which holds the registry's
source hash beside the pinned docs hash; this module calls it and copies what
it returns. No hash is computed or compared here, and
``tests/surface/test_registry_state_served.py`` asserts that on the AST.

THE PIN IS READ AT CALL TIME, as ``clockspeed.data.version.DOCS_SHA256`` - a
module attribute read inside :func:`registry_state`, never bound by a
``from ... import``, on the precedent ``clockspeed/surface/providers.py`` set.
An empty pin is handed over as it reads; the audit layer treats it as absent.

NO REGISTRY IS NOT A CASE HERE. All three doors answer 503 before a registry
is needed, so a 200 body always has one and ``registry_verified`` is always a
bool on them; the CS-1316 shape's null belongs to ``/api/map``, which answers
200 without one.
"""

# SEAM DISCIPLINE (BOOTSTRAP.md section 6).
# Each layer consumes only the layer below it through a stated model.
# solve/ never reads a save. advisor/ never reads the raw docs file.
# surface/ never computes. A layer that reaches past its neighbor is a
# design bug.
#
# NOT AN ENDPOINT MODULE. It publishes no route, so the rule in
# clockspeed/surface/api/routes.py that an endpoint imports none of its
# siblings is not reached by importing it - it is a helper on the terms
# clockspeed/surface/api/contract.py is one. The audit layer sits below the
# surface (clockspeed/surface/__init__.py enumerates it), so naming its build
# check is consuming a neighbour rather than reaching past one.

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from clockspeed.audit import build as build_model
from clockspeed.data import version

if TYPE_CHECKING:
    from clockspeed.data.registry import Registry

__all__ = [
    "BUILD_STATE_KEYS",
    "DATA_KEYS",
    "WARNING_KEYS",
    "WARNING_SOURCES",
    "registry_state",
]

#: The two members a pricing body gains, in the order they are added.
DATA_KEYS: Final = ("build_state", "warnings")

#: The build state's keys on these doors. ``registry_verified`` is
#: ``RegistryCheck.matches`` copied. The save-build keys ``/api/map`` serves are
#: absent: no save reaches these doors, so there is no save build to state.
BUILD_STATE_KEYS: Final = ("registry_verified",)

#: One served warning row's keys - the CS-977 shape CS-1316 kept.
WARNING_KEYS: Final = ("source", "code", "count")

#: Every source a warning row on these doors may carry: the audit's build source.
WARNING_SOURCES: Final = (build_model.SOURCE_BUILD,)


def registry_state(registry: Registry) -> dict[str, object]:
    """The registry's provenance, as the audit layer states it, for one body.

    Args:
        registry: The normalized registry the door priced from.

    Returns:
        A mapping keyed by :data:`DATA_KEYS`: the build state keyed by
        :data:`BUILD_STATE_KEYS`, and one row keyed by :data:`WARNING_KEYS` per
        code the audit raised - ``registry-mismatch`` or
        ``registry-unverified`` verbatim, at its own count - or none when the
        registry was built from the pinned docs bytes.
    """
    checked = build_model.registry_check_of(registry, pinned_docs_sha256=version.DOCS_SHA256)
    return {
        "build_state": {"registry_verified": checked.matches},
        "warnings": [
            {"source": warning.source, "code": warning.code, "count": warning.count}
            for warning in checked.warnings
        ],
    }
