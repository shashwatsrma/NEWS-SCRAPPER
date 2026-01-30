import os
import requests
import csv
import time
import re
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
OUTPUT_FILE = "republica/republica.csv"
START_LINE = 1   # ← change this to whatever line you want
END_LINE = 100  # ← change this to whatever line you want

# ---------------- HELPERS ----------------

def clean_text(text):
    return " ".join(text.split())

def remove_dateline(text):
    # Remove leading dateline like "KATHMANDU, Jan 12:" from Republica / OnlineKhabar
    return re.sub(r'^[A-Z\s]+,\s+[A-Za-z]+\s+\d{1,2}:\s*', '', text)

# ---------------- REPUBLICA ----------------

def extract_republica(url):
    soup = BeautifulSoup(
        requests.get(url, headers=HEADERS, timeout=15).text, "lxml"
    )

    # Category
    category_tag = soup.select_one("span.rep-body--small--sans.text-primary-blue")
    category = category_tag.text.strip() if category_tag else ""

    # Headline and subheading
    title_tag = soup.find("h1", class_="rep-headline--large")
    title = title_tag.text.strip() if title_tag else ""

    sub_title_tag = soup.find("div", class_="rep-body--large")
    sub_title = sub_title_tag.text.strip() if sub_title_tag else ""

    if sub_title:
        title = f"{title}: {sub_title}"  # combine title + subheading

    # Date
    time_tag = soup.find("time", id="pub-date")
    date = time_tag["datetime"] if time_tag and time_tag.has_attr("datetime") else ""

    # Content
    content_div = soup.find("div", id="content")
    paragraphs = []

    if content_div:
        for p in content_div.find_all("p"):
            txt = clean_text(p.get_text())
            if len(txt) > 40:
                txt = remove_dateline(txt)  # remove leading dateline
                paragraphs.append(txt)

    full_body = "\n\n".join(paragraphs)

    return {
        "CATEGORY": category,
        "TITLE": title,
        "BODY": full_body,
        "SOURCE": "Republica",
        "DATE": date,
    }

# ---------------- ROUTER ----------------

def extract_article(url):
    if "myrepublica.nagariknetwork.com" in url:
        return extract_republica(url)

# ---------------- BATCH RUN ----------------

def run_batch():
    with open("republica/republicaurls.txt") as f:
       urls = [
        u.strip()
        for idx, u in enumerate(f, start=1)
        if START_LINE <= idx <= END_LINE and u.strip()
    ]
    file_exists = os.path.isfile(OUTPUT_FILE)
    
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)

        if not file_exists:
            writer.writerow(
                ["ID", "CATEGORY", "LINK", "TITLE", "BODY", "SOURCE", "DATE"]
            )
        for i, url in enumerate(urls, start=START_LINE):
            try:
                data = extract_article(url)
                if not data:
                    continue

                writer.writerow([
                    i,
                    data["CATEGORY"],
                    url,
                    data["TITLE"],
                    data["BODY"],
                    data["SOURCE"],
                    data["DATE"]
                ])

                print(f"[OK] {i}: {url}")
                time.sleep(2)

            except Exception as e:
                print(f"[FAIL] {url} → {e}")
                time.sleep(5)

if __name__ == "__main__":
    run_batch()
