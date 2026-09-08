# 1일 1오픽

매일 오픽형 질문에 답하고, 교정과 표현을 쌓아가는 개인 영어 말하기 연습 공간입니다.

## 시작하기

저장소를 처음 받은 뒤 개인 학습 파일을 만듭니다. 예시 원본은 유지되며, 이미 존재하는 학습 파일은 덮어쓰지 않습니다.

```bash
python3 scripts/setup_learning_data.py
```

그다음 대화에서 **“오늘의 주제 줘”**라고 말하면 됩니다. 질문을 받은 뒤 영어로 말한 STT 결과나 직접 쓴 스크립트를 보내면 평가, 교정, 개선본, 다음 미션이 기록됩니다.

처음에는 `profile/learner-profile.md`에 목표 등급과 자주 선택할 Background Survey 항목을 적어두면 질문이 더 잘 맞습니다. 비워둔 채 바로 시작해도 됩니다.

## 폴더 구성

- `sessions/`: 날짜별 질문, 원문 답변, 피드백과 개선본
- `vocabulary/`: 답변 중 한국어로 막힌 표현과 복습할 영어
- `topics/`: 이미 연습한 주제와 질문 유형
- `progress/`: 반복 실수, 강점, 다음 집중 목표
- `profile/`: 목표 등급, 선호 주제, 실제 경험 등 개인화 정보
- `templates/`: 새 학습 기록에 사용할 세션 형식
- `dashboard/`: Markdown 기록을 시각화하는 로컬 대시보드

각 학습 폴더의 `*.example.md`는 공개 예시입니다. 실제 프로필, 진행 상황, 주제, 단어장과 세션 기록은 Git에 포함되지 않습니다.

## 학습 대시보드

Python 3만 있으면 현재까지의 기록으로 대시보드를 만들 수 있습니다.

```bash
python3 scripts/build_dashboard.py
open dashboard/generated/index.html
```

새 세션을 저장한 뒤 첫 번째 명령을 다시 실행하면 점수 추이, 반복 실수, 미션과 단어장이 갱신됩니다. 생성된 HTML에는 개인 학습 내용이 포함되므로 `dashboard/generated/`는 Git에 저장하지 않습니다.
