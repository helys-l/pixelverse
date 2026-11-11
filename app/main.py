
import json
import sys
from datetime import datetime, timezone

from app.content_manager import run_content_manager


def main():
    print("=" * 50)
    print("PIXELVERSE CONTENT MANAGER")
    print("=" * 50)

    print(
        "Waktu mulai:",
        datetime.now(timezone.utc).isoformat()
    )

    try:
        result = run_content_manager()

        print("\nIDE BERHASIL DIPILIH")
        print(json.dumps(
            result,
            ensure_ascii=False,
            indent=2
        ))

        print("\nStatus: berhasil")
        return 0

    except Exception as error:
        print("\nSISTEM GAGAL")
        print(f"Alasan: {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
