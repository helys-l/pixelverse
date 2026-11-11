
import json
import os
import urllib.error
import urllib.request


API_URL = "https://generativelanguage.googleapis.com/v1beta/interactions"
DEFAULT_MODEL = "gemini-3.8-flash"


class GeminiError(Exception):
    """Kesalahan komunikasi dengan Gemini API."""


def generate_text(
    prompt,
    system_instruction=None,
    max_output_tokens=2048
):
    """
    Mengirim prompt ke Gemini Interactions API
    dan mengembalikan teks hasil generasi.
    """

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise GeminiError(
            "GEMINI_API_KEY belum dikonfigurasi."
        )

    model = os.getenv("GEMINI_MODEL", DEFAULT_MODEL)

    payload = {
        "model": model,
        "input": prompt,
        "generation_config": {
            "max_output_tokens": max_output_tokens
        }
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
        with urllib.request.urlopen(
            request,
            timeout=90
        ) as response:
            result = json.loads(
                response.read().decode("utf-8")
            )

    except urllib.error.HTTPError as error:
        detail = error.read().decode(
            "utf-8",
            errors="replace"
        )

        raise GeminiError(
            f"Gemini API HTTP {error.code}: {detail[:1000]}"
        ) from error

    except urllib.error.URLError as error:
        raise GeminiError(
            f"Koneksi Gemini gagal: {error.reason}"
        ) from error

    except TimeoutError as error:
        raise GeminiError(
            "Permintaan Gemini melewati batas waktu."
        ) from error

    output = result.get("output_text")

    if not output or not output.strip():
        raise GeminiError(
            "Gemini tidak memberikan output teks."
        )

    return output.strip()
