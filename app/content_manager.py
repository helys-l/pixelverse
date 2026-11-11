
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from app.gemini import generate_text
from app.deduplication import check_duplicate


ROOT = Path(__file__).resolve().parent.parent
SETTINGS_PATH = ROOT / "config" / "settings.json"
DATABASE_PATH = ROOT / "data" / "content_history.json"


SYSTEM_INSTRUCTION = """
Kamu adalah Content Manager PIXELVERSE.

Channel:
- Bahasa Indonesia.
- Niche: sains, alam, fenomena dunia.
- Gaya: menarik, edukatif, mudah dipahami.
- Format: YouTube Shorts maksimal 30 detik.

Aturan:
- Jangan mengarang fakta.
- Jangan membuat klaim sensasional tanpa dasar.
- Hindari topik yang terlalu umum atau berulang.
- Berikan ide yang berbeda satu sama lain.
- Kembalikan JSON valid saja, tanpa Markdown.
"""


def load_json(path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")

    with temporary.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

    temporary.replace(path)


def clean_json_response(response):
    response = response.strip()

    response = re.sub(
        r"^```(?:json)?\s*",
        "",
        response,
        flags=re.IGNORECASE
    )

    response = re.sub(r"\s*```$", "", response)

    return json.loads(response)


def generate_ideas(count=10):
    settings = load_json(SETTINGS_PATH)
    history = load_json(DATABASE_PATH)

    previous_topics = [
        {
            "title": item.get("title", ""),
            "topic": item.get("topic", ""),
            "angle": item.get("angle", "")
        }
        for item in history.get("contents", [])
    ]

    prompt = f"""
Buat tepat {count} ide video baru untuk channel PIXELVERSE.

Pilar konten:
- Sains.
- Alam.
- Fenomena dunia.
- Hewan dan makhluk hidup.
- Geografi dan luar angkasa.

Hindari kemiripan dengan riwayat berikut:
{json.dumps(previous_topics, ensure_ascii=False)}

Buat setiap ide memiliki:
- id: nomor urut.
- title: judul menarik.
- topic: fenomena utama yang dibahas.
- angle: sudut pembahasan yang spesifik.
- keywords: 3 sampai 6 kata kunci.
- hook: kalimat pembuka.
- explanation: ringkasan penjelasan ilmiah.
- score: nilai kualitas 0 sampai 100.
- fact_check_needed: selalu true.

Berikan output dengan format:
{{
  "ideas": [
    {{
      "id": 1,
      "title": "...",
      "topic": "...",
      "angle": "...",
      "keywords": ["...", "...", "..."],
      "hook": "...",
      "explanation": "...",
      "score": 80,
      "fact_check_needed": true
    }}
  ]
}}

Jangan mengulang topik atau sudut pembahasan dari riwayat.
Jangan mengklaim fakta sudah diverifikasi.
"""

    response = generate_text(
        prompt,
        system_instruction=SYSTEM_INSTRUCTION,
        max_output_tokens=5000
    )

    result = clean_json_response(response)
    ideas = result.get("ideas", [])

    if not isinstance(ideas, list):
        raise ValueError("Format ide dari AI tidak valid.")

    return ideas, settings


def select_best_idea(ideas, settings):
    minimum_score = settings["ai"]["minimum_idea_score"]
    threshold = settings["content"]["similarity_threshold"]

    valid_ideas = []

    for idea in ideas:
        required = [
            "title",
            "topic",
            "angle",
            "keywords",
            "hook",
            "explanation",
            "score"
        ]

        if not all(key in idea for key in required):
            continue

        if not isinstance(idea["score"], (int, float)):
            continue

        if idea["score"] < minimum_score:
            continue

        duplicate = check_duplicate(idea, threshold)

        if duplicate["is_duplicate"]:
            continue

        valid_ideas.append(idea)

    if not valid_ideas:
        return None

    return max(valid_ideas, key=lambda item: item["score"])


def save_selected_idea(idea):
    history = load_json(DATABASE_PATH)

    record = {
        **idea,
        "status": "selected",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "published_at": None
    }

    history.setdefault("contents", []).append(record)
    history["total_generated"] = (
        history.get("total_generated", 0) + 1
    )

    save_json(DATABASE_PATH, history)

    return record


def run_content_manager():
    ideas, settings = generate_ideas(
        settings_count(settings_path=SETTINGS_PATH)
    )

    selected = select_best_idea(ideas, settings)

    if selected is None:
        raise RuntimeError(
            "Tidak ditemukan ide yang lolos seleksi. "
            "Sistem tidak akan memaksakan ide."
        )

    return save_selected_idea(selected)


def settings_count(settings_path):
    settings = load_json(settings_path)
    return settings["ai"]["ideas_per_generation"]
