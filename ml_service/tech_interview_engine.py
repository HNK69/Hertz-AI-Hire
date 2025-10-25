# ml_service/tech_interview_engine.py
import random

def generate_tech_questions(skills, projects, n_project_q=3, n_skill_q=3, n_general_q=2):
    """
    Generate a list of technical interview questions
    tailored to candidate skills and projects.
    """
    questions = []

    # --- project-based questions ---
    for proj in projects[:n_project_q]:
        q = (
            f"Tell me about your project '{proj}'. "
            f"What was the biggest technical challenge you faced and how did you solve it?"
        )
        questions.append(q)

        q2 = f"What part of '{proj}' are you most proud of, and why?"
        questions.append(q2)

    # --- skill-based questions ---
    for skill in skills[:n_skill_q]:
        q = f"You mentioned working with {skill}. Can you explain a scenario where you used it effectively?"
        questions.append(q)
        q2 = f"What are some limitations or common pitfalls of {skill} that you've encountered?"
        questions.append(q2)

    # --- general reasoning / tech comprehension ---
    general_bank = [
        "When debugging a complex issue, how do you usually approach finding the root cause?",
        "How do you ensure scalability and maintainability in your code?",
        "Describe a time you optimized performance in one of your projects.",
        "What trade-offs do you consider when choosing frameworks or libraries?"
    ]
    questions.extend(random.sample(general_bank, min(n_general_q, len(general_bank))))

    random.shuffle(questions)
    return questions[:10]
