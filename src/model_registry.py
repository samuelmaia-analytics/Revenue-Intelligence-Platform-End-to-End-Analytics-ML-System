from __future__ import annotations

import json
import pickle
import re
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from sklearn.pipeline import Pipeline

try:
    import joblib
except ModuleNotFoundError:  # pragma: no cover
    joblib = None


def _persist_pickle(model: Pipeline, path: Path) -> None:
    with path.open("wb") as model_file:
        pickle.dump(model, model_file)


def _resolve_registry_layout(base_dir: Path, model_name: str) -> tuple[Path, str]:
    registry_root = base_dir / "registry" / model_name
    if registry_root.exists():
        return registry_root, "versioned"

    legacy_root = base_dir / "model_registry" / model_name
    if legacy_root.exists():
        return legacy_root, "legacy"

    return registry_root, "versioned"


def _next_model_version(registry_root: Path) -> tuple[int, str]:
    pattern = re.compile(r"^model_v(\d+)$")
    versions: list[int] = []
    for child in registry_root.iterdir():
        if not child.is_dir():
            continue
        match = pattern.match(child.name)
        if match:
            versions.append(int(match.group(1)))

    if not versions:
        return 1, "model_v1"
    next_version = max(versions) + 1
    return next_version, f"model_v{next_version}"


def _latest_model_dir(registry_root: Path) -> Path:
    pattern = re.compile(r"^model_v(\d+)$")
    versioned_dirs: list[tuple[int, Path]] = []
    for child in registry_root.iterdir():
        if not child.is_dir():
            continue
        match = pattern.match(child.name)
        if match:
            versioned_dirs.append((int(match.group(1)), child))

    if not versioned_dirs:
        raise FileNotFoundError(f"No model_v* directories found in {registry_root.resolve()}")
    versioned_dirs.sort(key=lambda item: item[0], reverse=True)
    return versioned_dirs[0][1]


def _load_model(path: Path) -> Pipeline:
    if path.suffix == ".joblib" and joblib is not None:
        return joblib.load(path)
    with path.open("rb") as model_file:
        return pickle.load(model_file)


def register_model(
    model_name: str,
    model: Pipeline,
    output_dir: Path,
    data_version: str,
    metrics: dict[str, float | int | str | None],
    input_features: list[str],
    target_name: str,
) -> dict:
    registry_root = output_dir / "registry" / model_name
    registry_root.mkdir(parents=True, exist_ok=True)
    version_number, version_label = _next_model_version(registry_root)
    registry_dir = registry_root / version_label
    registry_dir.mkdir(parents=True, exist_ok=False)

    model_path = registry_dir / "model.pkl"
    metadata_path = registry_dir / "model_metadata.json"
    _persist_pickle(model, model_path)

    metadata = {
        "model_name": model_name,
        "run_id": str(uuid4()),
        "created_at_utc": datetime.now(UTC).isoformat(),
        "data_version": data_version,
        "model_version": version_label,
        "model_version_number": version_number,
        "metrics": metrics,
        "input_features": input_features,
        "target_name": target_name,
        "model_file": model_path.name,
    }
    with metadata_path.open("w", encoding="utf-8") as metadata_file:
        json.dump(metadata, metadata_file, indent=2, ensure_ascii=False)

    latest_pointer = registry_root / "latest.json"
    with latest_pointer.open("w", encoding="utf-8") as latest_file:
        json.dump(
            {
                "model_name": model_name,
                "latest_model_version": version_label,
                "latest_model_version_number": version_number,
                "updated_at_utc": metadata["created_at_utc"],
            },
            latest_file,
            indent=2,
            ensure_ascii=False,
        )
    return metadata


def load_registered_model(base_dir: Path, model_name: str) -> tuple[Pipeline, dict]:
    registry_root, layout = _resolve_registry_layout(base_dir, model_name)
    if not registry_root.exists():
        raise FileNotFoundError(
            f"Model registry not found for '{model_name}' in {registry_root.resolve()}"
        )

    if layout == "legacy":
        model_path = registry_root / "model.pkl"
        metadata_path = registry_root / "model_metadata.json"
    else:
        registry_dir = _latest_model_dir(registry_root)
        model_path = registry_dir / "model.pkl"
        metadata_path = registry_dir / "model_metadata.json"

    if not model_path.exists() or not metadata_path.exists():
        raise FileNotFoundError(
            f"Model registry not found for '{model_name}' in {registry_root.resolve()}"
        )

    model = _load_model(model_path)
    with metadata_path.open("r", encoding="utf-8") as metadata_file:
        metadata = json.load(metadata_file)
    return model, metadata
