from keyword_extractor import extract_keywords
from resume_engine import generate_resume

def test_nlp_extraction():
    jd = "Seeking a Senior Python Developer with expertise in Flask, PostgreSQL, and AWS. Experience with Machine Learning and React is a plus."
    keywords = extract_keywords(jd)
    print(f"Extracted Keywords: {keywords}")
    
    assert "python" in keywords
    assert "flask" in keywords
    assert "postgresql" in keywords
    assert "aws" in keywords
    print("✓ Keyword extraction test passed!")

def test_resume_generation():
    profile = {
        "name": "Jane Doe",
        "location": "San Francisco, CA",
        "github": "https://github.com/janedoe",
        "projects": ["Web-Crawler", "Flask-API-Service", "ML-Dashboard"]
    }
    jd = "Looking for a Software Engineer with Python and Flask experience."
    
    resume = generate_resume(profile, jd)
    print(f"Generated Resume Summary: {resume['summary']}")
    print(f"Skills: {resume['skills']}")
    
    assert "python" in resume['skills']
    assert "flask" in resume['skills']
    assert len(resume['experience']) == 3
    print("✓ Resume generation test passed!")

if __name__ == "__main__":
    try:
        test_nlp_extraction()
        test_resume_generation()
        print("\nAll automated tests passed successfully!")
    except Exception as e:
        print(f"Test failed: {e}")
