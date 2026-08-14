---
name: seven-bit-ascii-is-a-hard-rule
description: Why 7-bit ASCII in authored content is a hard rule and not a style preference, plus the safe commit-message path.
metadata:
  type: reference
---

All authored content is 7-bit ASCII: code, comments, docstrings, markdown, commit
messages, shell scripts and chat output. No em-dash (U+2014), no en-dash (U+2013), no
smart quotes (U+2018, U+2019, U+201C, U+201D), no arrows, no box drawing, no emoji. Use a
spaced hyphen " - " for a clause break.

**The mechanism, which is the part worth remembering.** Windows PowerShell 5.1 ANSI-decodes
a `.ps1` file that has no byte-order mark. A UTF-8 em-dash is a multi-byte sequence; under
ANSI decoding those bytes are reinterpreted as separate single-byte characters. When the
em-dash sits inside a double-quoted string, one of the resulting characters is treated by
the tokenizer as a string terminator. The string ends early, the rest of the line is parsed
as code, and the failure cascades into a parse error somewhere well away from the actual
character. The error message points at the wrong place, so the cost is not the typo - it is
the debugging.

One incident of exactly this made the rule permanent. It is a correctness rule about a
decoder, not a typographic preference, which is why it is enforced by a pre-commit
character-set gate rather than left to review.

**Commit messages with special characters:** write the message to a temp file and use
`git commit -F <file>`. Never a double-quoted here-string and never a piped string - both
carry BOM and ANSI mangling risk on this platform, which is the same failure class arriving
through a different door. A single-quoted here-string is acceptable where a file is
genuinely impractical.

Two related Windows encoding facts that bite in the same neighbourhood:

- `write_text` converts LF to CRLF on Windows and `read_text` hides it, so byte counts and
  hash comparisons lie. Write bytes explicitly whenever the byte count matters.
- Set `PYTHONUTF8=1` and `PYTHONIOENCODING=utf-8` in the environment so subprocess output
  does not mojibake.

Verification is by bytes, not by eye: read the file as bytes and assert no byte exceeds
126. A visual scan passes non-ASCII characters that render identically to ASCII ones.

Related: [[hook-presence-is-not-hook-firing]], [[verification-failure-classes]].
