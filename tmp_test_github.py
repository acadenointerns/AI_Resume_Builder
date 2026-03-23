import requests

def test_fetch(username):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Try repos directly
    print(f"Testing direct repo fetch for: {username}")
    repos_url = f"https://api.github.com/users/{username}/repos?per_page=100"
    try:
        r = requests.get(repos_url, headers=headers)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            repos = r.json()
            print(f"Found {len(repos)} repos")
            for repo in repos[:5]:
                print(f"- {repo['name']} (Fork: {repo['fork']})")
        else:
            print(f"Error Body: {r.text[:200]}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_fetch("Anulalsn")
