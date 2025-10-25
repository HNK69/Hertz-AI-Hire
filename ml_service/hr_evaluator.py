# ml_service/hr_evaluator.py
import re

def evaluate_hr_answer(answer: str) -> int:
    if not answer or len(answer.strip()) < 5:
        return 0

    score = 0
    words = answer.lower().split()

    # 1️⃣ length-based
    if len(words) > 15:
        score += 1

    # 2️⃣ teamwork / leadership / goals keywords
    keywords = ["team", "leader", "goal", "challenge", "learn", "improve", "growth", "project", "responsible", "help"]
    score += sum(1 for k in keywords if k in words)

    # 3️⃣ positivity markers
    if any(k in words for k in ["enjoy", "love", "passionate", "confident", "motivated", "excited"]):
        score += 1

    # 4️⃣ self-reflective structure
    if re.search(r"\bi\b.*\b(can|did|will|am|want)\b", answer.lower()):
        score += 1

    return min(score, 5)
