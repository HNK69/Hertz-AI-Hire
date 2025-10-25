"""
question_gen.py
Load aptitude questions from a CSV dataset and fetch per skill.
"""

import random
import pandas as pd
from pathlib import Path
from assess.models import Question

CSV_PATH = Path(__file__).resolve().parent / "aptitude_full.csv"


def import_questions_from_csv(csv_path=CSV_PATH):
    """Imports questions from the combined CSV file into the Question table."""
    if not Path(csv_path).exists():
        print(f"CSV not found at {csv_path}")
        return

    df = pd.read_csv(csv_path)

    for _, row in df.iterrows():
        try:
            Question.objects.get_or_create(
                text=row["question_text"],
                defaults={
                    "options": [
                        row["option_1"],
                        row["option_2"],
                        row["option_3"],
                        row["option_4"],
                    ],
                    "correct_index": int(row["correct_index"]),
                    "difficulty": row.get("difficulty", "medium"),
                    "tags": [t.strip() for t in str(row.get("tags", "")).split(",") if t.strip()],
                },
            )
        except Exception as e:
            print("Error importing row:", e)
    print("✅ Question import completed successfully.")


import random
from assess.models import Question

PLACEHOLDER_TEST = ("this is a", "option 1")  # heuristics

def _is_placeholder(q: Question):
    txt = (q.text or "").lower()
    opts = [str(o).strip().lower() for o in (q.options or [])]
    if any(p in txt for p in PLACEHOLDER_TEST):
        return True
    if any("option 1" == o for o in opts):
        return True
    return False


def get_questions_for_skills(skills, n=15):
    """
    Always return up to n random questions.
    Prioritize skill-matched, fall back to general, never return empty.
    """
    from assess.models import Question
    qs = list(Question.objects.all())

    if not qs:
        import_questions_from_csv()
        qs = list(Question.objects.all())

    # remove placeholder-like questions
    qs = [q for q in qs if not _is_placeholder(q)]

    # --- Build match pools ---
    matched = []
    if skills:
        matched = [
            q for q in qs
            if any(s.lower() in [t.lower() for t in q.tags] for s in skills)
        ]

    general = [q for q in qs if any(
        t.lower() in ("math", "logic", "reasoning") for t in q.tags
    )]

    # --- Selection priority ---
    selected = []

    if matched:
        selected.extend(random.sample(matched, min(10, len(matched))))
    if len(selected) < n and general:
        needed = n - len(selected)
        selected.extend(random.sample(general, min(needed, len(general))))
    if len(selected) < n:
        needed = n - len(selected)
        leftovers = [q for q in qs if q not in selected]
        selected.extend(random.sample(leftovers, min(needed, len(leftovers))))

    # absolute fallback
    if not selected and qs:
        selected = random.sample(qs, min(n, len(qs)))

    random.shuffle(selected)
    print(f"🧠 Selected {len(selected)} questions out of {len(qs)} total")
    return selected[:n]
