"""schema-gen: Generate Pydantic models from JSON samples."""

__version__ = "0.1.0"

from schema_gen.generator import generate_model as generate_model
from schema_gen.generator import generate_models_from_file as generate_models_from_file
from schema_gen.generator import infer_schema as infer_schema
