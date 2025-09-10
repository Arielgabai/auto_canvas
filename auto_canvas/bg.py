import os
import requests
from typing import List

from .config import load_settings
from .utils import file_basename_without_ext


PHOTOROOM_URL = "https://sdk.photoroom.com/v1/segment"


def remove_background_batch(input_paths: List[str]) -> List[str]:
    """Remove background for each input image using PhotoRoom API.

    Returns list of output file paths (PNG to preserve transparency).
    """
    settings = load_settings()
    if not settings.photoroom_api_key:
        raise RuntimeError("PHOTOROOM_API_KEY not configured")

    outputs: List[str] = []
    os.makedirs(settings.work_no_bg_dir, exist_ok=True)

    headers = {"x-api-key": settings.photoroom_api_key}

    for idx, path in enumerate(input_paths):
        name = file_basename_without_ext(path)
        out_path = os.path.join(settings.work_no_bg_dir, f"{name}.png")
        attempt = 0
        while True:
            attempt += 1
            try:
                with open(path, "rb") as f:
                    files = {"image_file": f}
                    data = {"format": "png"}
                    resp = requests.post(
                        PHOTOROOM_URL,
                        headers=headers,
                        files=files,
                        data=data,
                        timeout=60,
                    )
                if resp.status_code == requests.codes.ok:
                    with open(out_path, "wb") as out:
                        out.write(resp.content)
                    outputs.append(out_path)
                    break
                elif resp.status_code in (402, 429):
                    # Quota/rate limit reached - surface immediately without delaying
                    raise RuntimeError(
                        f"PhotoRoom error {resp.status_code}: {resp.text[:200]}"
                    )
                else:
                    raise RuntimeError(
                        f"PhotoRoom error {resp.status_code}: {resp.text[:200]}"
                    )
            except requests.RequestException as e:
                if attempt >= settings.photoroom_retry_max:
                    raise
                # Small backoff only for transient network errors
                import time as _t
                _t.sleep(settings.photoroom_retry_backoff_seconds)

    return outputs


