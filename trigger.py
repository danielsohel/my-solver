import os
import requests


def main():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("Error: GITHUB_TOKEN environment variable is not set.")
        return

    problem = input("Paste your LeetCode problem:\n")

    url = "https://api.github.com/repos/danielsohel/my-solver/actions/workflows/solve.yml/dispatches"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    data = {
        "ref": "main",
        "inputs": {"problem": problem},
    }

    resp = requests.post(url, headers=headers, json=data)

    if resp.status_code == 204:
        print("Workflow triggered! Check GitHub Actions for progress.")
    else:
        print(f"Failed to trigger workflow: {resp.status_code} {resp.text}")


if __name__ == "__main__":
    main()
