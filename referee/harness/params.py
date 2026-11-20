"""``harness.params``: the harness's five values of ``policy.json``, read from their paths and judged (stage 1;
tohum/29v's five paths of stage 1, tohum/18a's rows, tohum/26e "Puanlama").

The paths are ``policy.reads``' constants and every lookup goes through ``policy.reads.at`` (the one reader: a key
of the same name at the root or in another section is not that key). What is judged here is the value.

Rules (each bound by a test in ``tests/test_policy_reads.py``, class ``Harness``):

1. ``count(policy, path)``: ``None`` when the path is absent; the value when it is an integer of 1 or more (a
   boolean is not one); else ``Invalid`` with the one reason ``policy_invalid:<dotted path>``. ``Invalid`` with
   the same reason when ``policy.reads.at`` finds no object on the way (``Malformed``).
2. ``alpha(policy)``: ``None`` when ``constitutional.confidence_level`` is absent; else the level must be a JSON
   fraction (a Python ``float``) strictly between 0 and 1, and the answer is ``1 - level`` as an exact
   ``Fraction``, the level read as the shortest decimal Python writes for the float (``repr``; ``0.9`` is 9/10,
   so alpha is 1/10: tohum/19, one-sided). Anything else is ``Invalid`` as in rule 1.
3. ``score(policy)``: the four keyword arguments ``harness.score.report`` takes from the policy: ``alpha`` (rule
   2), ``min_groups`` (``census_min_groups``), ``window`` (``match_window_lines``) and ``ref_max_lines``
   (``evidence_ref_max_lines``), the last three by rule 1. ``Invalid`` carries every reason that holds, in that
   order.
4. ``planted_max_cases(policy)``: rule 1 on its path; ``snapshot.make``'s ``max_cases``.

The readers: ``loop.job.yaz_harness`` (``score``) and ``loop.cek.assemble`` (``planted_max_cases``).

Outside, stated: a default (an absent key leaves the argument ``None`` and the consumer says what that means:
no bound, ``min_groups_unknown``, the symbol alone, no length rule, ``max_cases_invalid`` for a planted
snapshot); an upper bound on a count; a window of 0 (refused here: tohum/18a's row is a window of lines around a
hunk, and no page gives 0 a meaning); "or all there are" of ``census_min_groups`` (tohum/18a: the exit sample's
judgement, ``exit.sample``, not built).
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any

from policy import reads as R

SCORE = (("min_groups", R.CENSUS_MIN_GROUPS), ("window", R.MATCH_WINDOW_LINES),
         ("ref_max_lines", R.EVIDENCE_REF_MAX_LINES))


class Invalid(ValueError):
    """A value of the policy the harness cannot use; ``reasons`` names each path."""

    def __init__(self, reasons: list[str]):
        super().__init__("; ".join(reasons))
        self.reasons = reasons


def _reason(path: tuple[str, ...]) -> str:
    return "policy_invalid:%s" % R.dotted(path)


def _at(policy: Any, path: tuple[str, ...]) -> Any:
    try:
        return R.at(policy, path)
    except R.Malformed:
        raise Invalid([_reason(path)]) from None


def count(policy: Any, path: tuple[str, ...]) -> int | None:
    """The positive integer at ``path``, ``None`` when absent (rule 1)."""
    value = _at(policy, path)
    if value is R.ABSENT:
        return None
    if type(value) is not int or value < 1:
        raise Invalid([_reason(path)])
    return value


def alpha(policy: Any) -> Fraction | None:
    """``1 - confidence_level``, exact; ``None`` when absent (rule 2)."""
    level = _at(policy, R.CONFIDENCE_LEVEL)
    if level is R.ABSENT:
        return None
    if type(level) is not float or not 0 < level < 1:
        raise Invalid([_reason(R.CONFIDENCE_LEVEL)])
    return 1 - Fraction(repr(level))


def score(policy: Any) -> dict[str, Any]:
    """``{alpha, min_groups, window, ref_max_lines}`` for ``harness.score.report`` (rule 3)."""
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


def planted_max_cases(policy: Any) -> int | None:
    """``snapshot.make``'s ``max_cases`` (rule 4)."""
    return count(policy, R.PLANTED_MAX_CASES)
