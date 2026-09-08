#!/usr/bin/env python3
from pathlib import Path

from opic_dashboard.metrics import add_metrics
from opic_dashboard.parsers import load_repository, validate_repository
from opic_dashboard.renderer import render_dashboard


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    data = load_repository(root)
    errors = validate_repository(data)
    if errors:
        formatted = "\n".join(f"- {error}" for error in errors)
        raise SystemExit(f"Dashboard metadata validation failed:\n{formatted}")
    data = add_metrics(data)
    destination = render_dashboard(root, data)
    print(f"Dashboard built: {destination}")


if __name__ == "__main__":
    main()
