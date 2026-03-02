from pathlib import Path
import json

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_recall_curve, roc_auc_score, roc_curve
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def _build_preprocessor(df: pd.DataFrame) -> tuple[ColumnTransformer, list[str], list[str]]:
    numeric_features = [
        "recency_days",
        "frequency",
        "monetary",
        "avg_order_value",
        "tenure_days",
        "arpu",
    ]
    categorical_features = ["channel", "segment"]
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numeric_features),
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
        ]
    )
    return preprocessor, numeric_features, categorical_features


def _safe_roc_auc(y_true: pd.Series, y_prob: np.ndarray) -> float:
    if y_true.nunique() < 2:
        return float("nan")
    return float(roc_auc_score(y_true, y_prob))


def _temporal_split_indices(df: pd.DataFrame, split_ratio: float = 0.8) -> tuple[pd.Index, pd.Index]:
    ordered_idx = df.sort_values("signup_date").index
    split_at = int(len(ordered_idx) * split_ratio)
    split_at = max(1, min(split_at, len(ordered_idx) - 1))
    train_idx = ordered_idx[:split_at]
    test_idx = ordered_idx[split_at:]
    return train_idx, test_idx


def _build_evaluation_split(df: pd.DataFrame, y: pd.Series) -> tuple[pd.Index, pd.Index, str]:
    train_idx, test_idx = _temporal_split_indices(df)
    y_train, y_test = y.loc[train_idx], y.loc[test_idx]
    if y_train.nunique() > 1 and y_test.nunique() > 1:
        return train_idx, test_idx, "temporal"

    train_idx, test_idx = train_test_split(
        y.index, test_size=0.2, random_state=42, stratify=y
    )
    return pd.Index(train_idx), pd.Index(test_idx), "stratified_fallback"


def _evaluate_pipeline_temporal(
    pipeline: Pipeline, x: pd.DataFrame, y: pd.Series, ordered_df: pd.DataFrame
) -> dict:
    train_idx, test_idx, split_strategy = _build_evaluation_split(ordered_df, y)
    x_train, x_test = x.loc[train_idx], x.loc[test_idx]
    y_train, y_test = y.loc[train_idx], y.loc[test_idx]

    class_count = y_train.value_counts()
    min_class_count = int(class_count.min()) if not class_count.empty else 0
    n_splits = min(5, min_class_count)
    if n_splits >= 2 and y_train.nunique() > 1:
        cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
        cv_scores = cross_val_score(pipeline, x_train, y_train, cv=cv, scoring="roc_auc")
        cv_mean = float(np.mean(cv_scores))
        cv_std = float(np.std(cv_scores))
    else:
        cv_mean = float("nan")
        cv_std = float("nan")

    pipeline.fit(x_train, y_train)
    y_prob = pipeline.predict_proba(x_test)[:, 1]
    roc_auc = _safe_roc_auc(y_test, y_prob)
    if y_test.nunique() > 1:
        fpr, tpr, _ = roc_curve(y_test, y_prob)
        precision, recall, _ = precision_recall_curve(y_test, y_prob)
        fpr_list, tpr_list = fpr.tolist(), tpr.tolist()
        precision_list, recall_list = precision.tolist(), recall.tolist()
    else:
        fpr_list, tpr_list = [], []
        precision_list, recall_list = [], []

    return {
        "model": pipeline,
        "cv_roc_auc_mean": cv_mean,
        "cv_roc_auc_std": cv_std,
        "temporal_test_roc_auc": roc_auc,
        "split_strategy": split_strategy,
        "train_size": int(len(x_train)),
        "test_size": int(len(x_test)),
        "fpr": fpr_list,
        "tpr": tpr_list,
        "precision": precision_list,
        "recall": recall_list,
        "x_test_index": x_test.index.tolist(),
        "y_prob_test": y_prob.tolist(),
    }


def train_and_score_models(df: pd.DataFrame, output_dir: Path) -> tuple[dict, dict, pd.DataFrame]:
    output_dir.mkdir(parents=True, exist_ok=True)
    work_df = df.copy().dropna(subset=["signup_date"])
    preprocessor, numeric_features, categorical_features = _build_preprocessor(work_df)
    feature_cols = numeric_features + categorical_features
    eval_df = work_df[feature_cols + ["signup_date", "is_churned", "next_purchase_30d"]].copy()

    churn_df = eval_df.dropna(subset=["is_churned"]).copy()
    churn_df["is_churned"] = churn_df["is_churned"].astype(int)
    x_churn = churn_df[feature_cols]

    churn_pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "clf",
                RandomForestClassifier(
                    n_estimators=280, min_samples_leaf=5, random_state=42, class_weight="balanced"
                ),
            ),
        ]
    )
    churn_results = _evaluate_pipeline_temporal(
        churn_pipeline, x_churn, churn_df["is_churned"], churn_df
    )
    churn_model = churn_results["model"]
    work_df["churn_probability"] = churn_model.predict_proba(work_df[feature_cols])[:, 1]

    next_df = eval_df.dropna(subset=["next_purchase_30d"]).copy()
    next_df["next_purchase_30d"] = next_df["next_purchase_30d"].astype(int)
    x_next = next_df[feature_cols]

    next_purchase_pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("clf", LogisticRegression(max_iter=1200)),
        ]
    )
    next_purchase_results = _evaluate_pipeline_temporal(
        next_purchase_pipeline, x_next, next_df["next_purchase_30d"], next_df
    )
    next_purchase_model = next_purchase_results["model"]
    work_df["next_purchase_probability"] = next_purchase_model.predict_proba(work_df[feature_cols])[:, 1]

    joblib.dump(churn_model, output_dir / "churn_model.joblib")
    joblib.dump(next_purchase_model, output_dir / "next_purchase_model.joblib")
    work_df.to_csv(output_dir / "scored_customers.csv", index=False)
    report = {
        "churn": {
            "cv_roc_auc_mean": churn_results["cv_roc_auc_mean"],
            "cv_roc_auc_std": churn_results["cv_roc_auc_std"],
            "temporal_test_roc_auc": churn_results["temporal_test_roc_auc"],
            "split_strategy": churn_results["split_strategy"],
            "train_size": churn_results["train_size"],
            "test_size": churn_results["test_size"],
        },
        "next_purchase_30d": {
            "cv_roc_auc_mean": next_purchase_results["cv_roc_auc_mean"],
            "cv_roc_auc_std": next_purchase_results["cv_roc_auc_std"],
            "temporal_test_roc_auc": next_purchase_results["temporal_test_roc_auc"],
            "split_strategy": next_purchase_results["split_strategy"],
            "train_size": next_purchase_results["train_size"],
            "test_size": next_purchase_results["test_size"],
        },
    }
    with (output_dir / "metrics_report.json").open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return churn_results, next_purchase_results, work_df
