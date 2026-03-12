import os
import smtplib
from email.mime.text import MIMEText
from openai import OpenAI


def solve(problem: str, api_key: str) -> str:
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert competitive programmer. "
                    "Given a coding problem, provide:\n"
                    "1. Approach / intuition\n"
                    "2. Clean, commented Python solution\n"
                    "3. Time and space complexity analysis"
                ),
            },
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
    api_key = os.environ["OPENAI_API_KEY"]
    gmail_user = os.environ["GMAIL_USER"]
    gmail_pass = os.environ["GMAIL_PASS"]

    print("Solving problem with GPT-4o...")
    solution = solve(problem, api_key)
    print(solution)

    print("Sending email...")
    send_email(
        subject="GPT-4o solved your LeetCode problem",
        body=solution,
        gmail_user=gmail_user,
        gmail_pass=gmail_pass,
    )
    print("Email sent!")


if __name__ == "__main__":
    main()
