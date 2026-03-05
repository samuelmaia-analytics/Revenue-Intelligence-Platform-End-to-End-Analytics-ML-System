from __future__ import annotations

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field


class ScoreInputRecord(BaseModel):
    recency_days: int = Field(ge=0)
    frequency: int = Field(ge=0)
    monetary: float = Field(ge=0)
    avg_order_value: float = Field(ge=0)
    tenure_days: int = Field(ge=0)
    arpu: float = Field(ge=0)
    channel: str = Field(min_length=1)
    segment: str = Field(min_length=1)


class ScoreRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    records: list[ScoreInputRecord] = Field(min_length=1, max_length=1000)


class ScorePrediction(BaseModel):
    churn_probability: float
    next_purchase_probability: float
    suggested_action: str


class ScoreResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    model_versions: dict[str, str]
    predictions: list[ScorePrediction]


class DimCustomersContract(BaseModel):
    customer_id: int
    signup_date: str
    channel: str
    segment: str


class DimDateContract(BaseModel):
    date_key: int
    date: str
    year: int
    month: int
    week_of_year: int
    day_of_week: str


class DimChannelContract(BaseModel):
    channel_key: int
    channel: str


class FactOrdersContract(BaseModel):
    order_id: str
    customer_id: int
    channel_key: int
    date_key: int
    order_date: str
    order_amount: float
    order_count: int


GOLD_CONTRACT_MODELS: dict[str, type[BaseModel]] = {
    "dim_customers.csv": DimCustomersContract,
    "dim_date.csv": DimDateContract,
    "dim_channel.csv": DimChannelContract,
    "fact_orders.csv": FactOrdersContract,
}


def required_columns_for(table_name: str) -> set[str]:
    contract = GOLD_CONTRACT_MODELS[table_name]
    return set(contract.model_fields.keys())


def validate_gold_table(df: pd.DataFrame, table_name: str) -> None:
    required_cols = required_columns_for(table_name)
    missing = required_cols.difference(df.columns)
    if missing:
        missing_cols = ", ".join(sorted(missing))
        raise ValueError(f"{table_name} missing required columns: {missing_cols}")
