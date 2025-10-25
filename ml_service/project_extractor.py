# ml_service/project_extractor.py
import re
from typing import List

PROJECT_HEADING_PATTERNS = [
    r"(?:projects?)[:\s]*",            # "Projects:" or "Project:"
    r"(?:selected projects)[:\s]*",
    r"(?:notable projects)[:\s]*",
    r"(?:academic projects)[:\s]*",
    r"(?:personal projects)[:\s]*",
]

def _split_lines(text: str) -> List[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]

def extract_projects_from_text(text: str, max_projects: int = 8):
    """
    Extract concise project names or one-liners.
    Avoids full section dumps and filters non-project lines.
    """
    if not text:
        return []

    lines = [l.strip() for l in text.splitlines() if 5 < len(l.strip()) < 180]
    projects = []

    for i, line in enumerate(lines):
        # detect start of "Projects" section
        if re.match(r"(?i)^projects?(\s*\(.*\))?:?$", line):
            for nxt in lines[i+1:i+15]:
                clean = re.sub(r"^[\-\u2022\*\d\.\)\s]+", "", nxt).strip()
                if not clean or re.match(r"(?i).*(experience|education|skills|highlights).*", clean):
                    continue
                if re.search(r"(project|app|system|application|model|platform|tool|api|engine|dashboard)", clean, re.I):
                    projects.append(clean)
            break

    # fallback: pick only lines mentioning "project"/"app"/"model"
    if not projects:
        for l in lines:
            if re.search(r"(project|app|system|model|tool)", l, re.I) and not re.search(r"(experience|skills|education)", l, re.I):
                clean = re.sub(r"^[\-\u2022\*\d\.\)\s]+", "", l).strip()
                if 8 < len(clean) < 150:
                    projects.append(clean)

    # keep concise, non-duplicate results
    seen = set()
    clean_projects = []
    for p in projects:
        p = re.sub(r"[-–•]+\s*", "", p).strip()
        if p and p not in seen:
            seen.add(p)
            clean_projects.append(p)
    return clean_projects[:max_projects]
