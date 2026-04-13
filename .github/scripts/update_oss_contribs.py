import json
import os
import re
import urllib.parse
import urllib.request

USER = os.environ["GITHUB_USER"]
TOKEN = os.environ["GH_TOKEN"]
README = "README.md"

START = "<!--START_SECTION:oss-contributions-->"
END = "<!--END_SECTION:oss-contributions-->"

def api_get(url: str):
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def fetch_repos():
    repos = []
    seen = set()

    # merged PRs authored by you, excluding your own repos
    for page in range(1, 6):  # up to 500 PRs scanned
        q = f"author:{USER} type:pr -user:{USER} is:public is:merged"
        url = f"https://api.github.com/search/issues?q={urllib.parse.quote_plus(q)}&per_page=100&page={page}"
        data = api_get(url)
        items = data.get("items", [])
        if not items:
            break

        for it in items:
            repo_url = it.get("repository_url", "")
            # e.g. https://api.github.com/repos/ministackorg/ministack
            if "/repos/" not in repo_url:
                continue
            owner_repo = repo_url.split("/repos/")[1]
            owner = owner_repo.split("/")[0]
            if owner.lower() == USER.lower():
                continue
            if owner_repo not in seen:
                seen.add(owner_repo)
                repos.append(owner_repo)

    return repos

def build_block(repos):
    if not repos:
        return "- No external contributions found yet."

    lines = ["<div align=\"center\">", ""]
    for r in repos[:12]:
        label = urllib.parse.quote_plus(r.replace("-", "--"))
        badge = (
            f"[![{r}](https://img.shields.io/badge/{label}-181717?"
            f"style=for-the-badge&logo=github)](https://github.com/{r})"
        )
        lines.append(badge)
    lines.extend(["", "</div>"])
    return "\n".join(lines)

def main():
    repos = fetch_repos()
    new_block = build_block(repos)

    with open(README, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = re.compile(
        rf"{re.escape(START)}.*?{re.escape(END)}",
        flags=re.DOTALL
    )
    replacement = f"{START}\n{new_block}\n{END}"

    if pattern.search(content):
        updated = pattern.sub(replacement, content)
    else:
        updated = content + "\n\n" + replacement + "\n"

    with open(README, "w", encoding="utf-8") as f:
        f.write(updated)

if __name__ == "__main__":
    main()
