import requests
import csv
import time
import re
from bs4 import BeautifulSoup
import os

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
OUTPUT_FILE = "TheKathmanduPost/tkp.csv"
START_LINE = 1
END_LINE = 10
INPUT_FILE = "TheKathmanduPost/tkpurls.txt"
# ---------------- HELPERS ----------------

def clean_text(text):
    return " ".join(text.split())

def extract_date(text):
    """
    Extract YYYY-MM-DD from text like:
    February 26, 2019
    """
    match = re.search(r'([A-Za-z]+)\s+(\d{1,2}),\s+(\d{4})', text)
    if not match:
        return ""

    month_map = {
        "January": "01", "February": "02", "March": "03",
        "April": "04", "May": "05", "June": "06",
        "July": "07", "August": "08", "September": "09",
        "October": "10", "November": "11", "December": "12"
    }

    month, day, year = match.groups()
    return f"{year}-{month_map.get(month, '01')}-{day.zfill(2)}"


# ---------------- KATHMANDU POST ----------------

def extract_kathmandupost(url):
    soup = BeautifulSoup(
        requests.get(url, headers=HEADERS, timeout=15).text, "lxml"
    )

    # Heading
    heading_tag = soup.select_one("div.col-sm-8 h1")
    heading = heading_tag.text.strip() if heading_tag else ""

    # Subheading
    sub_tag = soup.select_one("div.col-sm-8 span.title-sub")
    subheading = sub_tag.text.strip() if sub_tag else ""

    # Combine heading + subheading
    title = f"{heading}: {subheading}" if subheading else heading

    # Category
    cat_tag = soup.select_one("h4.title--line__red a")
    category = cat_tag.text.strip() if cat_tag else ""

    # Date (DATE ONLY)
    date = ""
    time_div = soup.find("div", class_="updated-time")
    if time_div:
        date = extract_date(time_div.text)

    # Body
    content = soup.find("section", class_="story-section")
    paragraphs = []
    if content:
        for p in content.find_all("p"):
            txt = clean_text(p.get_text())
            if len(txt) > 40:
                paragraphs.append(txt)

    return {
        "CATEGORY": category,
        "TITLE": title,
        "BODY": "\n\n".join(paragraphs),
        "SOURCE": "Kathmandu Post",
        "DATE": date,
    }


# ---------------- ROUTER ----------------

def extract_article(url):
    if "kathmandupost.com" in url:
        return extract_kathmandupost(url)
    return None


# ---------------- BATCH RUN ----------------

def run_batch():
    with open(INPUT_FILE) as f:
        urls = [
            u.strip()
            for idx, u in enumerate(f, start=1)
            if START_LINE <= idx <= END_LINE and u.strip()
        ]

    file_exists = os.path.isfile(OUTPUT_FILE)

    with open(OUTPUT_FILE, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)

        # ✅ write header ONLY if file does not exist
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
