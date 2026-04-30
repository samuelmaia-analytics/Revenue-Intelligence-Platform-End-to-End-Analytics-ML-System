"""Backward-compatible import path for processed artifact contracts.

Canonical contract is `contracts.v1.processed_contract`.
"""

from contracts.v1.processed_contract import (  # noqa: F401
    CSV_ARTIFACT_SPECS,
    JSON_ARTIFACT_SPECS,
    PROCESSED_CONTRACT_VERSION,
)
