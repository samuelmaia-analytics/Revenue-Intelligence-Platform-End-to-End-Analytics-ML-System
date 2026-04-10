from __future__ import annotations

import json
import pickle
import re
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from sklearn.pipeline import Pipeline

from src.io_utils import atomic_write_json

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


def _find_existing_version_by_data_version(
    registry_root: Path, data_version: str
) -> tuple[int, str] | None:
    pattern = re.compile(r"^model_v(\d+)$")
    for child in registry_root.iterdir():
        if not child.is_dir():
            continue
        match = pattern.match(child.name)
        if not match:
            continue
        metadata_path = child / "model_metadata.json"
        if not metadata_path.exists():
            continue
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if metadata.get("data_version") == data_version:
            version_number = int(match.group(1))
            return version_number, child.name
    return None


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
    run_id: str | None = None,
) -> dict:
    registry_root = output_dir / "registry" / model_name
    registry_root.mkdir(parents=True, exist_ok=True)
    existing_version = _find_existing_version_by_data_version(registry_root, data_version)
    if existing_version is None:
        version_number, version_label = _next_model_version(registry_root)
        registry_dir = registry_root / version_label
        registry_dir.mkdir(parents=True, exist_ok=False)
    else:
        version_number, version_label = existing_version
        registry_dir = registry_root / version_label
        registry_dir.mkdir(parents=True, exist_ok=True)

    model_path = registry_dir / "model.pkl"
    metadata_path = registry_dir / "model_metadata.json"
    _persist_pickle(model, model_path)

    metadata = {
        "model_name": model_name,
        "run_id": run_id or str(uuid4()),
        "created_at_utc": datetime.now(UTC).isoformat(),
        "data_version": data_version,
        "model_version": version_label,
        "model_version_number": version_number,
        "metrics": metrics,
        "input_features": input_features,
        "target_name": target_name,
        "model_file": model_path.name,
    }
    atomic_write_json(metadata_path, metadata)

    latest_pointer = registry_root / "latest.json"
    atomic_write_json(
        latest_pointer,
        {
            "model_name": model_name,
            "latest_model_version": version_label,
            "latest_model_version_number": version_number,
            "updated_at_utc": metadata["created_at_utc"],
            "run_id": metadata["run_id"],
            "data_version": data_version,
        },
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


def load_registered_model_by_data_version(
    base_dir: Path, model_name: str, data_version: str
) -> tuple[Pipeline, dict]:
    registry_root, layout = _resolve_registry_layout(base_dir, model_name)
    if layout != "versioned" or not registry_root.exists():
        raise FileNotFoundError(
            f"Versioned model registry not found for '{model_name}' in {registry_root.resolve()}"
        )

    existing_version = _find_existing_version_by_data_version(registry_root, data_version)
    if existing_version is None:
        raise FileNotFoundError(
            f"No registered model found for '{model_name}' and data_version='{data_version}'."
        )

    _, version_label = existing_version
    registry_dir = registry_root / version_label
    model_path = registry_dir / "model.pkl"
    metadata_path = registry_dir / "model_metadata.json"
    model = _load_model(model_path)
    with metadata_path.open("r", encoding="utf-8") as metadata_file:
        metadata = json.load(metadata_file)
    return model, metadata
