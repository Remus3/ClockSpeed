---
name: no-language-model-in-the-advice-path
description: The advisor is fully deterministic and local - zero language model, cloud service or API key anywhere in the advice path.
metadata:
  type: project
---

The advisor is fully deterministic and local. There is zero language-model dependency, zero
cloud service and zero API key anywhere in the advice path. Every recommendation is
reproducible from the same inputs, and **two runs on the same save that disagree constitute
a bug**, not variance to be tolerated or averaged away.

Concretely: do not propose an LLM-backed explainer, an LLM summarizer, an LLM ranker, or an
LLM tiebreaker for advice. This is a settled decision with a fence around it, recorded so
the argument is not rebuilt from scratch in a later session.

**The reason none is needed** - this is the load-bearing half, not the prohibition. The
tier-3 derivation is GENERATED from the same rule execution trace that produced tier 1 (the
headline) and tier 2 (the one-line reason). One trace, three projections. Because the
explanation is a projection of the trace rather than a retelling of it, it cannot drift
from the advice it explains. A generative explainer would be solving a problem the trace
already solved, and would reintroduce exactly the drift the trace design eliminates - the
explanation quietly disagreeing with the number.

Tier 3 is a learning surface, not a debug dump: every input read with its source, every
rule that fired, every number computed, and every alternative considered with why it was
rejected. It is never hand-written. Three separately authored renderings of the same advice
is the failure mode this design exists to prevent.

**Why:** Determinism is one of the four properties that define this product. An advisor the
operator cannot trust to give the same answer twice is not an advisor, it is a suggestion
box - and the operator would have to verify every card by hand, which spends the scarcest
resource in the system. Local-only also means nothing is uploaded, which matters because
save-derived state is personal data.

**How to apply:** When a hard ranking, phrasing or summarization problem appears, solve it
in the rule engine and the trace, not with a model. If an explanation is unclear, enrich
what the rule declares as its inputs so the trace projects better prose - do not layer a
writer on top. Treat any proposal to add a model, a network call or an API key to the
advice path as already refuted, and cite this fence rather than re-arguing it.

Related: [[unknown-content-is-flagged-not-fatal]], [[save-files-carry-pii]],
[[operator-attention-is-the-budget]].
