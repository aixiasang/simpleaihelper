"""
simpleaihelper - A high-performance wrapper for OpenAI API interactions

This package provides efficient interfaces for interacting with OpenAI's API,
with support for single requests, streaming, sessions, and persistent storage.
"""

from .client import AI
from .session import Session
from .db.sqlite_manager import SQLiteManager
from .db.json_manager import JSONManager

__version__ = "0.1.0"
__all__ = ["AI", "Session", "SQLiteManager", "JSONManager"] 