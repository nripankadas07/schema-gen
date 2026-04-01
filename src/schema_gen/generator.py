"""Core logic for inferring Pydantic models from JSON data."""

from __future__ import annotations

import json
import keyword
import re
from pathlib import Path
from typing import Any


def _sanitize_name(name: str) -> str:
    """Convert a JSON key into a valid Python identifier."""
    clean = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    if clean and clean[0].isdigit():
        clean = f"field_{clean}"
    if keyword.iskeyword(clean):
        clean = f"{clean}_"
    return clean


def _to_class_name(key: str) -> str:
    """Convert a JSON key into a PascalCase class name."""
    parts = re.split(r"[_\-\s]+", key)
    return "".join(p.capitalize() for p in parts if p) or "Model"


def _infer_type(value: Any, key: str, nested: dict[str, str]) -> str:
    """Infer the Python/Pydantic type string for a JSON value.

    For nested objects, creates a new model name and records it in *nested*.
    """
    if value is None:
        return "Any | None"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "str"
    if isinstance(value, list):
        if len(value) == 0:
            return "list[Any]"
        elem_type = _infer_type(value[0], key, nested)
        return f"list[{elem_type}]"
    if isinstance(value, dict):
        cls = _to_class_name(key)
        nested[cls] = key
        return cls
    return "Any"


def _merge_types(types: list[str]) -> str:
    """Merge multiple inferred types into a union when they differ."""
    unique = list(dict.fromkeys(types))
    if len(unique) == 1:
        return unique[0]
    return " | ".join(unique)


def infer_schema(samples: list[dict[str, Any]]) -> dict[str, list[str]]:
    """Analyse *samples* and return ``{field_name: [observed_types]}``."""
    schema: dict[str, list[str]] = {}
    for sample in samples:
        nested: dict[str, str] = {}
        for key, value in sample.items():
            safe = _sanitize_name(key)
            t = _infer_type(value, key, nested)
            schema.setdefault(safe, []).append(t)
    return schema


def _generate_nested_models(
    samples: list[dict[str, Any]],
    parent_class: str,
) -> list[str]:
    """Recursively generate model code for nested objects."""
    blocks: list[str] = []
    nested_map: dict[str, str] = {}

    for sample in samples:
        for key, value in sample.items():
            if isinstance(value, dict):
                cls = _to_class_name(key)
                nested_map[cls] = key
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                cls = _to_class_name(key)
                nested_map[cls] = key

    for cls, orig_key in nested_map.items():
        child_samples: list[dict[str, Any]] = []
        for sample in samples:
            v = sample.get(orig_key)
            if isinstance(v, dict):
                child_samples.append(v)
            elif isinstance(v, list):
                child_samples.extend(item for item in v if isinstance(item, dict))

        if child_samples:
            blocks.extend(_generate_nested_models(child_samples, cls))
            schema = infer_schema(child_samples)
            lines = [f"class {cls}(BaseModel):"]
            if not schema:
                lines.append("    pass")
            for field, types in schema.items():
                merged = _merge_types(types)
                lines.append(f"    {field}: {merged}")
            blocks.append("\n".join(lines))

    return blocks


def generate_model(
    samples: list[dict[str, Any]],
    class_name: str = "GeneratedModel",
) -> str:
    """Generate Pydantic model source code from one or more JSON samples.

    Parameters
    ----------
    samples:
        A list of JSON objects (dicts) that represent instances of the model.
    class_name:
        The name to use for the top-level generated class.

    Returns
    -------
    str
        Python source code defining the Pydantic model(s).
    """
    if not samples:
        raise ValueError("At least one sample is required")

    blocks: list[str] = [
        "from __future__ import annotations",
        "",
        "from typing import Any",
        "",
        "from pydantic import BaseModel",
        "",
    ]

    nested_blocks = _generate_nested_models(samples, class_name)
    blocks.extend(nested_blocks)
    if nested_blocks:
        blocks.append("")

    schema = infer_schema(samples)
    model_lines = [f"class {class_name}(BaseModel):"]
    if not schema:
        model_lines.append("    pass")
    else:
        for field, types in schema.items():
            merged = _merge_types(types)
            model_lines.append(f"    {field}: {merged}")
    blocks.append("\n".join(model_lines))
    blocks.append("")

    return "\n".join(blocks)


def generate_models_from_file(
    path: str | Path,
    class_name: str = "GeneratedModel",
) -> str:
    """Read a JSON file and generate Pydantic models.

    The file may contain a single object or an array of objects.
    """
    raw = Path(path).read_text(encoding="utf-8")
    data = json.loads(raw)
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list) or not all(isinstance(d, dict) for d in data):
        raise ValueError("JSON must be an object or array of objects")
    return generate_model(data, class_name)
