from keyword_extractor import extract_keywords
import random

def generate_impact_bullets(project_name, skills):
    """
    Generates high-impact, professional bullet points with quantified metrics.
    """
    # Clean project name for display
    display_name = project_name.replace("_", " ").replace("Webapp", "Web App").title()
    if "Alzeimer" in display_name:
        display_name = display_name.replace("Alzeimer", "Alzheimer's")

    metrics = [
        f"{random.randint(15, 45)}%",
        f"{random.randint(2, 10)}x",
        f"{random.randint(50, 500)}ms",
        f"${random.randint(5, 50)}k",
        "over 1,000+",
        "30% faster"
    ]

    templates = [
        f"Spearheaded the development of {display_name}, integrating {', '.join(skills[:2])} to enhance system throughput by {random.choice(metrics[:2])}.",
        f"Executed end-to-end design and implementation of the {display_name} module, leveraging {skills[0] if skills else 'modern architecture'} for scalable deployment.",
        f"Optimized performance metrics by {random.choice(metrics)} through advanced application of {skills[1] if len(skills)>1 else 'resource management'}.",
        f"Collaborated with cross-functional teams to deliver an integrated solution, ensuring high code quality and reducing technical debt by {random.choice(metrics)}.",
        f"Implemented robust {skills[0] if skills else 'backend'} solutions, reducing latency by {random.choice(metrics[2:3])} and improving user interaction response times.",
        f"Directed the technical roadmap for the project, utilizing {', '.join(skills[:3])} to solve complex computational challenges for {random.choice(metrics[4:5])} users.",
        f"Engineered a high-performance module using {skills[0] if skills else 'optimized algorithms'}, resulting in a {random.choice(metrics)} increase in operational efficiency."
    ]

    # Ensure variety and avoid repeating project name in every bullet
    selected = random.sample(templates, min(3, len(templates)))
    return selected


def generate_resume(profile, job_desc, personal_details=None):
    if personal_details is None:
        personal_details = {}

    jd_keywords = extract_keywords(job_desc)
    raw_skills  = list(dict.fromkeys(jd_keywords[:20]))

    # Merge manually-supplied skills (de-duplicate, preserving order)
    manual_skills = personal_details.get("manual_skills", [])
    for ms in manual_skills:
        if ms not in raw_skills:
            raw_skills.append(ms)

    # Categorize skills for professional look
    languages = [s for s in raw_skills if s.lower() in [
        "python", "javascript", "typescript", "java", "cpp", "c++", "c#",
        "go", "rust", "php", "sql", "html", "css", "kotlin", "swift", "r", "scala"
    ]]

    framework_list = [
        "react", "next.js", "node.js", "django", "flask", "fastapi", "spring",
        "vue", "angular", "tensorflow", "pytorch", "keras", "laravel", "express",
        "flutter", "react native", "bootstrap", "tailwind", "jquery", "svelte",
        "nuxt", "fastify", "nestjs", "redux", "graphql"
    ]
    frameworks = [s for s in raw_skills if s.lower() in framework_list]

    # Ensure frameworks isn't empty if we have general technical skills
    if not frameworks and raw_skills:
        frameworks = [s for s in raw_skills if s not in languages][:5]

    # Final fallback if still empty (professional defaults)
    if not frameworks:
        frameworks = ["React", "Node.js", "Git"]

    tools = [s for s in raw_skills if s not in languages and s not in frameworks][:10]
    if not tools:
        tools = ["Docker", "AWS", "CI/CD", "Agile"]

    skills_categorized = {
        "Languages":               languages  if languages  else ["Python", "JavaScript", "SQL"],
        "Frameworks & Libraries":  frameworks,
        "Tools & Platforms":       tools
    }

    experience = []
    for p in profile["projects"]:
        project_name  = p["name"]
        project_url   = p["url"]

        # Use simple project skills if not explicitly found in JD
        project_skills = [s for s in raw_skills if s.lower() in project_name.lower()]
        if not project_skills:
            project_skills = random.sample(raw_skills, min(3, len(raw_skills))) if raw_skills else ["Software Engineering", "System Design"]

        experience.append({
            "title":   project_name,
            "url":     project_url,
            "bullets": generate_impact_bullets(project_name, project_skills)
        })

    # Summary with quantified impact
    summary = (
        f"Results-oriented Software Engineer with a strong foundation in {', '.join(raw_skills[:3]) if len(raw_skills)>2 else 'software development'}. "
        f"Proven expertise in architecting high-scale systems that delivered up to a {random.randint(20, 40)}% increase in efficiency. "
        f"Demonstrated history of optimizing performance and enhancing user experience across diverse project portfolios using {raw_skills[3] if len(raw_skills)>3 else 'modern stacks'}. "
        f"Committed to technical excellence and reducing operational costs by over {random.randint(10, 25)}% through innovative engineering."
    )

    objective = (
        f"To leverage my extensive background in {', '.join(raw_skills[4:7]) if len(raw_skills)>6 else 'software engineering'} "
        f"to provide strategic value and technical leadership within a forward-thinking engineering team."
    )

    return {
        "name":         profile["name"],
        "location":     profile.get("location", ""),
        "github":       profile.get("github", ""),
        "portfolio":    profile.get("portfolio", ""),
        # Personal contact details
        "email":        personal_details.get("email", ""),
        "phone":        personal_details.get("phone", ""),
        "linkedin":     personal_details.get("linkedin", ""),
        # Sections
        "summary":      summary,
        "skills":       skills_categorized,
        "experience":   experience,
        "objective":    objective,
        # New sections
        "education":    personal_details.get("education", []),
        "achievements": personal_details.get("achievements", []),
    }
