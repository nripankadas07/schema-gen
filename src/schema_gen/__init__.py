"""schema-gen: Generate Pydantic models from JSON samples."""

__version__ = "0.1.0"

from schema_gen.generator import generate_model, generate_models_from_file, infer_schema
