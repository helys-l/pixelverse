
import json
import os
import urllib.error
import urllib.request


API_URL = "https://generativelanguage.googleapis.com/v1beta/interactions"
DEFAULT_MODEL = "gemini-3.8-flash"


class GeminiError(Exception):
    pass


def extract_text(result):
    """Mengambil teks dari respons REST Interactions API."""

    # Beberapa format respons menyediakan output_text langsung.
    direct_text = result.get("output_text")
    if isinstance(direct_text, str) and direct_text.strip():
        return direct_text.strip()

    collected = []

    # REST API mengembalikan langkah-langkah output.
    for step in result.get("output", []):
        if step.get("type") != "model_output":
            continue

        for item in step.get("content", []):
            if item.get("type") == "text":
                value = item.get("text", "")
                if value:
                    collected.append(value)

    return "\n".join(collected).strip()


def generate_text(
    prompt,
    system_instruction=None,
    max_output_tokens=2048
):
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise GeminiError("GEMINI_API_KEY belum dikonfigurasi.")

    model = os.getenv("GEMINI_MODEL") or DEFAULT_MODEL

    payload = {
        "model": model,
        "input": prompt,
        "generation_config": {
            "max_output_tokens": max_output_tokens,
            "thinking_level": "low"
        },
        "store": False
    }

    if system_instruction:
        payload["system_instruction"] = system_instruction

    request = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            result = json.loads(response.read().decode("utf-8"))

    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise GeminiError(
            f"Gemini API HTTP {error.code}: {detail[:1000]}"
        ) from error

    except (urllib.error.URLError, TimeoutError) as error:
        raise GeminiError(f"Koneksi Gemini gagal: {error}") from error

    text = extract_text(result)

    if not text:
        raise GeminiError(
            "Respons Gemini tidak berisi teks yang dapat dibaca."
        )

    return text
