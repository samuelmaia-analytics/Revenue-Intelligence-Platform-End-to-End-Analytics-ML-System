from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.io_utils import atomic_write_csv, atomic_write_json

STATUS_CANCELED = {"canceled", "unavailable"}


def _read_optional_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)


def _safe_ratio(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    return numerator / denominator.replace(0, np.nan)


def _coalesce_columns(frame: pd.DataFrame, base_name: str) -> pd.DataFrame:
    if base_name in frame.columns:
        return frame
    left = f"{base_name}_x"
    right = f"{base_name}_y"
    if left in frame.columns or right in frame.columns:
        primary = frame[right] if right in frame.columns else pd.Series(index=frame.index, dtype=object)
        fallback = frame[left] if left in frame.columns else pd.Series(index=frame.index, dtype=object)
        frame[base_name] = primary.fillna(fallback)
        frame = frame.drop(columns=[left, right], errors="ignore")
    return frame


def _quantile_score(series: pd.Series, ascending: bool = True) -> pd.Series:
    ranked = series.rank(method="first", ascending=ascending)
    if ranked.nunique() < 4:
        return pd.Series([1] * len(series), index=series.index)
    return pd.qcut(ranked, 4, labels=[1, 2, 3, 4]).astype(int)


def _rfm_label(row: pd.Series) -> str:
    score = int(row["rfm_total"])
    if score >= 10:
        return "Champions"
    if score >= 8:
        return "Loyal"
    if int(row["r_score"]) <= 2:
        return "At Risk"
    return "Hibernating"


def _build_customer_analytics(
    customers: pd.DataFrame,
    scored_df: pd.DataFrame,
    recommendations: pd.DataFrame,
) -> pd.DataFrame:
    customer_analytics = customers.merge(
        scored_df[
            [
                "customer_id",
                "recency_days",
                "frequency",
                "monetary",
                "avg_order_value",
                "total_freight",
                "delivered_orders",
                "canceled_orders",
                "avg_review_score",
                "late_order_rate",
                "avg_delivery_days",
                "arpu",
                "ltv_proxy",
                "churn_risk_proxy",
                "next_purchase_propensity_proxy",
                "churn_probability",
                "next_purchase_probability",
            ]
        ],
        on="customer_id",
        how="left",
    ).merge(
        recommendations[
            [
                "customer_id",
                "ltv",
                "cac",
                "ltv_cac_ratio",
                "strategic_score",
                "recommended_action",
            ]
        ],
        on="customer_id",
        how="left",
    )
    for column in [
        "avg_review_score",
        "late_order_rate",
        "delivered_orders",
        "canceled_orders",
        "total_freight",
    ]:
        customer_analytics = _coalesce_columns(customer_analytics, column)
    customer_analytics["repeat_customer_flag"] = (customer_analytics["frequency"] >= 2).astype(int)
    customer_analytics["health_score"] = (
        0.35 * (1 - customer_analytics["churn_probability"].fillna(0))
        + 0.30 * customer_analytics["next_purchase_probability"].fillna(0)
        + 0.20 * np.clip(customer_analytics["avg_review_score"].fillna(0) / 5, 0, 1)
        + 0.15 * (1 - customer_analytics["late_order_rate"].fillna(0).clip(0, 1))
    ).clip(0, 1)
    return customer_analytics.sort_values(
        ["strategic_score", "ltv_proxy"], ascending=[False, False]
    ).reset_index(drop=True)


def _build_payment_analytics(orders: pd.DataFrame) -> pd.DataFrame:
    payment = (
        orders.groupby("payment_type")
        .agg(
            total_orders=("order_id", "nunique"),
            total_revenue=("order_value", "sum"),
            total_freight=("freight_value", "sum"),
            avg_ticket=("order_value", "mean"),
            avg_installments=("payment_installments", "mean"),
            review_score=("review_score", "mean"),
            late_delivery_rate=("is_late", "mean"),
            cancellation_rate=("is_canceled", "mean"),
        )
        .reset_index()
        .rename(columns={"payment_type": "channel"})
    )
    payment["revenue_share_pct"] = (
        payment["total_revenue"] / payment["total_revenue"].sum()
    ).fillna(0)
    payment["freight_share_pct"] = _safe_ratio(
        payment["total_freight"], payment["total_revenue"]
    ).fillna(0)
    payment["on_time_delivery_rate"] = (1 - payment["late_delivery_rate"]).clip(0, 1)
    payment["review_promoter_rate"] = np.clip(payment["review_score"] / 5, 0, 1)
    return payment.sort_values("total_revenue", ascending=False).reset_index(drop=True)


def _build_geographic_analytics(orders: pd.DataFrame) -> pd.DataFrame:
    geography = (
        orders.groupby("customer_state")
        .agg(
            total_orders=("order_id", "nunique"),
            unique_customers=("customer_id", "nunique"),
            total_revenue=("order_value", "sum"),
            total_freight=("freight_value", "sum"),
            avg_ticket=("order_value", "mean"),
            avg_delivery_days=("delivery_days", "mean"),
            late_delivery_rate=("is_late", "mean"),
            avg_review_score=("review_score", "mean"),
        )
        .reset_index()
        .rename(columns={"customer_state": "state"})
    )
    geography["revenue_share_pct"] = (
        geography["total_revenue"] / geography["total_revenue"].sum()
    ).fillna(0)
    geography["revenue_per_customer"] = _safe_ratio(
        geography["total_revenue"], geography["unique_customers"]
    ).fillna(0)
    geography["on_time_delivery_rate"] = (1 - geography["late_delivery_rate"]).clip(0, 1)
    return geography.sort_values("total_revenue", ascending=False).reset_index(drop=True)


def _build_logistics_analytics(orders: pd.DataFrame) -> pd.DataFrame:
    logistics = orders.copy()
    logistics["order_month"] = pd.to_datetime(logistics["order_purchase_timestamp"]).dt.to_period("M").astype(str)
    monthly = (
        logistics.groupby("order_month")
        .agg(
            total_orders=("order_id", "nunique"),
            delivered_orders=("is_delivered", "sum"),
            canceled_orders=("is_canceled", "sum"),
            avg_delivery_days=("delivery_days", "mean"),
            median_delivery_days=("delivery_days", "median"),
            estimated_delivery_days=("estimated_delivery_days", "mean"),
            late_delivery_rate=("is_late", "mean"),
            avg_review_score=("review_score", "mean"),
        )
        .reset_index()
    )
    monthly["delivery_gap_days"] = (
        monthly["avg_delivery_days"] - monthly["estimated_delivery_days"]
    ).fillna(0)
    monthly["on_time_delivery_rate"] = (1 - monthly["late_delivery_rate"]).clip(0, 1)
    monthly["review_promoter_rate"] = np.clip(monthly["avg_review_score"] / 5, 0, 1)
    return monthly.sort_values("order_month").reset_index(drop=True)


def _build_executive_summary_layer(orders: pd.DataFrame) -> pd.DataFrame:
    monthly = orders.copy()
    monthly["order_month"] = pd.to_datetime(monthly["order_purchase_timestamp"]).dt.to_period("M").astype(str)
    repeat_customer_lookup = (
        monthly.groupby("customer_id")["order_id"].nunique().ge(2).rename("repeat_customer_flag")
    )
    monthly = monthly.merge(
        repeat_customer_lookup,
        left_on="customer_id",
        right_index=True,
        how="left",
    )
    summary = (
        monthly.groupby("order_month")
        .agg(
            total_revenue=("order_value", "sum"),
            total_orders=("order_id", "nunique"),
            unique_customers=("customer_id", "nunique"),
            total_freight=("freight_value", "sum"),
            avg_ticket=("order_value", "mean"),
            avg_review_score=("review_score", "mean"),
            late_delivery_rate=("is_late", "mean"),
            cancellation_rate=("is_canceled", "mean"),
            repeat_customer_rate=("repeat_customer_flag", "mean"),
            repeat_revenue=("order_value", lambda values: values[monthly.loc[values.index, "repeat_customer_flag"].fillna(False)].sum()),
        )
        .reset_index()
    )
    summary["revenue_growth_pct"] = summary["total_revenue"].pct_change().replace([np.inf, -np.inf], np.nan)
    summary["orders_growth_pct"] = summary["total_orders"].pct_change().replace([np.inf, -np.inf], np.nan)
    summary["freight_share_pct"] = _safe_ratio(summary["total_freight"], summary["total_revenue"]).fillna(0)
    summary["repeat_revenue_share"] = _safe_ratio(
        summary["repeat_revenue"], summary["total_revenue"]
    ).fillna(0)
    summary["on_time_delivery_rate"] = (1 - summary["late_delivery_rate"]).clip(0, 1)
    return summary.sort_values("order_month").reset_index(drop=True)


def _build_seller_and_product_analytics(
    order_items: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if order_items.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    seller = (
        order_items.groupby(["seller_id", "seller_state"])
        .agg(
            total_orders=("order_id", "nunique"),
            total_items=("order_item_id", "count"),
            total_revenue=("line_revenue", "sum"),
            merchandise_value=("price", "sum"),
            freight_value=("freight_value", "sum"),
            avg_review_score=("review_score", "mean"),
            late_delivery_rate=("delivery_delay_days", lambda values: (values > 0).mean()),
        )
        .reset_index()
    )
    seller["revenue_share_pct"] = (seller["total_revenue"] / seller["total_revenue"].sum()).fillna(0)
    seller["freight_share_pct"] = _safe_ratio(seller["freight_value"], seller["total_revenue"]).fillna(0)
    seller["on_time_delivery_rate"] = (1 - seller["late_delivery_rate"]).clip(0, 1)
    seller = seller.sort_values("total_revenue", ascending=False).reset_index(drop=True)

    product = (
        order_items.groupby(["product_id", "category_name_english"])
        .agg(
            total_orders=("order_id", "nunique"),
            total_items=("order_item_id", "count"),
            total_revenue=("line_revenue", "sum"),
            merchandise_value=("price", "sum"),
            freight_value=("freight_value", "sum"),
            avg_review_score=("review_score", "mean"),
            avg_product_weight_g=("product_weight_g", "mean"),
        )
        .reset_index()
    )
    product["revenue_share_pct"] = (product["total_revenue"] / product["total_revenue"].sum()).fillna(0)
    product["avg_ticket"] = _safe_ratio(product["total_revenue"], product["total_orders"]).fillna(0)
    product = product.sort_values("total_revenue", ascending=False).reset_index(drop=True)

    category = (
        order_items.groupby("category_name_english")
        .agg(
            total_products=("product_id", "nunique"),
            total_orders=("order_id", "nunique"),
            total_items=("order_item_id", "count"),
            total_revenue=("line_revenue", "sum"),
            freight_value=("freight_value", "sum"),
            avg_review_score=("review_score", "mean"),
            late_delivery_rate=("delivery_delay_days", lambda values: (values > 0).mean()),
        )
        .reset_index()
        .rename(columns={"category_name_english": "category"})
    )
    category["revenue_share_pct"] = (
        category["total_revenue"] / category["total_revenue"].sum()
    ).fillna(0)
    category["freight_share_pct"] = _safe_ratio(
        category["freight_value"], category["total_revenue"]
    ).fillna(0)
    category["avg_ticket"] = _safe_ratio(category["total_revenue"], category["total_orders"]).fillna(0)
    category["on_time_delivery_rate"] = (1 - category["late_delivery_rate"]).clip(0, 1)
    category = category.sort_values("total_revenue", ascending=False).reset_index(drop=True)
    return seller, product, category


def _build_rfm_table(customer_analytics: pd.DataFrame) -> pd.DataFrame:
    rfm = customer_analytics[
        ["customer_id", "channel", "recency_days", "frequency", "monetary", "segment"]
    ].copy()
    rfm = rfm.rename(columns={"recency_days": "recency"})
    rfm["r_score"] = _quantile_score(rfm["recency"], ascending=False)
    rfm["f_score"] = _quantile_score(rfm["frequency"], ascending=True)
    rfm["m_score"] = _quantile_score(rfm["monetary"], ascending=True)
    rfm["rfm_total"] = rfm[["r_score", "f_score", "m_score"]].sum(axis=1)
    rfm["segment"] = rfm.apply(_rfm_label, axis=1)
    return rfm.sort_values("rfm_total", ascending=False).reset_index(drop=True)


def _risk_band(series: pd.Series) -> pd.Series:
    return pd.cut(
        series.fillna(0),
        bins=[-0.001, 0.35, 0.65, 1.0],
        labels=["Low", "Medium", "High"],
    ).astype(str)


def _tier_from_percentile(series: pd.Series, high_label: str, mid_label: str, base_label: str) -> pd.Series:
    if series.nunique() < 3:
        return pd.Series([base_label] * len(series), index=series.index)
    thresholds = series.quantile([0.5, 0.8]).to_dict()
    return pd.Series(
        np.select(
            [
                series >= thresholds[0.8],
                series >= thresholds[0.5],
            ],
            [high_label, mid_label],
            default=base_label,
        ),
        index=series.index,
    )


def _build_customer_segment_health(customer_analytics: pd.DataFrame) -> pd.DataFrame:
    customer_frame = customer_analytics.copy()
    customer_frame["churn_risk_band"] = _risk_band(customer_frame["churn_probability"])
    grouped = (
        customer_frame.groupby(["recommended_action", "rfm_segment", "churn_risk_band"])
        .agg(
            customers=("customer_id", "nunique"),
            revenue_proxy=("monetary", "sum"),
            avg_ltv=("ltv", "mean"),
            avg_ticket=("avg_order_value", "mean"),
            avg_churn_probability=("churn_probability", "mean"),
            avg_next_purchase_probability=("next_purchase_probability", "mean"),
            avg_health_score=("health_score", "mean"),
        )
        .reset_index()
    )
    grouped["customer_share_pct"] = _safe_ratio(
        grouped["customers"], pd.Series([grouped["customers"].sum()] * len(grouped))
    ).fillna(0)
    return grouped.sort_values(["revenue_proxy", "customers"], ascending=[False, False]).reset_index(drop=True)


def _build_retention_scorecard(cohort: pd.DataFrame) -> pd.DataFrame:
    if cohort.empty:
        return cohort
    scorecard = cohort.copy()
    scorecard["cohort_month"] = scorecard["cohort_month"].astype(str)
    scorecard["retained_customers_pct"] = scorecard["retention_rate"].fillna(0)
    return scorecard.sort_values(["cohort_month", "cohort_index"]).reset_index(drop=True)


def _build_executive_scorecard(
    *,
    executive_kpis: dict[str, object],
    customer_analytics: pd.DataFrame,
    category_analytics: pd.DataFrame,
    seller_analytics: pd.DataFrame,
    geographic_analytics: pd.DataFrame,
    payment_analytics: pd.DataFrame,
    logistics_analytics: pd.DataFrame,
    cohort: pd.DataFrame,
) -> pd.DataFrame:
    high_risk = customer_analytics["churn_probability"].fillna(0) >= 0.7
    top_state = executive_kpis.get("top_state", {})
    top_category = executive_kpis.get("top_category", {})
    top_seller = executive_kpis.get("top_seller", {})
    latest_ops = logistics_analytics.sort_values("order_month").tail(1)
    m1_retention = cohort.loc[cohort["cohort_index"].eq(1), "retention_rate"]
    scorecard = pd.DataFrame(
        [
            {
                "snapshot_date": pd.Timestamp.utcnow().date().isoformat(),
                "total_revenue": executive_kpis.get("total_revenue", 0.0),
                "total_orders": executive_kpis.get("total_orders", 0),
                "average_ticket": executive_kpis.get("average_ticket", 0.0),
                "recurring_customer_rate": executive_kpis.get("recurring_customer_rate", 0.0),
                "repeat_revenue_share": float(
                    customer_analytics.loc[customer_analytics["frequency"] >= 2, "monetary"].sum()
                    / max(customer_analytics["monetary"].sum(), 1.0)
                ),
                "late_delivery_rate": executive_kpis.get("late_delivery_rate", 0.0),
                "on_time_delivery_rate": executive_kpis.get("on_time_delivery_rate", 0.0),
                "avg_delivery_days": executive_kpis.get("avg_delivery_days", 0.0),
                "avg_review_score": executive_kpis.get("avg_review_score", 0.0),
                "review_promoter_rate": executive_kpis.get("review_promoter_rate", 0.0),
                "high_churn_risk_customer_pct": float(high_risk.mean()),
                "high_churn_risk_revenue_pct": float(
                    customer_analytics.loc[high_risk, "monetary"].sum()
                    / max(customer_analytics["monetary"].sum(), 1.0)
                ),
                "m1_retention_rate": float(m1_retention.mean()) if not m1_retention.empty else 0.0,
                "seller_top10_revenue_share": float(seller_analytics.head(10)["revenue_share_pct"].sum())
                if not seller_analytics.empty
                else 0.0,
                "category_top10_revenue_share": float(category_analytics.head(10)["revenue_share_pct"].sum())
                if not category_analytics.empty
                else 0.0,
                "top_state": top_state.get("state", "n/a") if isinstance(top_state, dict) else "n/a",
                "top_state_revenue_share": top_state.get("revenue_share_pct", 0.0)
                if isinstance(top_state, dict)
                else 0.0,
                "top_category": top_category.get("category", "n/a") if isinstance(top_category, dict) else "n/a",
                "top_category_revenue_share": top_category.get("revenue_share_pct", 0.0)
                if isinstance(top_category, dict)
                else 0.0,
                "top_seller": top_seller.get("seller_id", "n/a") if isinstance(top_seller, dict) else "n/a",
                "top_payment_channel": payment_analytics.head(1)["channel"].iat[0]
                if not payment_analytics.empty
                else "n/a",
                "latest_month_orders": float(latest_ops["total_orders"].iat[0]) if not latest_ops.empty else 0.0,
            }
        ]
    )
    return scorecard


def _build_seller_scorecard(seller_analytics: pd.DataFrame) -> pd.DataFrame:
    if seller_analytics.empty:
        return seller_analytics
    scorecard = seller_analytics.copy()
    scorecard["seller_tier"] = _tier_from_percentile(
        scorecard["total_revenue"], "Strategic", "Core", "Long Tail"
    )
    scorecard["seller_risk_band"] = _risk_band(scorecard["late_delivery_rate"].clip(0, 1))
    return scorecard


def _build_category_scorecard(category_analytics: pd.DataFrame) -> pd.DataFrame:
    if category_analytics.empty:
        return category_analytics
    scorecard = category_analytics.copy()
    scorecard["category_tier"] = _tier_from_percentile(
        scorecard["total_revenue"], "Hero", "Core", "Tail"
    )
    scorecard["category_risk_band"] = _risk_band(scorecard["late_delivery_rate"].clip(0, 1))
    return scorecard


def _build_state_scorecard(geographic_analytics: pd.DataFrame) -> pd.DataFrame:
    if geographic_analytics.empty:
        return geographic_analytics
    scorecard = geographic_analytics.copy()
    scorecard["state_tier"] = _tier_from_percentile(
        scorecard["total_revenue"], "Anchor", "Growth", "Emerging"
    )
    scorecard["state_risk_band"] = _risk_band(scorecard["late_delivery_rate"].clip(0, 1))
    return scorecard


def build_marketplace_outputs(
    *,
    silver_customers_path: Path,
    silver_orders_path: Path,
    processed_dir: Path,
    scored_df: pd.DataFrame,
    recommendations_df: pd.DataFrame,
    cohort_df: pd.DataFrame,
) -> dict[str, Any]:
    silver_dir = silver_customers_path.parent
    customer_columns = pd.read_csv(silver_customers_path, nrows=0).columns.tolist()
    customers = pd.read_csv(
        silver_customers_path,
        parse_dates=[column for column in ["signup_date", "latest_order_at"] if column in customer_columns],
    )
    order_columns = pd.read_csv(silver_orders_path, nrows=0).columns.tolist()
    orders = pd.read_csv(
        silver_orders_path,
        parse_dates=[
            column
            for column in [
                "order_date",
                "order_purchase_timestamp",
                "order_approved_at",
                "order_delivered_carrier_date",
                "order_delivered_customer_date",
                "order_estimated_delivery_date",
            ]
            if column in order_columns
        ],
    )
    order_items = _read_optional_csv(silver_dir / "silver_order_items.csv")
    order_defaults = {
        "order_purchase_timestamp": orders["order_date"] if "order_date" in orders.columns else pd.NaT,
        "freight_value": 0.0,
        "payment_installments": 0,
        "review_score": 0.0,
        "is_late": 0.0,
        "is_canceled": 0,
        "is_delivered": 1,
        "delivery_days": 0.0,
        "estimated_delivery_days": 0.0,
        "payment_type": orders["channel"] if "channel" in orders.columns else "Other",
        "order_status": "delivered",
    }
    for column, default_value in order_defaults.items():
        if column not in orders.columns:
            orders[column] = default_value
    if "customer_state" not in orders.columns:
        if "customer_state" in customers.columns:
            orders = orders.merge(
                customers[["customer_id", "customer_state"]].drop_duplicates(subset=["customer_id"]),
                on="customer_id",
                how="left",
            )
        else:
            orders["customer_state"] = "Unknown"

    customer_analytics = _build_customer_analytics(customers, scored_df, recommendations_df)
    rfm = _build_rfm_table(customer_analytics)
    customer_analytics = customer_analytics.merge(
        rfm[["customer_id", "rfm_total", "segment"]].rename(columns={"segment": "rfm_segment"}),
        on="customer_id",
        how="left",
    )
    payment_analytics = _build_payment_analytics(orders)
    geographic_analytics = _build_geographic_analytics(orders)
    logistics_analytics = _build_logistics_analytics(orders)
    executive_summary_layer = _build_executive_summary_layer(orders)
    seller_analytics, product_analytics, category_analytics = _build_seller_and_product_analytics(
        order_items
    )
    customer_segment_health = _build_customer_segment_health(customer_analytics)
    retention_scorecard = _build_retention_scorecard(cohort_df)
    seller_scorecard = _build_seller_scorecard(seller_analytics)
    category_scorecard = _build_category_scorecard(category_analytics)
    state_scorecard = _build_state_scorecard(geographic_analytics)

    recurring_customers = int((customer_analytics["frequency"] >= 2).sum())
    total_customers = max(int(customer_analytics["customer_id"].nunique()), 1)
    delivered_orders = orders[orders["order_status"].eq("delivered")].copy()
    in_progress = (
        orders.loc[~orders["order_status"].isin(["delivered", *STATUS_CANCELED])]
        .groupby("order_status")["order_id"]
        .nunique()
        .to_dict()
    )
    executive_kpis = {
        "revenue_proxy": float(delivered_orders["order_value"].sum()),
        "total_revenue": float(delivered_orders["order_value"].sum()),
        "total_orders": int(orders["order_id"].nunique()),
        "delivered_orders": int(delivered_orders["order_id"].nunique()),
        "average_ticket": float(delivered_orders["order_value"].mean()),
        "total_freight": float(delivered_orders["freight_value"].sum()),
        "avg_freight": float(delivered_orders["freight_value"].mean()),
        "unique_customers": total_customers,
        "recurring_customers": recurring_customers,
        "recurring_customer_rate": recurring_customers / total_customers,
        "avg_delivery_days": float(delivered_orders["delivery_days"].mean()),
        "late_delivery_rate": float(delivered_orders["is_late"].mean()),
        "on_time_delivery_rate": float(1 - delivered_orders["is_late"].mean()),
        "cancellations": int(orders["is_canceled"].sum()),
        "cancellation_rate": float(orders["is_canceled"].mean()),
        "orders_in_progress": {str(key): int(value) for key, value in in_progress.items()},
        "avg_review_score": float(delivered_orders["review_score"].mean()),
        "review_promoter_rate": float((delivered_orders["review_score"].fillna(0) >= 4).mean()),
        "avg_ltv": float(customer_analytics["ltv"].mean()),
        "avg_cac": float(customer_analytics["cac"].mean()),
        "avg_ltv_cac_ratio": float(customer_analytics["ltv_cac_ratio"].mean()),
        "high_churn_risk_pct": float((customer_analytics["churn_probability"] >= 0.7).mean()),
        "portfolio_size": total_customers,
        "repeat_revenue_share": float(
            customer_analytics.loc[customer_analytics["frequency"] >= 2, "monetary"].sum()
            / max(customer_analytics["monetary"].sum(), 1.0)
        ),
        "m1_retention_rate": float(
            retention_scorecard.loc[retention_scorecard["cohort_index"].eq(1), "retention_rate"].mean()
        )
        if not retention_scorecard.empty
        else 0.0,
        "seller_top10_revenue_share": float(seller_analytics.head(10)["revenue_share_pct"].sum())
        if not seller_analytics.empty
        else 0.0,
        "category_top10_revenue_share": float(category_analytics.head(10)["revenue_share_pct"].sum())
        if not category_analytics.empty
        else 0.0,
        "best_channel_efficiency": payment_analytics.sort_values("revenue_share_pct", ascending=False)
        .head(1)[["channel", "revenue_share_pct"]]
        .to_dict(orient="records")[0],
        "top_category": category_analytics.head(1).to_dict(orient="records")[0]
        if not category_analytics.empty
        else {},
        "top_seller": seller_analytics.head(1).to_dict(orient="records")[0]
        if not seller_analytics.empty
        else {},
        "top_state": geographic_analytics.head(1).to_dict(orient="records")[0]
        if not geographic_analytics.empty
        else {},
    }
    executive_scorecard = _build_executive_scorecard(
        executive_kpis=executive_kpis,
        customer_analytics=customer_analytics,
        category_analytics=category_analytics,
        seller_analytics=seller_analytics,
        geographic_analytics=geographic_analytics,
        payment_analytics=payment_analytics,
        logistics_analytics=logistics_analytics,
        cohort=retention_scorecard,
    )

    atomic_write_csv(processed_dir / "customer_analytics.csv", customer_analytics)
    atomic_write_csv(processed_dir / "payment_analytics.csv", payment_analytics)
    atomic_write_csv(processed_dir / "geographic_analytics.csv", geographic_analytics)
    atomic_write_csv(processed_dir / "logistics_analytics.csv", logistics_analytics)
    atomic_write_csv(processed_dir / "executive_summary_layer.csv", executive_summary_layer)
    atomic_write_csv(processed_dir / "rfm_segments.csv", rfm)
    atomic_write_csv(processed_dir / "executive_scorecard.csv", executive_scorecard)
    atomic_write_csv(processed_dir / "customer_segment_health.csv", customer_segment_health)
    atomic_write_csv(processed_dir / "payment_scorecard.csv", payment_analytics)
    atomic_write_csv(processed_dir / "retention_scorecard.csv", retention_scorecard)
    if not seller_analytics.empty:
        atomic_write_csv(processed_dir / "seller_analytics.csv", seller_analytics)
        atomic_write_csv(processed_dir / "seller_scorecard.csv", seller_scorecard)
    if not product_analytics.empty:
        atomic_write_csv(processed_dir / "product_analytics.csv", product_analytics)
    if not category_analytics.empty:
        atomic_write_csv(processed_dir / "category_analytics.csv", category_analytics)
        atomic_write_csv(processed_dir / "category_scorecard.csv", category_scorecard)
    if not state_scorecard.empty:
        atomic_write_csv(processed_dir / "state_scorecard.csv", state_scorecard)
    if not logistics_analytics.empty:
        atomic_write_csv(processed_dir / "operations_scorecard.csv", logistics_analytics)
    atomic_write_json(processed_dir / "executive_kpis.json", executive_kpis)

    return {
        "executive_kpis": executive_kpis,
        "customer_analytics": customer_analytics,
        "payment_analytics": payment_analytics,
        "geographic_analytics": geographic_analytics,
        "logistics_analytics": logistics_analytics,
        "executive_summary_layer": executive_summary_layer,
        "seller_analytics": seller_analytics,
        "product_analytics": product_analytics,
        "category_analytics": category_analytics,
        "rfm": rfm,
        "executive_scorecard": executive_scorecard,
        "customer_segment_health": customer_segment_health,
        "retention_scorecard": retention_scorecard,
        "seller_scorecard": seller_scorecard,
        "category_scorecard": category_scorecard,
        "state_scorecard": state_scorecard,
    }
