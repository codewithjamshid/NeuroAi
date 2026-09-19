"""Imports every module's SQLAlchemy models so `Base.metadata` is complete.

Used by alembic/env.py (autogenerate) and app.main (relationship resolution at startup).
One line per module, keep alphabetical.
"""

from app.modules.patients import models as _patients  # noqa: F401
from app.modules.protocols import models as _protocols  # noqa: F401
from app.modules.sessions import models as _sessions  # noqa: F401
from app.modules.users import models as _users  # noqa: F401
