"""
Enhanced resume parser that supports PDF, DOCX, and TXT files.
Dependencies:
  pip install pymupdf python-docx sentence-transformers
"""

import re
import fitz  # PyMuPDF
from pathlib import Path
from sentence_transformers import SentenceTransformer

try:
    import docx
except ImportError:
    docx = None

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
_EMBED_MODEL = None


def _get_model():
    global _EMBED_MODEL
    if _EMBED_MODEL is None:
        _EMBED_MODEL = SentenceTransformer(MODEL_NAME)
    return _EMBED_MODEL


def extract_text_from_pdf(path):
    doc = fitz.open(path)
    parts = [page.get_text() for page in doc]
    return "\n".join(parts)


def extract_text_from_docx(path):
    if not docx:
        raise ImportError("python-docx not installed.")
    document = docx.Document(path)
    return "\n".join([p.text for p in document.paragraphs])


def extract_text_from_txt(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def naive_skill_extractor(text, top_k=20):
    text_lower = text.lower()
    seeds = [
        "python", "django", "flask", "pandas", "numpy", "sql", "postgresql",
        "mysql", "aws", "docker", "kubernetes", "rest", "api", "javascript",
        "react", "node", "git", "tensorflow", "pytorch", "sklearn", "ml",
        "nlp", "computer vision", "cv", "linux", "bash", "c++", "java",
    ]
    found = set()
    for s in seeds:
        if s in text_lower:
            found.add(s)
    m = re.search(r"(skills|technical skills|technologies)[:\-\n]+([\s\S]{0,300})", text_lower)
    if m:
        snippet = m.group(2)
        tokens = re.split(r"[,;\n\|]", snippet)
        for t in tokens:
            t = re.sub(r"[^a-z0-9+\#\.\- ]", "", t).strip()
            if len(t) > 1 and len(found) < top_k:
                found.add(t)
    return list(found)[:top_k]


def embed_text(text):
    model = _get_model()
    return model.encode(text).tolist()


def parse_resume(path):
    """
    Detect file type and extract text accordingly.
    Supports: PDF, DOCX, TXT
    """
    path = Path(path)
    text = ""
    suffix = path.suffix.lower()

    try:
        if suffix == ".pdf":
            text = extract_text_from_pdf(path)
        elif suffix == ".docx":
            text = extract_text_from_docx(path)
        elif suffix == ".txt":
            text = extract_text_from_txt(path)
        else:
            raise ValueError(f"Unsupported file type: {suffix}")
    except Exception as e:
        text = f"(Error reading {suffix}: {e})"

    skills = naive_skill_extractor(text)
    try:
        embedding = embed_text(text)
    except Exception:
        embedding = []

    return {"text": text, "skills": skills, "embedding": embedding}


def extract_resume_skills(resume_text: str):
    common_skills = ["C", "C++", "Java", "Python", "DSA", "OOP", "MySQL", "HTML", "CSS"]
    found = [s for s in common_skills if s.lower() in resume_text.lower()]
    return found[:3] if found else ["DSA"]
