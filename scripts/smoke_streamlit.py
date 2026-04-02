from __future__ import annotations

import sys
import time
import urllib.error
import urllib.request


def main() -> None:
    url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8501"
    deadline = time.time() + 45
    last_error: Exception | None = None

    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                body = response.read().decode("utf-8")
                content_type = response.headers.get("Content-Type", "")

            if "text/html" in content_type and "<title>" in body:
                print("Streamlit smoke check passed.")
                return
            last_error = RuntimeError(f"unexpected response shape: content_type={content_type!r}")
        except (urllib.error.URLError, TimeoutError, RuntimeError) as exc:
            last_error = exc
            time.sleep(2)

    raise SystemExit(f"Streamlit smoke failed: {last_error}")


if __name__ == "__main__":
    main()
