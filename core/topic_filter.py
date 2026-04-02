"""
Topic Filter for UniUs Chatbot.
Determines whether a user's question is related to US universities.
"""

from rapidfuzz import fuzz, process
from core.retriever import ABBREVIATIONS

# Keywords that indicate a university-related question
UNIVERSITY_KEYWORDS = [
    # Institution types
    "university", "college", "institute", "school", "academy", "seminary",
    "campus", "institution",
    # Admissions
    "admission", "admissions", "acceptance rate", "acceptance", "apply",
    "application", "enroll", "enrollment", "enrolled", "gpa", "sat", "act",
    "requirement", "requirements", "deadline", "deadlines",
    # Academics
    "major", "majors", "minor", "degree", "degrees", "program", "programs",
    "course", "courses", "curriculum", "department", "faculty", "professor",
    "research", "study", "education", "academic", "graduate", "undergraduate",
    "bachelor", "master", "phd", "doctoral", "mba",
    # Financial
    "tuition", "fee", "fees", "scholarship", "scholarships", "financial aid",
    "cost", "affordable", "expensive", "cheap",
    # Campus life
    "dormitory", "dorm", "housing", "student life", "clubs", "athletics",
    "sports", "library", "cafeteria", "dining",
    # Rankings & reputation
    "ranking", "rankings", "ranked", "top", "best", "prestigious",
    "ivy league", "tier", "reputation",
    # Location
    "located", "location", "where is", "address",
    # General
    "student", "students", "alumni", "graduation", "commencement",
    "accreditation", "accredited", "public university", "private university",
    "community college", "technical college", "liberal arts",
    # Specific US education terms
    "fafsa", "common app", "transfer", "credits", "semester", "quarter",
    "online degree", "distance learning",
]

# Greeting patterns (we allow these through with a special flag)
GREETING_PATTERNS = [
    "hi", "hello", "hey", "good morning", "good afternoon", "good evening",
    "howdy", "what's up", "sup", "yo", "greetings", "hola",
    "how are you", "what can you do", "help", "who are you",
    "what are you", "tell me about yourself",
]


def is_greeting(question: str) -> bool:
    """Check if the input is a greeting or general bot query."""
    q = question.lower().strip().rstrip("?!.")
    for pattern in GREETING_PATTERNS:
        if q == pattern or q.startswith(pattern + " ") or q.startswith(pattern + ","):
            return True
    return False


def _contains_university_reference(question: str) -> float:
    """
    Check if the question contains a known university abbreviation or name.
    Returns a score 0.0-1.0.
    """
    q_lower = question.lower().strip()
    words = q_lower.split()
    
    # Check single-word and multi-word abbreviations
    for abbr in ABBREVIATIONS:
        if abbr in words or abbr in q_lower:
            return 0.8
    
    return 0.0


def is_university_question(question: str, university_names: list = None) -> tuple:
    """
    Determine if a question is related to US universities.
    
    Returns:
        tuple: (is_relevant: bool, confidence: float, is_greeting: bool)
        - is_relevant: True if the question is about US universities
        - confidence: 0.0 to 1.0 score
        - is_greeting_flag: True if it's a greeting
    """
    q_lower = question.lower().strip()
    
    # Check if it's a greeting
    if is_greeting(question):
        return (True, 1.0, True)
    
    # Very short queries (1-2 words) — still check abbreviations
    if len(q_lower.split()) <= 1:
        abbr_score = _contains_university_reference(question)
        if abbr_score > 0:
            return (True, abbr_score, False)
        if not any(kw in q_lower for kw in UNIVERSITY_KEYWORDS):
            return (False, 0.0, False)
    
    score = 0.0
    
    # Check keyword presence (up to 0.6 score)
    keyword_hits = 0
    for keyword in UNIVERSITY_KEYWORDS:
        if keyword in q_lower:
            keyword_hits += 1
    
    if keyword_hits > 0:
        score += min(0.6, keyword_hits * 0.2)
    
    # Check for known abbreviation (up to 0.8 score)
    abbr_score = _contains_university_reference(question)
    score = max(score, abbr_score)
    
    # Check for university name mention via fuzzy matching (up to 0.5 score)
    if university_names and score < 0.5:
        result = process.extractOne(
            q_lower, 
            university_names, 
            scorer=fuzz.partial_ratio,
            score_cutoff=70
        )
        if result:
            name_score = result[1] / 100.0
            score += name_score * 0.5
    
    # Normalize to 0-1 range
    confidence = min(1.0, score)
    
    # Threshold: anything above 0.15 is considered relevant
    is_relevant = confidence >= 0.15
    
    return (is_relevant, confidence, False)
