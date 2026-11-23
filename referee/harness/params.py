"""``harness.params``: the one judge of the values of ``policy.json`` that stage 1 reads: the harness's five and
the watcher's thirteen thresholds (tohum/29v "Döngüde eksik anahtar", tohum/26h "Harness'in politika değerleri",
tohum/01c "Politikanın sayıları", tohum/28a's seven paths, tohum/18a's rows).

The paths are ``policy.reads``' constants and every lookup goes through ``policy.reads.at`` (the one reader: a key
of the same name at the root or in another section is not that key). What is judged here is the value.

Rules (each bound by a test in ``tests/test_policy_reads.py``, class ``Harness``):

1. A **count** is a JSON integer of 1 or more (a boolean is not one; a float, ``3.0`` too, is not one). A
   **fraction** is a string of tohum/01c's form, ``0.`` and exactly six digits, that is not ``0.000000`` (so
   strictly between 0 and 1); its value is that decimal as an exact ``Fraction`` (``"0.900000"`` is 9/10). A JSON
   number at a fraction's path, whatever its value, is not one. ``FRACTIONS`` names the four paths that hold a
   fraction; every other path of ``JUDGED`` (``policy.reads.HARNESS_PATHS`` and ``GOZCU_PATHS``) holds a count.
2. ``value(policy, path)`` for a path of ``JUDGED``: the count or the ``Fraction`` there. A value off rule 1, or
   ``policy.reads.at`` finding no object on the way (``Malformed``), is ``Invalid`` with the one reason
   ``policy_invalid:<dotted path>``. An absent path: the same ``Invalid`` when the path is one of
   ``policy.reads.REQUIRED`` (stage 1's twelve), so no caller is ever handed ``None`` for a required path;
   ``None`` when it is one of the other six (the watcher's thresholds no page of stage 1 requires: its rule is
   ``unjudged``, tohum/28a). ``count`` and ``fraction`` are the two halves by name, same rules.
3. ``check(policy)``: rule 2 on every path of ``JUDGED``, in that order; the reasons of all that fail (``[]``
   when none). ``usable(policy)`` raises ``Invalid`` with them. This is the whole policy's judgement the loop
   makes before it writes (``loop.cek.assemble`` and ``loop.job.yaz_policy``).
4. ``alpha(policy)`` is ``1 - fraction`` of ``constitutional.confidence_level``, exact (alpha of ``"0.900000"``
   is 1/10: tohum/19, one-sided). ``score(policy)``: the three keyword arguments ``harness.score.report`` takes
   from the policy: ``alpha``, ``window`` (``match_window_lines``) and ``ref_max_lines``
   (``evidence_ref_max_lines``). ``Invalid`` carries every reason that holds, in that order.
5. ``planted_max_cases(policy)``: rule 2 on its path; ``snapshot.make``'s ``max_cases``.

The readers: no caller in the loop for ``score`` today (the scorer is off the live path, tohum/26q (6);
``tests/test_score.Composed`` composes it with the report), ``loop.cek.assemble`` (``usable``, ``planted_max_cases``),
``loop.job.yaz_policy`` (``check``) and ``gozcu.evaluate.thresholds`` (``value`` on its thirteen paths: one rule
for a count and for a fraction of the policy, not a second copy there).

Outside, stated: the word for an absent required path is ``policy_invalid:<path>``, the one reason the seed gives
a policy value (tohum/01c, 26h); no page gives absence its own. ``census_min_groups`` is judged here (rules 2 and
3) and handed to no consumer: its reader is ``exit.sample`` (tohum/26h), not built. An upper bound on a count (no
page has one); a window of 0 (refused: tohum/26h, 1 or more). A float elsewhere in the file (tohum/01c refuses it
at the reader of its path; the paths outside ``JUDGED`` are their readers'; ``dispatcher.llm_call.policy_usd``
still takes a JSON fraction of USD, founder ledger "open").
"""

from __future__ import annotations

import re
from fractions import Fraction
from typing import Any

from policy import reads as R

SCORE = (("window", R.MATCH_WINDOW_LINES), ("ref_max_lines", R.EVIDENCE_REF_MAX_LINES))
JUDGED = R.HARNESS_PATHS + R.GOZCU_PATHS
FRACTIONS = (R.CONFIDENCE_LEVEL, R.REGRESSION_REVERT_RATE, R.DRIFT_BOUND, R.SEAT_SIMILARITY)
_FRACTION = re.compile(r"0\.[0-9]{6}", re.ASCII)


class Invalid(ValueError):
    """A value of the policy the loop cannot use; ``reasons`` names each path."""

    def __init__(self, reasons: list[str]):
        super().__init__("; ".join(reasons))
        self.reasons = reasons


def _reason(path: tuple[str, ...]) -> str:
    return "policy_invalid:%s" % R.dotted(path)


def _at(policy: Any, path: tuple[str, ...]) -> Any:
    """``policy.reads.at``'s value, ``None`` for an absent path outside ``REQUIRED`` (rule 2)."""
    try:
        found = R.at(policy, path)
    except R.Malformed:
        raise Invalid([_reason(path)]) from None
    if found is not R.ABSENT:
        return found
    if path in R.REQUIRED:
        raise Invalid([_reason(path)])
    return R.ABSENT


def count(policy: Any, path: tuple[str, ...]) -> int | None:
    """The positive integer at ``path`` (rules 1 and 2)."""
    found = _at(policy, path)
    if found is R.ABSENT:
        return None
    if type(found) is not int or found < 1:
        raise Invalid([_reason(path)])
    return found


def fraction(policy: Any, path: tuple[str, ...]) -> Fraction | None:
    """The six-decimal string strictly between 0 and 1 at ``path``, exact (rules 1 and 2)."""
    found = _at(policy, path)
    if found is R.ABSENT:
        return None
    if not (isinstance(found, str) and _FRACTION.fullmatch(found)) or not int(found[2:]):
        raise Invalid([_reason(path)])
    return Fraction(found)


def value(policy: Any, path: tuple[str, ...]) -> Any:
    """The judged value at a path of ``JUDGED``: a fraction's for ``FRACTIONS``, else a count's (rule 2)."""
    return (fraction if path in FRACTIONS else count)(policy, path)


def check(policy: Any) -> list[str]:
    """The reasons of every path of ``JUDGED`` that is off its rule, required and absent included (rule 3)."""
    reasons: list[str] = []
    for path in JUDGED:
        try:
            value(policy, path)
        except Invalid as exc:
            reasons += exc.reasons
    return reasons


def usable(policy: Any) -> None:
    """``Invalid`` with ``check``'s reasons when there is one (rule 3)."""
    reasons = check(policy)
    if reasons:
        raise Invalid(reasons)


def alpha(policy: Any) -> Fraction:
    """``1 - confidence_level``, exact (rule 4)."""
    return 1 - fraction(policy, R.CONFIDENCE_LEVEL)


def score(policy: Any) -> dict[str, Any]:
    """``{alpha, window, ref_max_lines}`` for ``harness.score.report`` (rule 4)."""
    out: dict[str, Any] = {}
    reasons: list[str] = []
    for name, read in (("alpha", alpha),) + tuple((n, lambda p, path=path: count(p, path)) for n, path in SCORE):
        try:
            out[name] = read(policy)
        except Invalid as exc:
            reasons += exc.reasons
    if reasons:
        raise Invalid(reasons)
    return out


def planted_max_cases(policy: Any) -> int:
    """``snapshot.make``'s ``max_cases`` (rule 5)."""
    return count(policy, R.PLANTED_MAX_CASES)
