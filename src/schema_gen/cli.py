"""CLI entry-point for schema-gen."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from schema_gen.generator import generate_model, generate_models_from_file


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="schema-gen",
        description="Generate Pydantic models from JSON samples.",
    )
    parser.add_argument(
        "input",
        nargs="?",
        help="Path to a JSON file. Reads stdin if omitted.",
    )
    parser.add_argument(
        "-n",
        "--name",
        default="GeneratedModel",
        help="Name for the generated top-level class (default: GeneratedModel).",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Write output to a file instead of stdout.",
    )

    args = parser.parse_args(argv)

    if args.input:
        code = generate_models_from_file(args.input, class_name=args.name)
    else:
        raw = sys.stdin.read()
        data = json.loads(raw)
        if isinstance(data, dict):
            data = [data]
        code = generate_model(data, class_name=args.name)

    if args.output:
        Path(args.output).write_text(code, encoding="utf-8")
    else:
        print(code)


if __name__ == "__main__":
    main()
