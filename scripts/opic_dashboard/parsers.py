from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .models import Session


def _scalar(value: str) -> Any:
    value = value.strip().strip('"').strip("'")
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    if value.lower() in {"null", "none", "~"}:
        return None
    return value


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Parse the deliberately small YAML subset used by session files."""
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text

    lines = text[4:end].splitlines()
    data: dict[str, Any] = {}
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line or line.startswith(" ") or ":" not in line:
            index += 1
            continue
        key, raw_value = line.split(":", 1)
        key = key.strip()
        if raw_value.strip():
            data[key] = _scalar(raw_value)
            index += 1
            continue

        index += 1
        nested: list[str] = []
        while index < len(lines):
            candidate = lines[index]
            if candidate and not candidate.startswith(" ") and not candidate.startswith("-"):
                break
            nested.append(candidate)
            index += 1

        if any(item.lstrip().startswith("-") for item in nested):
            items: list[dict[str, Any]] = []
            current: dict[str, Any] | None = None
            for item in nested:
                stripped = item.strip()
                if not stripped:
                    continue
                if stripped.startswith("-"):
                    current = {}
                    items.append(current)
                    stripped = stripped[1:].strip()
                if current is not None and ":" in stripped:
                    nested_key, nested_value = stripped.split(":", 1)
                    current[nested_key.strip()] = _scalar(nested_value)
            data[key] = items
        else:
            mapping: dict[str, Any] = {}
            for item in nested:
                stripped = item.strip()
                if ":" in stripped:
                    nested_key, nested_value = stripped.split(":", 1)
                    mapping[nested_key.strip()] = _scalar(nested_value)
            data[key] = mapping

    return data, text[end + 5 :]


def _sections(body: str, level: int = 2) -> dict[str, str]:
    marker = "#" * level
    matches = list(re.finditer(rf"^{marker} (.+?)\s*$", body, re.MULTILINE))
    result: dict[str, str] = {}
    for position, match in enumerate(matches):
        start = match.end()
        end = matches[position + 1].start() if position + 1 < len(matches) else len(body)
        result[match.group(1).strip()] = body[start:end].strip()
    return result


def _bullets(text: str) -> list[str]:
    return [match.group(1).strip() for match in re.finditer(r"^-\s+(.+)$", text, re.MULTILINE)]


def _markdown_table(text: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in text.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            continue
        rows.append(cells)
    return rows


def parse_session(path: Path, root: Path) -> Session:
    metadata, body = parse_frontmatter(path.read_text(encoding="utf-8"))
    sections = _sections(body)
    questions = [
        match.group(1).strip()
        for match in re.finditer(r"^\d+\.\s+(.+)$", sections.get("질문", ""), re.MULTILINE)
    ]
    original_lines = []
    for line in sections.get("사용자 원문(STT)", "").splitlines():
        if line.startswith(">"):
            original_lines.append(line[1:].lstrip())
        elif original_lines:
            original_lines.append(line)

    correction_rows = _markdown_table(sections.get("주요 교정", ""))
    corrections = []
    for row in correction_rows[1:]:
        if len(row) >= 3:
            corrections.append({"original": row[0], "recommendation": row[1], "reason": row[2]})

    improved = []
    improved_text = sections.get("개선된 답변", "")
    for label, answer in _sections(improved_text, 3).items():
        improved.append({"label": label, "answer": answer.strip()})

    title_match = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
    inferred_topic = title_match.group(1).split("—", 1)[-1].strip() if title_match else path.stem
    session = Session(
        path=str(path.relative_to(root)),
        date=str(metadata.get("date", path.name[:10])),
        topic=str(metadata.get("topic", inferred_topic)),
        status=str(metadata.get("status", "unknown")),
        input_type=str(metadata.get("input_type", "unknown")),
        estimated_level=str(metadata.get("estimated_level", "")),
        scores=metadata.get("scores", {}) if isinstance(metadata.get("scores"), dict) else {},
        mistakes=metadata.get("mistakes", []) if isinstance(metadata.get("mistakes"), list) else [],
        mission=metadata.get("mission", {}) if isinstance(metadata.get("mission"), dict) else {},
        questions=questions,
        original="\n\n".join(part.strip() for part in "\n".join(original_lines).split("\n\n") if part.strip()),
        corrections=corrections,
        improved_answers=improved,
        key_evaluation=_bullets(sections.get("핵심 평가", "")),
    )
    return session


def parse_topic_history(path: Path) -> list[dict[str, str]]:
    rows = _markdown_table(path.read_text(encoding="utf-8"))
    return [
        {"date": row[0], "topic": row[1], "question_type": row[2], "mission": row[3], "status": row[4]}
        for row in rows[1:]
        if len(row) >= 5
    ]


def parse_vocabulary(path: Path) -> list[dict[str, Any]]:
    rows = _markdown_table(path.read_text(encoding="utf-8"))
    result = []
    for row in rows[1:]:
        if len(row) >= 6:
            result.append(
                {
                    "korean": row[0],
                    "english": row[1].replace("`", ""),
                    "example": row[2],
                    "topic": row[3],
                    "date": row[4],
                    "count": int(row[5]) if row[5].isdigit() else 0,
                }
            )
    return result


def parse_section_bullets(path: Path) -> dict[str, list[str]]:
    sections = _sections(path.read_text(encoding="utf-8"))
    return {title: _bullets(content) for title, content in sections.items()}


def load_repository(root: Path) -> dict[str, Any]:
    session_paths = [path for path in sorted((root / "sessions").glob("*.md")) if not path.name.endswith(".example.md")]
    sessions = [parse_session(path, root).to_dict() for path in session_paths]
    return {
        "sessions": sessions,
        "topics": parse_topic_history(root / "topics" / "topic-history.md"),
        "vocabulary": parse_vocabulary(root / "vocabulary" / "vocabulary.md"),
        "progress": parse_section_bullets(root / "progress" / "progress.md"),
        "profile": parse_section_bullets(root / "profile" / "learner-profile.md"),
    }


def validate_repository(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    score_keys = {"content", "grammar", "vocabulary", "flow", "delivery"}
    mission_results = {"success", "partial", "retry", "unknown"}
    for session in data.get("sessions", []):
        source = session.get("path", "unknown session")
        for required in ("date", "topic", "status"):
            if not session.get(required):
                errors.append(f"{source}: missing '{required}'")
        for key, value in session.get("scores", {}).items():
            if key not in score_keys:
                errors.append(f"{source}: unknown score '{key}'")
            if not isinstance(value, int) or not 1 <= value <= 5:
                errors.append(f"{source}: score '{key}' must be an integer from 1 to 5")
        for mistake in session.get("mistakes", []):
            if not mistake.get("id") or not mistake.get("label"):
                errors.append(f"{source}: every mistake needs an id and label")
            if not isinstance(mistake.get("count"), int) or mistake.get("count", 0) < 1:
                errors.append(f"{source}: mistake count must be a positive integer")
        result = session.get("mission", {}).get("result", "unknown")
        if result not in mission_results:
            errors.append(f"{source}: mission result must be success, partial, retry, or unknown")
    return errors
