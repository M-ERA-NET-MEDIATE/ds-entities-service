"""SOFT models."""

from __future__ import annotations

import re

from .auth import DSAPIRole
from .service_errors import HTTPError

URI_REGEX = re.compile(r"^(?P<namespace>https?://.+)/(?P<version>\d(?:\.\d+){0,2})/(?P<name>[^/#?]+)$")
"""Regular expression to parse a SOFT entity URI."""

__all__ = ("URI_REGEX", "DSAPIRole", "HTTPError")
