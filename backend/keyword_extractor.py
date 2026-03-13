try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
except (ImportError, Exception):
    nlp = None
import re

# Comprehensive set of technical terms
TECH_TERMS = {
    "python", "java", "c++", "c#", "javascript", "typescript", "html", "css", "php", "ruby", "rust", "go", "kotlin", "swift",
    "react", "angular", "vue", "next.js", "node.js", "express", "django", "flask", "fastapi", "spring boot", "laravel",
    "sql", "mysql", "postgresql", "mongodb", "redis", "firebase", "sqlite", "oracle", "mariadb", "cassandra",
    "docker", "kubernetes", "aws", "azure", "gcp", "devops", "ci/cd", "git", "github", "terraform", "jenkins", "ansible",
    "machine learning", "deep learning", "nlp", "ai", "ml", "tensorflow", "pytorch", "keras", "scikit-learn",
    "pandas", "numpy", "matplotlib", "seaborn", "opencv", "scipy", "nltk", "spacy",
    "rest api", "graphql", "microservices", "serverless", "agile", "scrum", "kanban",
    "linux", "bash", "power bi", "tableau", "excel", "analytics", "hadoop", "spark", "kafka", "elk stack",
    "flutter", "react native", "android", "ios", "unity", "unreal engine", "blockchain"
}

# Generic words that often appear in JDs but aren't specific technical skills
# We must be EXTREMELY AGGRESSIVE here.
EXCLUDE_TERMS = {
    "bachelor", "master", "degree", "computer", "science", "information", "technology", "engineering",
    "similar", "preference", "equivalent", "depth", "data", "experience", "years", "knowledge",
    "working", "requirements", "strong", "excellent", "plus", "understanding", "good", "proficient",
    "familiarity", "ability", "skills", "tools", "environment", "field", "industry", "professional",
    "university", "college", "graduate", "study", "education", "discipline", "related", "equivalent",
    "candidates", "applicant", "position", "role", "team", "organization", "company", "culture",
    "communication", "written", "verbal", "problem", "solving", "analytical", "critical", "thinking",
    "design", "development", "implementation", "support", "maintenance", "optimization", "testing",
    "quality", "assurance", "best", "practices", "principles", "concepts", "standards", "processes",
    "methodologies", "frameworks", "libraries", "systems", "applications", "solutions", "platforms",
    "projects", "tasks", "responsibilities", "requirements", "qualifications", "preferred", "required",
    "ideal", "successful", "highly", "motivated", "detail", "oriented", "self", "starter", "fast", "paced",
    "top", "tier", "cutting", "edge", "innovative", "impact", "growth", "opportunity", "growth", "career"
}

def extract_keywords(text):
    if not text:
        return []
    
    text_lower = text.lower()
    extracted = []
    
    # 1. Exact matches from TECH_TERMS (Word-bound)
    for term in TECH_TERMS:
        pattern = r'\b' + re.escape(term) + r'\b'
        if re.search(pattern, text_lower):
            extracted.append(term.title())
    
    # 2. Add extra discovery with SpaCy
    if nlp:
        doc = nlp(text_lower)
        for ent in doc.ents:
            if ent.label_ in ["ORG", "PRODUCT"]:
                clean_ent = ent.text.strip().lower()
                # Stricter checks: no common words, no excludes, length > 2
                if clean_ent not in EXCLUDE_TERMS and clean_ent not in [t.lower() for t in extracted] and len(clean_ent) > 2:
                    # Ignore common verbs/adjectives that SpaCy might misclassify
                    token = doc[ent.start]
                    if token.pos_ not in ["VERB", "ADJ"]:
                        extracted.append(clean_ent.title())

    # 3. Aggressive filtering
    final_skills = []
    for skill in extracted:
        skill_lower = skill.lower()
        if skill_lower not in EXCLUDE_TERMS and not any(exclude in skill_lower for exclude in ["bachelor", "master", "degree"]):
            # Ensure it's not JUST a common english word (simple check)
            if skill_lower in TECH_TERMS or len(skill_lower) > 3:
                final_skills.append(skill)
                    
    return list(dict.fromkeys(final_skills))[:20]
