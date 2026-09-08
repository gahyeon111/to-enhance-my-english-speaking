from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Session:
    path: str
    date: str
    topic: str
    status: str = "unknown"
    input_type: str = "unknown"
    estimated_level: str = ""
    scores: dict[str, int] = field(default_factory=dict)
    mistakes: list[dict[str, Any]] = field(default_factory=list)
    mission: dict[str, str] = field(default_factory=dict)
    questions: list[str] = field(default_factory=list)
    original: str = ""
    corrections: list[dict[str, str]] = field(default_factory=list)
    improved_answers: list[dict[str, str]] = field(default_factory=list)
    key_evaluation: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
