"""The target branches the system keeps (tohum/01, asama-0/00 "Veri iki hedefin ``brain/state`` dalında, çalışma dalı
``brain/integration``"): the one place their names are written. Read by ``loop.job`` (D1's heads), ``ledger.append``
(the state writer), ``ledger.schema`` and ``activate``. Also the names of ``brain/state``'s chained files (tohum/01b:
``chain/*`` and ``ledger.jsonl`` are append only; tohum/26, tohum/27a), written by ``ledger.append`` and
``ledger.anchor`` and read by ``loop.state`` (D1's ``verify --previous`` and its root check), and of its
``status.md`` (asama-0/14 row 16), written by ``status.block`` and carried by D1 to D6 (``loop.pulled``).

``CHECK`` is the name of the check run the referee writes on a candidate's head before merging it into
``brain/integration`` (``target.land``, called by ``activate`` and D6 of ``yaz``): tohum/25a row 3's required
check of ``brain/integration``'s ruleset, "adı ``snowball-gate``".
"""

STATE = "brain/state"
INTEGRATION = "brain/integration"

STATE_LEDGER = "ledger.jsonl"
STATE_ROOTS = "chain/root.jsonl"
STATE_CHAINS = (STATE_LEDGER, STATE_ROOTS)
STATE_STATUS = "status.md"

CHECK = "snowball-gate"
