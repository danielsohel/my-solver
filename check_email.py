import argparse
import email
import imaplib
import os
import re
import sys

from dotenv import load_dotenv

from wifi import switch_to_hotspot, switch_to_home

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QUESTIONS_DIR = os.path.join(BASE_DIR, "questions")

# Map email subject suffix to question file
QUESTION_MAP = {
    "Q1": {"file": "q1.c", "type": "analysis"},
    "Q2": {"file": "q2.c", "type": "solve"},
    "Q3": {"file": "q3.c", "type": "solve"},
    "Q4": {"file": "q4.c", "type": "solve"},
}

SUBJECT_PREFIX = "GPT Solution:"


def extract_solution(body):
    """Extract code between ===SOLUTION_START=== and ===SOLUTION_END=== markers."""
    match = re.search(
        r"===SOLUTION_START===\s*\n(.*?)\n\s*===SOLUTION_END===",
        body,
        re.DOTALL,
    )
    if match:
        return match.group(1).strip()
    return None


def fetch_solutions(gmail_user, gmail_pass, unread_only=True):
    """Fetch all GPT Solution emails, grouped by question number."""
    solutions = {}

    with imaplib.IMAP4_SSL("imap.gmail.com", 993) as mail:
        mail.login(gmail_user, gmail_pass)
        mail.select("INBOX")

        for q_num in QUESTION_MAP:
            subject_filter = f"{SUBJECT_PREFIX} {q_num}"
            if unread_only:
                criteria = f'(UNSEEN SUBJECT "{subject_filter}")'
            else:
                criteria = f'(SUBJECT "{subject_filter}")'

            status, data = mail.search(None, criteria)
            if status != "OK" or not data[0]:
                continue

            # Use the latest email for this question
            msg_ids = data[0].split()
            latest_id = msg_ids[-1]

            status, msg_data = mail.fetch(latest_id, "(RFC822)")
            if status != "OK":
                continue

            msg = email.message_from_bytes(msg_data[0][1])
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode(
                            part.get_content_charset() or "utf-8", errors="replace"
                        )
                        break
            else:
                body = msg.get_payload(decode=True).decode(
                    msg.get_content_charset() or "utf-8", errors="replace"
                )

            solutions[q_num] = {
                "date": msg["Date"],
                "subject": msg["Subject"],
                "body": body,
            }

    return solutions


def paste_solution(q_num, solution_code, q_info):
    """Write the solution into the corresponding .c file."""
    filepath = os.path.join(QUESTIONS_DIR, q_info["file"])

    # Read existing content
    existing = ""
    if os.path.exists(filepath):
        with open(filepath) as f:
            existing = f.read()

    with open(filepath, "w") as f:
        if q_info["type"] == "analysis":
            # Q1: paste the annotated code (which includes complexity comments)
            # Keep original code, append analysis as comments
            f.write(existing.rstrip() + "\n\n")
            f.write("// === GPT Complexity Analysis ===\n")
            for line in solution_code.splitlines():
                f.write(f"// {line}\n")
        else:
            # Q2-Q4: replace file content with the solution
            # Keep original question comment at top, add solution below
            f.write(existing.rstrip() + "\n\n")
            f.write("// === GPT Solution ===\n")
            f.write(solution_code + "\n")

    return filepath


def main():
    parser = argparse.ArgumentParser(description="Check Gmail for exam solutions")
    parser.add_argument(
        "--all", action="store_true", help="Show all solution emails (not just unread)"
    )
    args = parser.parse_args()

    load_dotenv()
    gmail_user = os.environ.get("GMAIL_USER")
    gmail_pass = os.environ.get("GMAIL_PASS")

    if not gmail_user or not gmail_pass:
        print("Error: GMAIL_USER and GMAIL_PASS must be set in .env")
        sys.exit(1)

    try:
        # Switch to hotspot
        print(">>> Switching to hotspot ...")
        switch_to_hotspot()

        # Fetch emails
        unread_only = not args.all
        label = "unread " if unread_only else ""
        print(f"\nChecking for {label}solution emails ...")

        solutions = fetch_solutions(gmail_user, gmail_pass, unread_only=unread_only)

        if not solutions:
            print("No solution emails found.")
            return

        print(f"Found solutions for: {', '.join(sorted(solutions.keys()))}\n")

        # Parse and paste solutions
        for q_num in sorted(solutions.keys()):
            sol = solutions[q_num]
            q_info = QUESTION_MAP[q_num]

            print(f"  {q_num}: {sol['subject']}  ({sol['date']})")

            code = extract_solution(sol["body"])
            if code is None:
                print(f"    WARNING: Could not find ===SOLUTION_START=== markers in {q_num} email.")
                print(f"    Pasting full body as fallback.")
                code = sol["body"]

            filepath = paste_solution(q_num, code, q_info)
            print(f"    Pasted into {filepath}")
    finally:
        # Reconnect to home WiFi
        print("\n>>> Reconnecting to home WiFi ...")
        switch_to_home()

    print("\nDone! Check your question files in questions/")


if __name__ == "__main__":
    main()
