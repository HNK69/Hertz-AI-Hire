# ml_service/tech_evaluator.py
from textblob import TextBlob
import re

def evaluate_tech_answer(answer):
    """
    Heuristic scoring for technical interview answers.
    Returns a float (0 - 5)
    """
    if not answer or not answer.strip():
        return 0.0

    # measure answer length (for completeness)
    length_score = min(len(answer.split()) / 30, 1)  # 30+ words = full

    # penalize filler or uncertain language
    filler_words = len(re.findall(r"\b(um|uh|maybe|i think|not sure)\b", answer.lower()))
    clarity_score = max(0, 1 - (filler_words / 5))

    # grammar using TextBlob
    corrected = TextBlob(answer).correct().string
    grammar_score = 1.0 if corrected == answer else 0.8

    # technical keyword relevance
    tech_terms = ["python", "django", "api", "ml", "model", "data", "flask", "sql", "deployment"]
    keyword_hits = sum(1 for t in tech_terms if t in answer.lower())
    keyword_score = min(keyword_hits / 5, 1)

    # final composite
    final_score = round(((length_score * 1.5) + clarity_score + grammar_score + keyword_score) / 4 * 5, 2)
    return final_score
