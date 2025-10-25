# ml_service/hr_interview_engine.py
import random

def generate_hr_questions(n=6):
    """
    Return a list of HR/behavioral interview questions.
    """
    hr_bank = [
        "Tell me about yourself and what drives you.",
        "Why did you choose this career path?",
        "Describe a time you faced a challenge and how you handled it.",
        "What are your strengths and weaknesses?",
        "How do you handle feedback or criticism?",
        "Where do you see yourself in the next 2 years?",
        "What does teamwork mean to you?",
        "Describe a situation where you showed leadership.",
        "How do you deal with pressure or tight deadlines?",
        "Why should we hire you?",
    ]
    random.shuffle(hr_bank)
    return hr_bank[:n]
