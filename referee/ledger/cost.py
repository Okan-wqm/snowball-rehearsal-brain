"""The ``cost`` section of the loop's ledger as data: its row type, the closed set of outcomes and the spend.

Rules: tohum/26 (``cost`` rows of ``<state_root>/ledger.jsonl``), asama-0/14 MF15 (every call adds a row), asama-0/12
(the stage brake reads the spend), asama-1/13e "Maliyet bölümü" (the section's readers).

Why it is its own module: the section has one writer that calls a model (``dispatcher.llm_call``) and readers that
must not reach one: ``ledger.schema`` (the row's shape) and ``status.block`` (the brake's ``spent``), both on the
import path of the harness's judges (``harness.offline``; asama-0/09 test 9). So the facts every side shares are
here, below both, and ``dispatcher.llm_call`` takes them from here (its names ``PART``, ``KIND``, ``OUTCOMES``,
``Unusable`` and ``spent_micros`` are these objects). This module imports ``ledger.chain`` only.

- ``PART``, ``KIND``: a cost row is ``part: cost``, ``kind: cost``.
- ``OUTCOMES``: the row's ``payload.outcome``, a closed set (what each means is ``dispatcher.llm_call``'s).
- ``micros(value, what, positive=False)``: ``value`` when its type is ``int`` itself (a ``bool`` is not) and it is
  from 0 (1 when ``positive``) to ``ledger.chain.MAX_SAFE_INT``, else ``Unusable`` naming ``what``.
- ``spent_micros(rows)``: the sum of ``payload.usd_micros`` over every ``part: cost`` row; ``Unusable`` when one
  has no such integer. One rule for the brake and for ``status.block``.
"""

from __future__ import annotations

from typing import Any

from ledger import chain

PART = KIND = "cost"
OUTCOMES = ("ok", "outage", "request_rejected", "unresolved", "secret", "brake")


class Unusable(ValueError):
    pass


def micros(value: Any, what: str, positive: bool = False) -> int:
    if type(value) is not int or value < (1 if positive else 0) or value > chain.MAX_SAFE_INT:
        raise Unusable("%s must be an integer %s" % (what, "> 0" if positive else ">= 0"))
    return value


def spent_micros(rows: list[dict]) -> int:
    """The stage's spend; see the module docstring."""
    total = 0
    for row in rows:
        if row.get("part") == PART:
            payload = row.get("payload")
            total += micros(payload.get("usd_micros") if isinstance(payload, dict) else None,
                            "cost row %r usd_micros" % row.get("row_id"))
    return total
