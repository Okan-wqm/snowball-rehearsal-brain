"""``cases.census``: the rule set a target's census is counted over (tohum/26q (10), tohum/29za).

Rules: tohum/26q (10) (``rules_total`` is the rule set of the target's ``census`` vectors, per tool; a target
with no such vector has no count), tohum/29za (the denominator is the seed's set; until a vector file names it
per target "the rule set is on this page": the toy's is the seven ESLint rules its config enables).

``RULES`` is that page's set written here once, by target kind (``targets[].kind`` of the policy): ``toy`` has
seven ``(tool, rule_id)`` pairs. ``rules(kind)`` is the set of a kind, ``None`` for a kind with no vector (the
copy today): the scorer (``harness.score.report``) then gives no count and never ``PASS``.

The seed's vector file (``/vec/cases.json``'s ``census.*`` cases, each one ``cases.build produce TOOL RULE``) is
not read at run time: the set is the referee's own, kept in its tree by the target's kind, and a run reads it
from no vector file, policy, ``state_root`` or target (tohum/29za, "Koşan hakem bir hedefin ``census`` kümesini
nerede bulur" (1): the vector is the set's ground and a test input, not a run input). The
tests (``tests/test_cases.py``) hold the toy's set here to the seven rules written there by hand; only on a
machine that has that vector file does one more test read it and hold the set to exactly the rules its cases ask
for (it is skipped elsewhere: the file is the seed's, not this tree's).

Out of scope, stated: which rules the toy's own config enables at a commit (the set is the seed's, not read
from the target, so a target cannot shrink its own denominator); a set for any other target.
"""
from __future__ import annotations

RULES: dict[str, frozenset[tuple[str, str]]] = {
    "toy": frozenset(("eslint", rule) for rule in (
        "dot-notation", "no-var", "object-shorthand", "operator-assignment", "prefer-const", "prefer-template",
        "yoda")),
}


def rules(kind: object) -> frozenset[tuple[str, str]] | None:
    """The census rule set of a target of this kind; ``None`` when the seed has no ``census`` vector for it."""
    return RULES.get(kind) if isinstance(kind, str) else None
