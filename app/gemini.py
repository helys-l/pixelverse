
import json
import os
import time
import random
import urllib.error
import urllib.request


API_URL = "https://generativelanguage.googleapis.com/v1beta/interactions"
DEFAULT_MODEL = "gemini-3.8-flash"

MAX_RETRIES = 4
RETRYABLE_STATUS = {408, 429, 500, 502, 503, 504}


class GeminiError(Exception):
    pass


def extract_text(result):
    direct_text = result.get("output_text")

    if isinstance(direct_text, str) and direct_text.strip():
        return direct_text.strip()

    collected = []

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

    request_data = json.dumps(payload).encode("utf-8")

    for attempt in range(MAX_RETRIES):
        request = urllib.request.Request(
            API_URL,
            data=request_data,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": api_key
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=90
            ) as response:
                result = json.loads(
                    response.read().decode("utf-8")
                )

            text = extract_text(result)

            if not text:
                raise GeminiError(
                    "Gemini tidak memberikan output teks."
                )

            return text

        except urllib.error.HTTPError as error:
            detail = error.read().decode(
                "utf-8",
                errors="replace"
            )

            if error.code not in RETRYABLE_STATUS:
                raise GeminiError(
                    f"Gemini API HTTP {error.code}: {detail[:1000]}"
                ) from error

            if attempt == MAX_RETRIES - 1:
                raise GeminiError(
                    f"Gemini gagal setelah {MAX_RETRIES} percobaan. "
                    f"HTTP {error.code}: {detail[:1000]}"
                ) from error

            retry_after = error.headers.get("Retry-After")

            try:
                wait_time = float(retry_after)
            except (TypeError, ValueError):
                wait_time = 2 ** (attempt + 1) + random.uniform(0, 1)

            wait_time = min(wait_time, 60)

            print(
                f"Gemini HTTP {error.code}. "
                f"Percobaan ulang {attempt + 1}/{MAX_RETRIES} "
                f"dalam {wait_time:.1f} detik..."
            )

            time.sleep(wait_time)

        except (urllib.error.URLError, TimeoutError) as error:
            if attempt == MAX_RETRIES - 1:
                raise GeminiError(
                    f"Koneksi Gemini gagal setelah "
                    f"{MAX_RETRIES} percobaan: {error}"
                ) from error

            wait_time = 2 ** (attempt + 1) + random.uniform(0, 1)

            print(
                f"Koneksi bermasalah. "
                f"Mencoba kembali dalam {wait_time:.1f} detik..."
            )

            time.sleep(wait_time)

    raise GeminiError("Gemini gagal memberikan respons.")
