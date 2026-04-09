import hashlib
import pickle
from pathlib import Path
from typing import cast

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_recall_curve, roc_auc_score, roc_curve
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.io_utils import atomic_write_csv, atomic_write_json
from src.model_registry import register_model

try:
    import joblib
except ModuleNotFoundError:  # pragma: no cover - fallback used only in minimal envs
    joblib = None


def _build_preprocessor() -> tuple[ColumnTransformer, list[str], list[str]]:
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


def _positive_class_probability(model: Pipeline, features: pd.DataFrame) -> np.ndarray:
    probabilities = model.predict_proba(features)
    classifier = model.named_steps["clf"]
    classes = getattr(classifier, "classes_", [])
    if len(classes) == 1:
        positive_class = int(classes[0])
        fill_value = 1.0 if positive_class == 1 else 0.0
        return np.full(shape=len(features), fill_value=fill_value, dtype=float)
    positive_index = list(classes).index(1)
    return probabilities[:, positive_index]


def _temporal_split_indices(
    df: pd.DataFrame, split_ratio: float = 0.8
) -> tuple[pd.Index, pd.Index]:
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

    if y.nunique() < 2:
        return train_idx, test_idx, "temporal_single_class"

    if int(y.value_counts().min()) < 2 or len(y) < 5:
        return train_idx, test_idx, "temporal_minority_class_fallback"

    train_idx, test_idx = train_test_split(y.index, test_size=0.2, random_state=42, stratify=y)
    return pd.Index(train_idx), pd.Index(test_idx), "stratified_fallback"


def _evaluate_pipeline_temporal(
    pipeline: Pipeline, x: pd.DataFrame, y: pd.Series, ordered_df: pd.DataFrame
) -> dict:
    train_idx, test_idx, split_strategy = _build_evaluation_split(ordered_df, y)
    x_train, x_test = x.loc[train_idx], x.loc[test_idx]
    y_train, y_test = y.loc[train_idx], y.loc[test_idx]

    if y_train.nunique() < 2 and y.nunique() >= 2:
        x_train = x
        y_train = y
        split_strategy = f"{split_strategy}_full_fit"

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
    y_prob = _positive_class_probability(pipeline, x_test)
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


def _persist_model(model: Pipeline, path: Path) -> None:
    if joblib is not None:
        joblib.dump(model, path)
        return
    with path.open("wb") as model_file:
        pickle.dump(model, model_file)


def _validate_binary_target(y: pd.Series, target_name: str) -> None:
    if y.nunique() < 2:
        raise ValueError(
            f"Target '{target_name}' has a single class after preprocessing; "
            "cannot train a classifier."
        )


def _compute_data_version(df: pd.DataFrame) -> str:
    normalized = df.copy()
    for col in normalized.columns:
        if pd.api.types.is_datetime64_any_dtype(normalized[col]):
            normalized[col] = normalized[col].astype(str)
    hashed = pd.util.hash_pandas_object(normalized, index=True).to_numpy().tobytes()
    return hashlib.md5(hashed).hexdigest()


def _extract_model_drivers(pipeline: Pipeline) -> list[dict[str, float | str]]:
    preprocessor = pipeline.named_steps["preprocessor"]
    feature_names = preprocessor.get_feature_names_out().tolist()
    classifier = pipeline.named_steps["clf"]

    if hasattr(classifier, "feature_importances_"):
        scores = classifier.feature_importances_
    elif hasattr(classifier, "coef_"):
        scores = np.abs(classifier.coef_[0])
    else:
        return []

    drivers = pd.DataFrame({"feature": feature_names, "importance": scores})
    drivers = drivers.sort_values("importance", ascending=False).head(8)
    return cast(list[dict[str, float | str]], drivers.to_dict(orient="records"))


def _build_business_model_summary(
    model_name: str,
    results: dict,
    pipeline: Pipeline,
) -> dict:
    top_drivers = _extract_model_drivers(pipeline)
    interpretation = {
        "churn": "Use churn risk to prioritize retention budget toward customers with high value and deteriorating recency.",
        "next_purchase_30d": "Use next-purchase propensity to target upsell and timing-sensitive CRM actions.",
    }
    return {
        "model_name": model_name,
        "split_strategy": results["split_strategy"],
        "cv_roc_auc_mean": results["cv_roc_auc_mean"],
        "cv_roc_auc_std": results["cv_roc_auc_std"],
        "temporal_test_roc_auc": results["temporal_test_roc_auc"],
        "train_size": results["train_size"],
        "test_size": results["test_size"],
        "top_business_drivers": top_drivers,
        "business_interpretation": interpretation[model_name],
    }


def _cap_training_frame(
    frame: pd.DataFrame,
    target_col: str,
    *,
    max_rows: int | None,
    seed: int,
) -> pd.DataFrame:
    if max_rows is None or len(frame) <= max_rows:
        return frame
    target = frame[target_col]
    if target.nunique() >= 2:
        sampled = (
            frame.groupby(target_col, group_keys=False)
            .apply(
                lambda group: group.sample(
                    n=max(1, int(round(max_rows * len(group) / len(frame)))),
                    random_state=seed,
                    replace=False,
                )
            )
            .reset_index(drop=True)
        )
        if len(sampled) > max_rows:
            sampled = sampled.sample(n=max_rows, random_state=seed).reset_index(drop=True)
        return sampled
    return frame.sample(n=max_rows, random_state=seed).reset_index(drop=True)


def train_and_score_models(
    df: pd.DataFrame,
    output_dir: Path,
    run_id: str | None = None,
    *,
    max_training_rows: int | None = None,
    seed: int = 42,
) -> tuple[dict, dict, pd.DataFrame]:
    output_dir.mkdir(parents=True, exist_ok=True)
    work_df = df.copy().dropna(subset=["signup_date"])
    preprocessor, numeric_features, categorical_features = _build_preprocessor()
    feature_cols = numeric_features + categorical_features
    eval_df = work_df[feature_cols + ["signup_date", "is_churned", "next_purchase_30d"]].copy()

    churn_df = eval_df.dropna(subset=["is_churned"]).copy()
    churn_df["is_churned"] = churn_df["is_churned"].astype(int)
    churn_df = _cap_training_frame(
        churn_df,
        "is_churned",
        max_rows=max_training_rows,
        seed=seed,
    )
    _validate_binary_target(churn_df["is_churned"], "is_churned")
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
    work_df["churn_probability"] = _positive_class_probability(churn_model, work_df[feature_cols])

    next_df = eval_df.dropna(subset=["next_purchase_30d"]).copy()
    next_df["next_purchase_30d"] = next_df["next_purchase_30d"].astype(int)
    next_df = _cap_training_frame(
        next_df,
        "next_purchase_30d",
        max_rows=max_training_rows,
        seed=seed,
    )
    _validate_binary_target(next_df["next_purchase_30d"], "next_purchase_30d")
    x_next = next_df[feature_cols]

    next_purchase_pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("clf", LogisticRegression(max_iter=1200, solver="liblinear")),
        ]
    )
    next_purchase_results = _evaluate_pipeline_temporal(
        next_purchase_pipeline, x_next, next_df["next_purchase_30d"], next_df
    )
    next_purchase_model = next_purchase_results["model"]
    work_df["next_purchase_probability"] = _positive_class_probability(
        next_purchase_model,
        work_df[feature_cols],
    )

    _persist_model(churn_model, output_dir / "churn_model.joblib")
    _persist_model(next_purchase_model, output_dir / "next_purchase_model.joblib")
    churn_data_version = _compute_data_version(churn_df[feature_cols + ["is_churned"]])
    next_data_version = _compute_data_version(next_df[feature_cols + ["next_purchase_30d"]])

    register_model(
        model_name="churn",
        model=churn_model,
        output_dir=output_dir,
        data_version=churn_data_version,
        metrics={
            "cv_roc_auc_mean": churn_results["cv_roc_auc_mean"],
            "cv_roc_auc_std": churn_results["cv_roc_auc_std"],
            "temporal_test_roc_auc": churn_results["temporal_test_roc_auc"],
            "split_strategy": churn_results["split_strategy"],
            "train_size": churn_results["train_size"],
            "test_size": churn_results["test_size"],
        },
        input_features=feature_cols,
        target_name="is_churned",
        run_id=run_id,
    )
    register_model(
        model_name="next_purchase_30d",
        model=next_purchase_model,
        output_dir=output_dir,
        data_version=next_data_version,
        metrics={
            "cv_roc_auc_mean": next_purchase_results["cv_roc_auc_mean"],
            "cv_roc_auc_std": next_purchase_results["cv_roc_auc_std"],
            "temporal_test_roc_auc": next_purchase_results["temporal_test_roc_auc"],
            "split_strategy": next_purchase_results["split_strategy"],
            "train_size": next_purchase_results["train_size"],
            "test_size": next_purchase_results["test_size"],
        },
        input_features=feature_cols,
        target_name="next_purchase_30d",
        run_id=run_id,
    )

    atomic_write_csv(output_dir / "scored_customers.csv", work_df)
    churn_summary = _build_business_model_summary("churn", churn_results, churn_model)
    next_purchase_summary = _build_business_model_summary(
        "next_purchase_30d", next_purchase_results, next_purchase_model
    )
    report = {
        "churn": churn_summary,
        "next_purchase_30d": next_purchase_summary,
    }
    atomic_write_json(output_dir / "metrics_report.json", report)

    return churn_summary, next_purchase_summary, work_df
