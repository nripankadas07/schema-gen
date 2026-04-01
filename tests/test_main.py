"""Tests for schema-gen."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest

from schema_gen.generator import (
    generate_model,
    generate_models_from_file,
    infer_schema,
)


# ---------- infer_schema tests ----------


def test_infer_schema_basic_types():
    samples = [{"name": "Alice", "age": 30, "active": True, "score": 9.5}]
    schema = infer_schema(samples)
    assert schema["name"] == ["str"]
    assert schema["age"] == ["int"]
    assert schema["active"] == ["bool"]
    assert schema["score"] == ["float"]


def test_infer_schema_null_value():
    schema = infer_schema([{"x": None}])
    assert schema["x"] == ["Any | None"]


def test_infer_schema_list_field():
    schema = infer_schema([{"tags": ["a", "b"]}])
    assert schema["tags"] == ["list[str]"]


def test_infer_schema_empty_list():
    schema = infer_schema([{"items": []}])
    assert schema["items"] == ["list[Any]"]


def test_infer_schema_multiple_samples_merge():
    schema = infer_schema([{"val": 1}, {"val": 2}])
    assert schema["val"] == ["int", "int"]


# ---------- generate_model tests ----------


def test_generate_model_simple():
    code = generate_model([{"name": "Alice", "age": 30}], class_name="User")
    assert "class User(BaseModel):" in code
    assert "name: str" in code
    assert "age: int" in code
    assert "from pydantic import BaseModel" in code


def test_generate_model_nested_object():
    sample = {"user": {"name": "Bob", "email": "bob@test.com"}}
    code = generate_model([sample], class_name="Root")
    assert "class User(BaseModel):" in code
    assert "class Root(BaseModel):" in code
    assert "user: User" in code


def test_generate_model_list_of_objects():
    sample = {"items": [{"id": 1, "label": "x"}]}
    code = generate_model([sample], class_name="Response")
    assert "class Items(BaseModel):" in code
    assert "items: list[Items]" in code


def test_generate_model_no_samples_raises():
    with pytest.raises(ValueError, match="At least one sample"):
        generate_model([])


def test_generate_model_mixed_types():
    """Multiple samples with different types for the same field."""
    code = generate_model(
        [{"val": 1}, {"val": "text"}],
        class_name="Mixed",
    )
    assert "class Mixed(BaseModel):" in code
    assert "val: int | str" in code


# ---------- generate_models_from_file tests ----------


def test_generate_from_file_single_object(tmp_path: Path):
    p = tmp_path / "single.json"
    p.write_text(json.dumps({"id": 1, "name": "test"}))
    code = generate_models_from_file(p, class_name="Item")
    assert "class Item(BaseModel):" in code
    assert "id: int" in code


def test_generate_from_file_array(tmp_path: Path):
    data = [{"a": 1}, {"a": 2, "b": "x"}]
    p = tmp_path / "arr.json"
    p.write_text(json.dumps(data))
    code = generate_models_from_file(p, class_name="Row")
    assert "class Row(BaseModel):" in code


def test_generate_from_file_invalid_json(tmp_path: Path):
    p = tmp_path / "bad.json"
    p.write_text('"just a string"')
    with pytest.raises(ValueError, match="object or array"):
        generate_models_from_file(p)


# ---------- edge cases ----------


def test_sanitize_special_keys():
    code = generate_model([{"first-name": "A", "2nd": "B", "class": "C"}])
    assert "first_name: str" in code
    assert "field_2nd: str" in code
    assert "class_: str" in code


def test_deeply_nested():
    sample = {"a": {"b": {"c": {"d": 42}}}}
    code = generate_model([sample], class_name="Deep")
    assert "class Deep(BaseModel):" in code
    assert "class A(BaseModel):" in code
