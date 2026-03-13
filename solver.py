import os
import smtplib
from email.mime.text import MIMEText
from openai import OpenAI

# ---------------------------------------------------------------------
# CODING CONVENTIONS (injected into every prompt)
# ---------------------------------------------------------------------

CODING_CONVENTIONS = (
    "CODING RULES (follow ALL):\n"
    "- camelCase or snake_case names. Constants: #define ALL_CAPS.\n"
    "- NO globals, NO statics, NO code duplication, NO calloc (malloc only).\n"
    "- English only. Brief function doc comments.\n"
    "- Braces on EVERY if/else/while/for/switch. Opening { on same line.\n"
    "- Spaces around operators. One statement per line. Max 80 chars/line.\n"
    "- Max 16 counted lines per function (blank/comment/brace-only lines excluded).\n"
    "- Only allowed libs: stdio.h, stdlib.h, stdbool.h (unless question says otherwise).\n"
)

# ---------------------------------------------------------------------
# PROMPT TEMPLATES per question type
# ---------------------------------------------------------------------

PROMPTS = {
    "q1_analysis": (
        "Analyze time and space complexity of the C functions below.\n\n"
        "Functions may be grouped, separated by '//time and space'.\n"
        "For each group, provide ONE line: // Time: O(...)  |  Space: O(...)\n\n"
        "Assumptions: all library functions (strlen, strcmp, printf, free) are O(1) "
        "time and O(1) space. malloc(n) is O(1) time, O(n) space.\n\n"
        "Do NOT modify the code. Only provide complexity comments.\n"
        "Output ONLY the commented version of the code between the markers."
    ),
    "q2_solve": (
        "Solve the C exam question below.\n\n"
        "The code has a comment describing the question with function signature(s), "
        "constraints, and examples.\n\n"
        "Write the complete solution. Do NOT change the given function signature(s). "
        "Respect time/space constraints. You may add helper functions.\n"
        "Output ONLY the solution code between the markers."
    ),
    "q3_solve": (
        "Solve the C exam question below.\n\n"
        "The code has a comment describing the question with function signature(s), "
        "constraints, and examples.\n\n"
        "Write the complete solution. Do NOT change the given function signature(s). "
        "Respect time/space constraints. You may add helper functions.\n"
        "Output ONLY the solution code between the markers."
    ),
    "q4_backtracking": (
        "Solve the BACKTRACKING C exam question below.\n\n"
        "The code has a comment describing the question with function signature, "
        "constraints, and examples.\n\n"
        "APPROACH: Do NOT change the given function signature. Create an auxiliary helper "
        "function for the backtracking recursion. The given function calls the helper.\n\n"
        "Write the complete solution. Respect time/space constraints. "
        "You may add helper functions.\n"
        "Output ONLY the solution code between the markers."
    ),
}

# Map question type to question number for email subject
QUESTION_NUMBERS = {
    "q1_analysis": "Q1",
    "q2_solve": "Q2",
    "q3_solve": "Q3",
    "q4_backtracking": "Q4",
}


def solve(problem: str, question_type: str, api_key: str) -> str:
    prompt_template = PROMPTS.get(question_type, PROMPTS["q2_solve"])

    system_prompt = (
        "You are an expert C programmer solving a Technion CS exam.\n\n"
        + CODING_CONVENTIONS + "\n\n"
        + prompt_template + "\n\n"
        "IMPORTANT: Wrap your final answer code EXACTLY like this:\n"
        "===SOLUTION_START===\n"
        "<your code here>\n"
        "===SOLUTION_END===\n\n"
        "The markers must be on their own lines. Put ALL your code between them."
    )

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="o3",
        messages=[
            {"role": "developer", "content": system_prompt},
            {"role": "user", "content": problem},
        ],
    )
    return response.choices[0].message.content


def send_email(subject: str, body: str, gmail_user: str, gmail_pass: str):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = gmail_user
    msg["To"] = gmail_user

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_user, gmail_pass)
        server.sendmail(gmail_user, gmail_user, msg.as_string())


def main():
    problem = os.environ["PROBLEM"]
    question_type = os.environ.get("QUESTION_TYPE", "q2_solve")
    api_key = os.environ["OPENAI_API_KEY"]
    gmail_user = os.environ["GMAIL_USER"]
    gmail_pass = os.environ["GMAIL_PASS"]

    q_num = QUESTION_NUMBERS.get(question_type, "Q?")
    print(f"Solving {q_num} ({question_type}) with o3...")

    solution = solve(problem, question_type, api_key)
    print(solution)

    subject = f"GPT Solution: {q_num}"
    print(f"Sending email with subject: {subject}")
    send_email(
        subject=subject,
        body=solution,
        gmail_user=gmail_user,
        gmail_pass=gmail_pass,
    )
    print("Email sent!")


if __name__ == "__main__":
    main()
