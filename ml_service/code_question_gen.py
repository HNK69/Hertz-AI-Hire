import joblib
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from pathlib import Path
from assess.models import CodingQuestion

MODEL_PATH = Path(__file__).resolve().parent / "question_selector.pkl"
DATA_PATH = Path(__file__).resolve().parent / "interview_questions_500.csv"


def _normalize_tags(s):
    return [t.strip().lower() for t in str(s).split(",") if t.strip()]


def get_three_coding_questions(skills, top_k_search=20):
    """
    ML-driven adaptive selector with de-duplication and diversity.
    """
    if not Path(MODEL_PATH).exists() or not Path(DATA_PATH).exists():
        qs = list(CodingQuestion.objects.all())
        if not qs:
            return []
        unique = []
        for q in qs:
            if q.title not in {x.title for x in unique}:
                unique.append(q)
            if len(unique) >= 3:
                break
        return unique[:3]

    model, vectorizer, mlb = joblib.load(MODEL_PATH)
    df = pd.read_csv(DATA_PATH)
    df["skill_tags"] = df["skill_tags"].apply(_normalize_tags)

    skills = [s.lower() for s in (skills or [])]
    if len(skills) == 0:
        skills = ["python"]
    try:
        cand_vector = mlb.transform([skills])
    except Exception:
        cand_vector = np.zeros((1, len(mlb.classes_)))

    question_tag_vectors = mlb.transform(df["skill_tags"])
    similarity_scores = cosine_similarity(cand_vector, question_tag_vectors)[0]
    ranked = np.argsort(similarity_scores)[::-1]

    picked = []
    picked_titles = set()
    picked_tag_groups = []

    def is_diverse(q_tags):
        q_set = set(q_tags)
        for group in picked_tag_groups:
            if len(q_set.intersection(group)) > 0:
                return False
        return True

    for idx in ranked[:max(top_k_search, 50)]:
        row = df.iloc[idx]
        title = str(row["title"]).strip()
        if title in picked_titles:
            continue
        tags = row["skill_tags"]
        if not picked or is_diverse(tags) or len(picked) < 2:
            picked.append((title, row))
            picked_titles.add(title)
            picked_tag_groups.append(set(tags))
        if len(picked) >= 3:
            break

    if len(picked) < 3:
        db_qs = list(CodingQuestion.objects.all())
        for q in db_qs:
            if q.title in picked_titles:
                continue
            picked.append((q.title, None))
            picked_titles.add(q.title)
            if len(picked) >= 3:
                break

    # ✅ Added section below
    selected_questions = []
    for title, row in picked[:3]:
        lang = "python"
        if row is not None:
            tags = [t.lower() for t in row.get("skill_tags", [])]
            if any(t in tags for t in ["java", "spring", "kotlin"]):
                lang = "java"
            elif any(t in tags for t in ["c", "c++", "cpp"]):
                lang = "c"
            else:
                lang = "python"

            qobj = CodingQuestion.objects.filter(title=title).first()
            if qobj:
                qobj.language = lang
                selected_questions.append(qobj)
            else:
                q_temp = CodingQuestion(
                    title=row.get("title"),
                    description=row.get("description", ""),
                    starter_code=row.get("starter_code", ""),
                    test_cases=[],
                    skill_tags=row.get("skill_tags", []),
                    difficulty=row.get("difficulty", "medium"),
                )
                q_temp.language = lang
                selected_questions.append(q_temp)
        else:
            qobj = CodingQuestion.objects.filter(title=title).first()
            if qobj:
                qobj.language = "python"
                selected_questions.append(qobj)

    return selected_questions[:3]
