import os
import sys

import requests
from dotenv import load_dotenv

from wifi import switch_to_hotspot, switch_to_home

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QUESTIONS_DIR = os.path.join(BASE_DIR, "questions")

# Question files and their types
QUESTIONS = [
    {"file": "q1.c", "type": "q1_analysis"},
    {"file": "q2.c", "type": "q2_solve"},
    {"file": "q3.c", "type": "q3_solve"},
    {"file": "q4.c", "type": "q4_backtracking"},
]

DISPATCH_URL = "https://api.github.com/repos/danielsohel/my-solver/actions/workflows/solve.yml/dispatches"


def read_question(filepath):
    if not os.path.exists(filepath):
        return None
    with open(filepath) as f:
        content = f.read()
    return content if content.strip() else None


def trigger_workflow(token, problem, question_type):
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    data = {
        "ref": "main",
        "inputs": {
            "problem": problem,
            "question_type": question_type,
        },
    }
    return requests.post(DISPATCH_URL, headers=headers, json=data)


def main():
    load_dotenv()
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("Error: GITHUB_TOKEN must be set in .env")
        sys.exit(1)

    # Read all question files
    questions_to_send = []
    for q in QUESTIONS:
        filepath = os.path.join(QUESTIONS_DIR, q["file"])
        content = read_question(filepath)
        if content is None:
            print(f"Skipping {q['file']} (not found or empty)")
            continue
        questions_to_send.append({
            "file": q["file"],
            "type": q["type"],
            "content": content,
        })

    if not questions_to_send:
        print("Error: No question files found with content in questions/")
        sys.exit(1)

    print(f"Found {len(questions_to_send)} question(s) to send.")

    try:
        # Switch to hotspot
        print("\n>>> Switching to hotspot ...")
        switch_to_hotspot()

        # Trigger workflows
        print("\n>>> Triggering GitHub Actions workflows ...")
        for q in questions_to_send:
            print(f"  Sending {q['file']} ({q['type']}) ...")
            resp = trigger_workflow(token, q["content"], q["type"])
            if resp.status_code == 204:
                print(f"    Triggered successfully!")
            else:
                print(f"    Failed: {resp.status_code} {resp.text}")
    finally:
        # Reconnect to home WiFi
        print("\n>>> Reconnecting to home WiFi ...")
        switch_to_home()

    print("\nDone! Check GitHub Actions for progress, then run check_email.py")


if __name__ == "__main__":
    main()
