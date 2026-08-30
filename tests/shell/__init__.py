"""Tests for ``shell/`` - the Electron companion window - graded from Python.

A package for the same reason ``tests/surface`` and ``tests/data`` are: a unique
dotted name per module, so a ``test_shell_assets.py`` here can never collide
during collection with a same-named module added elsewhere later.

WHY THE SHELL IS GRADED FROM PYTHON AT ALL, given ``shell/test/`` already holds
five ``node --test`` suites. Those run on the tier-2 lane, which needs a Node
toolchain present. Everything in this package runs on the tier-1 lane, on every
push, on a machine with no Node, no npm and no electron binary - and it must
never invoke any of them. What it grades is therefore what can be established
from the BYTES of the shipped files: character set, line endings, the absence of
a named token, the count of a call site, and agreement between a constant
spelled on both sides of the language seam.

Three rules bind every module in this directory.

- **Nothing here may run Node.** Not ``node --test``, not ``npm``, not an
  electron binary. A tier-1 arm that shells out to a toolchain is an arm that
  goes red on a clean checkout for a reason that is not a defect.
- **A text scan cannot tell code from comment, and both directions bite.** A
  banned token inside a comment that EXPLAINS the ban is not a violation, and a
  required symbol mentioned only in prose is not an implementation. Every arm
  whose subject is "this token must (not) appear in code" strips comments first,
  and the stripper itself carries planted controls in both directions.
- **An assertion binds a SCALAR before it fires.** pytest renders the asserted
  EXPRESSION independently of the message, so ``assert not findings`` prints the
  findings. Compute the count, then assert on the count.
"""
