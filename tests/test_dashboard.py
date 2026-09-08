import tempfile
import unittest
from datetime import date
from pathlib import Path

from scripts.opic_dashboard.metrics import add_metrics
from scripts.opic_dashboard.parsers import parse_frontmatter, parse_session, validate_repository


SAMPLE = """---
date: 2026-09-08
topic: 테스트 주제
status: completed
input_type: stt
estimated_level: IM2
scores:
  content: 4
  grammar: 3
  vocabulary: 4
  flow: 3
  delivery: 3
mistakes:
- id: tense-consistency
  label: 과거시제 유지
  count: 2
mission:
  text: 과거형 유지하기
  result: partial
---

# 2026-09-08 — 테스트 주제

## 질문

1. Tell me about your routine.

## 사용자 원문(STT)

> I go there yesterday.

## 핵심 평가

- 구체적인 장소를 설명했다.

## 주요 교정

| 원문 | 추천 표현 | 이유 |
|---|---|---|
| I go there yesterday. | I went there yesterday. | 과거시제 |

## 개선된 답변

### Q1

I went there yesterday.
"""


class DashboardParserTest(unittest.TestCase):
    def test_frontmatter_nested_values(self):
        metadata, _ = parse_frontmatter(SAMPLE)
        self.assertEqual(metadata["scores"]["content"], 4)
        self.assertEqual(metadata["mistakes"][0]["count"], 2)
        self.assertEqual(metadata["mission"]["result"], "partial")

    def test_session_body(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            session_dir = root / "sessions"
            session_dir.mkdir()
            path = session_dir / "2026-09-08-test.md"
            path.write_text(SAMPLE, encoding="utf-8")
            session = parse_session(path, root)
        self.assertEqual(session.topic, "테스트 주제")
        self.assertEqual(len(session.questions), 1)
        self.assertEqual(len(session.corrections), 1)
        self.assertEqual(session.improved_answers[0]["label"], "Q1")

    def test_metrics(self):
        session = {
            "date": "2026-09-08",
            "status": "completed",
            "scores": {"content": 4},
            "mistakes": [{"id": "tense", "label": "과거시제", "count": 2}],
            "mission": {"result": "partial"},
        }
        result = add_metrics({"sessions": [session]}, today=date(2026, 9, 8))
        self.assertEqual(result["metrics"]["streak"], 1)
        self.assertEqual(result["metrics"]["score_averages"]["content"], 4.0)
        self.assertEqual(result["metrics"]["mistakes"][0]["count"], 2)

    def test_validation_rejects_out_of_range_score(self):
        data = {"sessions": [{"path": "bad.md", "date": "2026-09-08", "topic": "test", "status": "completed", "scores": {"content": 6}, "mission": {"result": "partial"}}]}
        self.assertIn("must be an integer from 1 to 5", validate_repository(data)[0])


if __name__ == "__main__":
    unittest.main()
