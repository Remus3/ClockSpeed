---
name: a-guard-can-be-accepted-and-unscoped
description: A tool accepting a scoped configuration key is not evidence it applies only where you named; probe inside AND outside the scope.
metadata:
  type: reference
---

# A guard can be accepted and still unscoped

**A tool accepting your configuration key is not evidence the key does what you asked.**
Acceptance and scoping are two different claims, and the failure mode is that the tool
takes the setting, applies it somewhere WIDER than you named, and reports success.

## The measurement behind this

Session 3, on the pinned mypy. `pyproject.toml` carried a per-module override:

```
[[tool.mypy.overrides]]
module = ["clockspeed.solve.*"]
strict = true
```

That is accepted with no warning. It also turns the strict flags on GLOBALLY. Measured on
the tree: the block alone produced 25 errors in `tests/data/test_blobs.py`, a file the
pattern `clockspeed.solve.*` cannot match, while removing the block was clean.

The trap is that the obvious differential test PASSES. Replacing `strict` with a bogus key
in the same position gives `Unrecognized option`, so `strict` looks validated by contrast.
That test proves the key is RECOGNIZED. It says nothing about where it is APPLIED.

The fix is to write out the per-module-settable constituents, which do scope:
`check_untyped_defs`, `disallow_any_generics`, `disallow_incomplete_defs`,
`disallow_subclassing_any`, `disallow_untyped_calls`, `disallow_untyped_decorators`,
`disallow_untyped_defs`, `extra_checks`, `no_implicit_reexport`, `strict_equality`,
`warn_return_any`, `warn_unused_ignores`. `warn_unused_configs` and `warn_redundant_casts`
are global-only and belong in the global block.

## The general test - two probes, not one

A scoping claim needs a NEGATIVE probe as well as a positive one. Put the SAME violating
code in a location the rule should cover and one it should not, and require the results to
DIFFER:

- violation inside the named scope -> must fail
- identical violation outside it   -> must pass
- both clean                       -> the rule is inert
- both fail                        -> the rule is not scoped, whatever the tool said

Only the third and fourth outcomes are visible, and only if you run both probes. One probe
inside the scope is green-and-meaningless: it cannot distinguish "correctly scoped" from
"applied to everything".

This generalizes past mypy - per-file lint ignores, per-path CI filters, per-directory
formatter settings, per-module log levels, and any tool with a glob. Related:
[[hook-presence-is-not-hook-firing]], which is the same shape one level up - a gate that
exists but never runs - and [[verification-failure-classes]].
