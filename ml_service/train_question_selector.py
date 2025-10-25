import pandas as pd
import numpy as np
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sentence_transformers import SentenceTransformer
import joblib
from pathlib import Path

# ---------------------------------------------------
# PATHS
# ---------------------------------------------------
DATA_PATH = Path(__file__).resolve().parent / "interview_questions_cleaned.csv"
MODEL_PATH = Path(__file__).resolve().parent / "question_selector.pkl"

# ---------------------------------------------------
# LOAD DATA
# ---------------------------------------------------
print("📦 Loading dataset...")
df = pd.read_csv(DATA_PATH)

expected_cols = ["title", "description", "skill_tags", "difficulty"]
for col in expected_cols:
    if col not in df.columns:
        raise KeyError(f"Missing column: {col}")

# ---------------------------------------------------
# CLEAN + PREPROCESS
# ---------------------------------------------------
df = df.dropna(subset=["title", "description", "skill_tags", "difficulty"])
df["text"] = (df["title"].astype(str) + " " + df["description"].astype(str)).str.lower()
df["skill_tags"] = df["skill_tags"].apply(
    lambda x: [t.strip().lower() for t in str(x).split(",") if t.strip()]
)

# Optional: balance difficulty labels
min_count = df["difficulty"].value_counts().min()
df_balanced = pd.concat([
    df[df["difficulty"] == d].sample(min_count, random_state=42)
    for d in df["difficulty"].unique()
])
df = df_balanced.reset_index(drop=True)

# ---------------------------------------------------
# TEXT EMBEDDINGS
# ---------------------------------------------------
print("🔤 Generating sentence embeddings...")
embedder = SentenceTransformer("all-MiniLM-L6-v2")
text_embeddings = embedder.encode(df["text"].tolist(), show_progress_bar=True)

# ---------------------------------------------------
# TAG ENCODING
# ---------------------------------------------------
print("🏷️ Encoding skill tags...")
mlb = MultiLabelBinarizer()
X_tags = mlb.fit_transform(df["skill_tags"])

# Combine features
X = np.hstack((text_embeddings, X_tags))
y = df["difficulty"].astype(str)

# ---------------------------------------------------
# TRAIN / TEST SPLIT
# ---------------------------------------------------
print("🧠 Splitting data...")
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# ---------------------------------------------------
# MODEL TRAINING
# ---------------------------------------------------
print("🚀 Training GradientBoosting model...")
model = GradientBoostingClassifier(
    n_estimators=400,
    learning_rate=0.05,
    max_depth=6,
    random_state=42
)
model.fit(X_train, y_train)
acc = model.score(X_test, y_test)
print(f"✅ Model trained successfully with accuracy: {acc:.2f}")

# ---------------------------------------------------
# SAVE MODEL
# ---------------------------------------------------
joblib.dump((model, embedder, mlb), MODEL_PATH)
print(f"💾 Model + encoders saved at: {MODEL_PATH}")
