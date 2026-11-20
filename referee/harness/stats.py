"""``harness.stats``: the two statistics of the harness report (stage 1, P1 row 4; test 28).

Rules: tohum/19 (one-sided Clopper-Pearson lower bound with a real number of successes: ``BetaInv(alpha; x, n - x
+ 1)``; the exact one-sided McNemar test), tohum/29a (the command lines and the tables of values), tohum/26b (no
float in a report: a number with decimals is a string of six decimals).

1. ``cp_lower(x, n, alpha)``: the ``p`` in [0, 1] at which the regularized incomplete beta function ``I_p(x, n - x
   + 1)`` is ``alpha``; 0 when ``x`` is 0. ``x`` is a ``Fraction`` (an integer or not: ``x_eff = recall * G``),
   ``n`` a positive integer, ``0 <= x <= n``, ``alpha`` a ``Fraction`` strictly between 0 and 1; anything else is
   ``ValueError``. Computed in floats (``lgamma`` and the function's continued fraction, then 200 halvings of
   [0, 1]) and returned as a float; ``fixed6`` of it is what a report carries. Bound by test 28's tables (29a: six
   integer rows and the real ``x_eff`` 7,5 of 10, to four decimals) and, for ``x = n``, by the closed form
   ``alpha ** (1 / n)``.
2. ``mcnemar(b, c)``: with ``b`` discordant pairs favouring the old and ``c`` favouring the new, the probability
   of ``c`` or more of ``b + c`` at one half each, ``P(X >= c | Bin(b + c, 1/2))``, an exact ``Fraction`` (1 when
   both are 0). ``b`` and ``c`` are non-negative integers with ``b + c <= MAX_PAIRS``, else ``ValueError``: the
   exact value costs work that grows with the square of ``b + c`` (``min(b + 1, c)`` terms of the binomial row,
   each a number of up to ``b + c`` bits, one from the one before), so the function refuses counts above the
   bound instead of running without one. No count of pairs the seed names is near it (tohum/19: 8 discordant
   pairs, 45 paired cases).
3. ``fixed6(value)``: a non-negative ``Fraction`` rounded to six decimals, half to even, or a float as ``%.6f``,
   as a string.

Work, stated: ``cp_lower`` runs ``HALVINGS`` halvings of at most ``LENTZ_STEPS`` steps each, whatever its
arguments; ``mcnemar`` is bounded by ``MAX_PAIRS`` (rule 2). Measured on the machine this was written on, not
promised for another: ``mcnemar(10000, 10000)`` 0.07 s, the command with those counts under 1 s.

Out of scope, stated: how accurate ``cp_lower`` is beyond what the tables show (four decimals at the rows of 29a;
no bound is claimed for other arguments, e.g. ``n`` in the thousands); two-sided bounds; the paired comparison's
choice of ``b`` and ``c`` (its caller's).

Command line (tohum/29a), run from ``referee/``::

    python -m harness.stats cp_lower <x> <n> <alpha>     ->  {"lb": "0.962400"}
    python -m harness.stats mcnemar <b> <c>              ->  {"p": "0.062500"}

``x`` and ``alpha`` are decimal numbers (``7.5``, ``0.10``), ``n``, ``b`` and ``c`` integers, each in ASCII digits.
Exit 0 with the one JSON line; exit 2 with ``{"ok": false, "error": ...}`` for any other arguments.
"""

from __future__ import annotations

import json
import math
import re
import sys
from fractions import Fraction

import cli

FAULT_LINE = {"ok": False, "error": "internal error"}
DECIMAL = re.compile(r"[0-9]+(\.[0-9]+)?\Z", re.ASCII)
INTEGER = re.compile(r"[0-9]+\Z", re.ASCII)
MAX_DIGITS = 12   # of an argument of the command line: no table needs more, and a count is no big number
MAX_PAIRS = 20000   # mcnemar's b + c (rule 2)
HALVINGS = 200
LENTZ_STEPS = 10000


def fixed6(value: "Fraction | float") -> str:
    """``value`` as a string of six decimals (rule 3)."""
    if isinstance(value, float):
        return "%.6f" % value
    if not isinstance(value, Fraction) or value < 0:
        raise ValueError("fixed6: a non-negative Fraction or a float")
    return "%d.%06d" % divmod(round(value * 10 ** 6), 10 ** 6)


def _fraction_of_tail(a: float, b: float, p: float) -> float:
    """The continued fraction of the incomplete beta function at ``p`` (modified Lentz)."""
    tiny = 1e-300
    c, d = 1.0, 1.0 - (a + b) * p / (a + 1.0)
    d = 1.0 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, LENTZ_STEPS):
        for num in (m * (b - m) * p / ((a + 2 * m - 1) * (a + 2 * m)),
                    -(a + m) * (a + b + m) * p / ((a + 2 * m) * (a + 2 * m + 1))):
            d = 1.0 + num * d
            d = 1.0 / (d if abs(d) > tiny else tiny)
            c = 1.0 + num / c
            c = c if abs(c) > tiny else tiny
            h *= d * c
        if abs(d * c - 1.0) < 1e-15:
            break
    return h


def _betainc(a: float, b: float, p: float) -> float:
    """The regularized incomplete beta function ``I_p(a, b)``, ``a`` and ``b`` positive."""
    if p <= 0.0:
        return 0.0
    if p >= 1.0:
        return 1.0
    front = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(p) + b * math.log1p(-p))
    if p < (a + 1.0) / (a + b + 2.0):
        return front * _fraction_of_tail(a, b, p) / a
    return 1.0 - front * _fraction_of_tail(b, a, 1.0 - p) / b


def cp_lower(x: Fraction, n: int, alpha: Fraction) -> float:
    """The one-sided Clopper-Pearson lower bound (rule 1)."""
    if not (isinstance(x, Fraction) and type(n) is int and isinstance(alpha, Fraction)
            and n >= 1 and 0 <= x <= n and 0 < alpha < 1):
        raise ValueError("cp_lower: 0 <= x <= n, n >= 1, 0 < alpha < 1")
    if x == 0:
        return 0.0
    a, b, level = float(x), float(n - x + 1), float(alpha)
    low, high = 0.0, 1.0
    for _ in range(HALVINGS):
        middle = (low + high) / 2.0
        if _betainc(a, b, middle) < level:
            low = middle
        else:
            high = middle
    return (low + high) / 2.0


def mcnemar(b: int, c: int) -> Fraction:
    """The exact one-sided McNemar probability (rule 2)."""
    if not (type(b) is int and type(c) is int and b >= 0 and c >= 0):
        raise ValueError("mcnemar: two non-negative integers")
    n = b + c
    if n > MAX_PAIRS:
        raise ValueError("mcnemar: b + c is at most %d" % MAX_PAIRS)
    # the tail k = c..n has b + 1 terms, the head k = 0..c-1 has c: the shorter one is summed
    tail = _row_head(n, b + 1) if b + 1 <= c else 2 ** n - _row_head(n, c)
    return Fraction(tail, 2 ** n)


def _row_head(n: int, terms: int) -> int:
    """``C(n, 0) + ... + C(n, terms - 1)``, ``0 <= terms <= n + 1``; the row is symmetric, so this is its tail too."""
    total, term = 0, 1
    for k in range(terms):
        total += term
        term = term * (n - k) // (k + 1)
    return total


def _refuse(message: str) -> int:
    sys.stdout.write(json.dumps({"ok": False, "error": message}) + "\n")
    return 2


def _number(text: str, shape: "re.Pattern[str]") -> Fraction:
    if not shape.match(text) or len(text) > MAX_DIGITS:
        raise ValueError("not a number of this command: at most %d ASCII digits" % MAX_DIGITS)
    return Fraction(text)


def main(argv: list[str]) -> int:
    usage = "usage: harness.stats cp_lower <x> <n> <alpha> | mcnemar <b> <c> (b + c <= %d)" % MAX_PAIRS
    try:
        if len(argv) == 4 and argv[0] == "cp_lower":
            bound = cp_lower(_number(argv[1], DECIMAL), int(_number(argv[2], INTEGER)), _number(argv[3], DECIMAL))
            line = {"lb": fixed6(bound)}
        elif len(argv) == 3 and argv[0] == "mcnemar":
            line = {"p": fixed6(mcnemar(int(_number(argv[1], INTEGER)), int(_number(argv[2], INTEGER))))}
        else:
            return _refuse(usage)
    except ValueError:
        return _refuse(usage)
    sys.stdout.write(json.dumps(line) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(cli.run(main, sys.argv[1:], FAULT_LINE))
