import requests

def fetch_github_profile(username):
    if "github.com" in username:
        username = username.rstrip("/").split("/")[-1]

    url = f"https://api.github.com/users/{username}"
    response = requests.get(url)

    if response.status_code != 200:
        return {
            "name": username.replace("-", " ").title(),
            "location": "",
            "github": f"https://github.com/{username}",
            "projects": []
        }

    data = response.json()

    # Fetch repositories
    repos = requests.get(data["repos_url"]).json()

    projects = []
    for repo in repos:
        repo_name = repo["name"]
        # Skip profile READMEs and forks
        if repo_name.lower() == username.lower() or repo.get("fork"):
            continue
        
        projects.append({
            "name": repo_name.replace("-", "_").replace("_", " ").title(),
            "url": repo.get("html_url", "")
        })
        if len(projects) >= 6: # Professional limit
            break

    name = data.get("name")
    if not name or name.strip() == "":
        name = username.replace("-", " ").title()

    return {
        "name": name,
        "location": data.get("location", ""),
        "github": f"https://github.com/{username}",
        "projects": projects
    }
