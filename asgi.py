"""Create App"""

from __future__ import annotations

from dataspaces_entities.logging import setup_logging
from dataspaces_entities.main import create_app

setup_logging()
app = create_app()
