from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def render_dashboard(root: Path, data: dict[str, Any]) -> Path:
    source = root / "dashboard" / "src"
    template = (source / "index.template.html").read_text(encoding="utf-8")
    style = (source / "dashboard.css").read_text(encoding="utf-8")
    script = (source / "dashboard.js").read_text(encoding="utf-8")
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    output = (
        template.replace("{{STYLE}}", style)
        .replace("{{DATA}}", payload)
        .replace("{{SCRIPT}}", script)
        .replace("{{BUILT_AT}}", datetime.now().astimezone().strftime("%Y-%m-%d %H:%M"))
    )
    destination = root / "dashboard" / "generated" / "index.html"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(output, encoding="utf-8")
    return destination
