#!/usr/bin/env python3
from pathlib import Path
from shutil import copyfile


FILES = {
    "profile/learner-profile.example.md": "profile/learner-profile.md",
    "progress/progress.example.md": "progress/progress.md",
    "topics/topic-history.example.md": "topics/topic-history.md",
    "vocabulary/vocabulary.example.md": "vocabulary/vocabulary.md",
}


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    created = []
    for example, destination in FILES.items():
        target = root / destination
        if target.exists():
            continue
        copyfile(root / example, target)
        created.append(destination)

    if created:
        print("Created personal learning files:")
        for path in created:
            print(f"- {path}")
    else:
        print("Personal learning files already exist; nothing changed.")


if __name__ == "__main__":
    main()
