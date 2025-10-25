import pandas as pd
import random, json, uuid
from pathlib import Path

SRC = Path(__file__).resolve().parent / "interview_questions_500.csv"
DEST = Path(__file__).resolve().parent / "interview_questions_cleaned.csv"

df = pd.read_csv(SRC)

# ---- Basic clean-up ----
df = df.drop_duplicates(subset=["description"], keep="first")
df["skill_tags"] = df["skill_tags"].fillna("").apply(lambda x: [t.strip().lower() for t in str(x).split(",") if t.strip()])
df["difficulty"] = df["difficulty"].fillna("medium").str.lower()

# ---- buckets ----
main_skills = ["python","ml","sql","flask","django","api","c","java"]
dsa_tags = ["dsa","algorithm","logic","data structures","arrays","strings","recursion"]
secondary = ["web","analytics","pandas","linux","git","deployment","api","backend"]

def make_question(base, tag_group, diff=None):
    """Create new question synthetically"""
    t = random.choice(tag_group)
    difficulty = diff or random.choice(["easy","medium","hard"])
    title = f"{t.title()} Problem — {uuid.uuid4().hex[:4]}"
    desc = f"Write a {t} function to solve a realistic interview challenge. Include edge-case handling and O(n) complexity where possible."
    starter = "def solution():\n    pass" if "python" in t else "public class Solution {\n    public static void main(String[] args) {\n        // code\n    }\n}"
    tc = json.dumps([{"input":"2 3","output":"5"}])
    return dict(title=title, description=desc, starter_code=starter, test_cases=tc, skill_tags=",".join(tag_group), difficulty=difficulty)

# ---- ensure 200/200/100 counts ----
main_df = df[df["skill_tags"].apply(lambda x: any(t in main_skills for t in x))].head(200)
dsa_df  = df[df["skill_tags"].apply(lambda x: any(t in dsa_tags for t in x))].head(200)
sec_df  = df[df["skill_tags"].apply(lambda x: any(t in secondary for t in x))].head(100)

# ---- fill shortages ----
while len(main_df) < 200:
    main_df = pd.concat([main_df, pd.DataFrame([make_question(df, main_skills)])])
while len(dsa_df) < 200:
    dsa_df = pd.concat([dsa_df, pd.DataFrame([make_question(df, dsa_tags)])])
while len(sec_df) < 100:
    sec_df = pd.concat([sec_df, pd.DataFrame([make_question(df, secondary)])])

final = pd.concat([main_df, dsa_df, sec_df]).sample(frac=1, random_state=42).reset_index(drop=True)
final.to_csv(DEST, index=False)
print(f"✅ Cleaned + augmented dataset saved to {DEST} with {len(final)} rows")
