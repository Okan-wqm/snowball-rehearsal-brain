"""The target branches the system keeps (tohum/01, asama-0/00 "Veri iki hedefin ``brain/state`` dalında, çalışma dalı
``brain/integration``"): the one place their names are written. Read by ``loop.job`` (D1's heads), ``ledger.append``
(the state writer), ``ledger.schema`` and ``activate``. Also the names of ``brain/state``'s chained files (tohum/01b:
``chain/*`` and ``ledger.jsonl`` are append only; tohum/26, tohum/27a), written by ``ledger.append`` and
``ledger.anchor`` and read by ``loop.state`` (D1's ``verify --previous`` and its root check).
"""

STATE = "brain/state"
INTEGRATION = "brain/integration"

STATE_LEDGER = "ledger.jsonl"
STATE_ROOTS = "chain/root.jsonl"
STATE_CHAINS = (STATE_LEDGER, STATE_ROOTS)
