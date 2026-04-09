from pathlib import Path

import pandas as pd
import pytest

from src.analytics_duckdb import build_curated_support_frames_duckdb, duckdb_available
from src.metrics import calculate_cac, cohort_analysis, rfm_segmentation


@pytest.mark.skipif(not duckdb_available(), reason="duckdb not installed")
def test_duckdb_curated_support_frames_match_existing_contract_logic(tmp_path: Path) -> None:
    customers_path = tmp_path / "customers.csv"
    orders_path = tmp_path / "orders.csv"
    marketing_path = tmp_path / "marketing_spend.csv"

    pd.DataFrame(
        {
            "customer_id": [1, 2, 3, 4],
            "signup_date": ["2025-01-05", "2025-01-10", "2025-02-01", "2025-02-18"],
            "channel": ["Organic", "Paid Search", "Organic", "Referral"],
            "segment": ["SMB", "SMB", "Mid-Market", "Enterprise"],
        }
    ).to_csv(customers_path, index=False)
    pd.DataFrame(
        {
            "order_id": ["o1", "o2", "o3", "o4", "o5"],
            "customer_id": [1, 1, 2, 3, 4],
            "order_date": [
                "2025-01-06",
                "2025-02-06",
                "2025-01-21",
                "2025-02-10",
                "2025-03-01",
            ],
            "order_value": [100.0, 120.0, 200.0, 300.0, 900.0],
        }
    ).to_csv(orders_path, index=False)
    pd.DataFrame(
        {
            "channel": ["Organic", "Paid Search", "Referral"],
            "marketing_spend": [50.0, 300.0, 150.0],
        }
    ).to_csv(marketing_path, index=False)

    expected_cac = calculate_cac(marketing_path, customers_path)
    expected_rfm = rfm_segmentation(orders_path, customers_path)
    expected_cohort = cohort_analysis(orders_path, customers_path)

    actual_cac, actual_rfm, actual_cohort = build_curated_support_frames_duckdb(
        customers_path=customers_path,
        orders_path=orders_path,
        marketing_path=marketing_path,
    )

    pd.testing.assert_frame_equal(
        expected_cac.sort_values("channel").reset_index(drop=True),
        actual_cac.sort_values("channel").reset_index(drop=True),
        check_dtype=False,
    )
    pd.testing.assert_frame_equal(
        expected_rfm.sort_values("customer_id").reset_index(drop=True),
        actual_rfm.sort_values("customer_id").reset_index(drop=True),
        check_dtype=False,
    )
    pd.testing.assert_frame_equal(
        expected_cohort.sort_values(["cohort_month", "cohort_index"]).reset_index(drop=True),
        actual_cohort.sort_values(["cohort_month", "cohort_index"]).reset_index(drop=True),
        check_dtype=False,
    )
