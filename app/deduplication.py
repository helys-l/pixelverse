
import re
import json
import unicodedata
from pathlib import Path
from difflib import SequenceMatcher

DATABASE_PATH = Path("data/content_history.json")


def normalize(text):
    """Membersihkan teks agar mudah dibandingkan."""
    text = unicodedata.normalize("NFKD", text.lower())
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return " ".join(text.split())


def similarity(text_a, text_b):
    """Menghitung kemiripan dua teks."""
    a = normalize(text_a)
    b = normalize(text_b)

    if not a or not b:
        return 0.0

    return SequenceMatcher(None, a, b).ratio()


def load_history():
    if not DATABASE_PATH.exists():
        return {"contents": []}

    with DATABASE_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def check_duplicate(candidate, threshold=0.80):
    """
    Memeriksa kandidat terhadap seluruh riwayat.
    Kandidat berisi title, topic, angle, dan keywords.
    """
    history = load_history()

    candidate_text = " ".join([
        candidate.get("title", ""),
        candidate.get("topic", ""),
        candidate.get("angle", ""),
        " ".join(candidate.get("keywords", []))
    ])

    matches = []

    for content in history.get("contents", []):
        previous_text = " ".join([
            content.get("title", ""),
            content.get("topic", ""),
            content.get("angle", ""),
            " ".join(content.get("keywords", []))
        ])

        score = similarity(candidate_text, previous_text)

        if score >= threshold:
            matches.append({
                "title": content.get("title", ""),
                "similarity": round(score, 3)
            })

    return {
        "is_duplicate": len(matches) > 0,
        "matches": matches
    }
