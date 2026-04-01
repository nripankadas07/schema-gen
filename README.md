# schema-gen

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)]()

Generate Pydantic v2 models from JSON samples â automatically infer types, handle nested objects, and produce clean, importable Python code.

## Why

Hand-writing Pydantic models from large JSON payloads is tedious and error-prone. `schema-gen` analyses one or more JSON samples and emits fully-typed Pydantic `BaseModel` classes, including nested models for sub-objects and proper list typing.

## Installation

```bash
pip install .
```

Or for development:

```bash
pip install -e ".[dev]"
```

## Usage

### CLI

```bash
# From a file
schema-gen data/sample.json -n UserProfile

# From stdin
cat payload.json | schema-gen -n ApiResponse

# Write to file
schema-gen input.json -n Order -o models.py
```

### Python API

```python
from schema_gen import generate_model, generate_models_from_file

# From dicts
samples = [
    {"name": "Alice", "age": 30, "address": {"city": "NYC", "zip": "10001"}},
    {"name": "Bob", "age": 25, "address": {"city": "LA", "zip": "90001"}},
]
code = generate_model(samples, class_name="User")
print(code)

# From a JSON file
code = generate_models_from_file("data.json", class_name="Record")
```

### Example Output

Given this JSON:

```json
{"name": "Alice", "age": 30, "address": {"city": "NYC", "zip": "10001"}}
```

`schema-gen` produces:

```python
from __future__ import annotations

from typing import Any

from pydantic import BaseModel

class Address(BaseModel):
    city: str
    zip: str

class User(BaseModel):
    name: str
    age: int
    address: Address
```

## API Reference

| Function | Description |
|----------|-------------|
| `generate_model(samples, class_name)` | Generate Pydantic model code from a list of dicts |
| `generate_models_from_file(path, class_name)` | Read a JSON file and generate models |
| `infer_schema(samples)` | Return raw schema dict mapping field names to observed types |

## Architecture

```
src/schema_gen/
âââ __init__.py       # Public API re-exports
âââ generator.py      # Core inference and code generation engine
âââ cli.py            # CLI entry-point (argparse)
```

The generator walks each sample recursively: primitive values map directly to Python types, nested dicts become child `BaseModel` classes, and arrays infer element types from the first item. When multiple samples disagree on a field's type, the generator produces a union (e.g. `int | str`).

## License

MIT â Nripanka Das
