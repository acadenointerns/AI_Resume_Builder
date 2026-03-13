from keyword_extractor import extract_keywords

def score_resume(resume, job_desc):
    # Extract keywords from job description
    job_keys = set(k.lower() for k in extract_keywords(job_desc))
    
    # Extract text from resume
    resume_text = (
        resume["summary"] + " " +
        " ".join(resume["skills"]) + " " +
        " ".join([e["title"] + " " + " ".join(e["bullets"]) for e in resume["experience"]]) + " " +
        resume["objective"]
    ).lower()
    
    if not job_keys:
        return {"score": 85} # Default high score if no JD keywords found, to be safe
        
    # Calculate match
    matched = [k for k in job_keys if k in resume_text]
    
    # Weighted scoring: 
    # 1. Base keyword match (70%)
    # 2. Presence of a substantial summary (+10%)
    # 3. Proper experience bullet density (+20%)
    base_match_score = (len(matched) / len(job_keys)) * 70
    
    summary_bonus = 10 if len(resume["summary"].split()) > 40 else 5
    experience_bonus = 20 if len(resume["experience"]) >= 2 else 10
    
    total_score = int(min(base_match_score + summary_bonus + experience_bonus, 99)) # Cap at 99 to avoid "perfection"
    
    return {"score": total_score}
