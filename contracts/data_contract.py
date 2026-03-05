"""Backward-compatible import path for data contracts.

Canonical contract for current API is `contracts.v1.data_contract`.
"""

from contracts.v1.data_contract import (  # noqa: F401
    GOLD_CONTRACT_MODELS,
    DimChannelContract,
    DimCustomersContract,
    DimDateContract,
    FactOrdersContract,
    ScoreInputRecord,
    ScorePrediction,
    ScoreRequest,
    ScoreResponse,
    required_columns_for,
    validate_gold_table,
)
