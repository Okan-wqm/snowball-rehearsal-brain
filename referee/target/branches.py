"""The target branches the system keeps (tohum/01, asama-0/00 "Veri iki hedefin ``brain/state`` dalında, çalışma dalı
``brain/integration``"): the one place their names are written. Read by ``loop.job`` (D1's heads), ``ledger.append``
(the state writer), ``ledger.schema`` and ``activate``.
"""

STATE = "brain/state"
INTEGRATION = "brain/integration"
