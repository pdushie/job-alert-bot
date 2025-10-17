
from flask import Flask
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

URL = os.getenv("JOB_URL")
STORAGE_FILE = "seen_jobs.json"

GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASS = os.getenv("GMAIL_PASS")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")

def fetch_jobs():
    response = requests.get(URL)
    soup = BeautifulSoup(response.text, "html.parser")
    jobs = []
    for job_card in soup.select(".jobTitle a"):
        title = job_card.text.strip()
        href = job_card.get("href")
        if href:
            link = "https://jobs.novascotia.ca" + href
        else:
            continue
        jobs.append({"title": title, "link": link})
    return jobs

def load_seen_jobs():
    if os.path.exists(STORAGE_FILE):
        with open(STORAGE_FILE, "r") as f:
            return json.load(f)
    return []

def save_jobs(jobs):
    with open(STORAGE_FILE, "w") as f:
        json.dump(jobs, f)

def send_email(new_jobs):
    if not GMAIL_USER or not GMAIL_PASS or not RECIPIENT_EMAIL:
        print("Email credentials not configured properly")
        return

    msg = MIMEMultipart()
    msg['From'] = GMAIL_USER
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = "New CSDS Job Postings"

    body = "Here are the new job postings:\n\n"
    for job in new_jobs:
        body += f"{job['title']}\n{job['link']}\n\n"

    msg.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(GMAIL_USER, GMAIL_PASS)
        server.send_message(msg)

@app.route("/")
def check_jobs():
    current_jobs = fetch_jobs()
    seen_jobs = load_seen_jobs()

    # Compare by job link to avoid duplicates
    seen_links = {job['link'] for job in seen_jobs}
    new_jobs = [job for job in current_jobs if job['link'] not in seen_links]

    if new_jobs:
        send_email(new_jobs)
        save_jobs(current_jobs)
        return f"Sent email with {len(new_jobs)} new jobs."
    else:
        return "No new jobs found."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
