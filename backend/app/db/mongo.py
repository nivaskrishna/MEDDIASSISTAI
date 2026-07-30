"""
MongoDB Atlas Connection — DISABLED on macOS Python 3.9 + LibreSSL 2.8.3

LibreSSL 2.8.3 (macOS system Python) cannot complete TLS handshakes with
MongoDB Atlas. Every connection attempt blocks for 8 seconds before failing,
which causes the entire analyze endpoint to timeout from the frontend.

This module is intentionally disabled until running under Python 3.11+
(brew install python@3.11) which ships with OpenSSL 3.x.

Impact: Cloud history sync is disabled. All other features work normally.
        Recent Analyses continue to work via browser localStorage.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def _get_client():
    logger.debug("[MongoDB] Disabled — LibreSSL 2.8.3 incompatible with Atlas TLS 1.3")
    return None


async def ping_mongo() -> bool:
    logger.info(
        "[MongoDB] ℹ️  Atlas sync disabled (LibreSSL 2.8.3 on Python 3.9). "
        "All other features work normally. Recent Analyses stored in localStorage."
    )
    return False


def get_mongo_db():
    return None


def get_collection(name: str):
    return None
