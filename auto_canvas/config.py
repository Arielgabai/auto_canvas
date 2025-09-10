import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class Settings:
    photoroom_api_key: str
    wkhtmltopdf_path: str
    input_dir: str
    output_pdf_dir: str
    work_no_bg_dir: str
    work_shadow_dir: str
    state_file: str
    batch_size: int = 9
    poll_interval_seconds: int = 5
    stability_seconds: int = 3
    photoroom_requests_per_min: int = 6
    photoroom_retry_max: int = 3
    photoroom_retry_backoff_seconds: int = 5
    batch_cooldown_seconds: int = 10
    rate_limit_sleep_seconds: int = 65


def load_settings() -> Settings:
    load_dotenv()

    root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

    def _default_path(*parts: str) -> str:
        return os.path.join(root, *parts)

    settings = Settings(
        photoroom_api_key=os.getenv("PHOTOROOM_API_KEY", ""),
        wkhtmltopdf_path=os.getenv(
            "WKHTMLTOPDF_PATH",
            r"C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe",
        ),
        input_dir=os.getenv("INPUT_DIR", _default_path("drive_in")),
        output_pdf_dir=os.getenv("OUTPUT_PDF_DIR", _default_path("drive_out")),
        work_no_bg_dir=os.getenv("WORK_NO_BG_DIR", _default_path("work", "no_bg")),
        work_shadow_dir=os.getenv(
            "WORK_SHADOW_DIR", _default_path("work", "shadow")
        ),
        state_file=os.getenv("STATE_FILE", _default_path(".state.json")),
        photoroom_requests_per_min=int(os.getenv("PHOTOROOM_RPM", "6")),
        photoroom_retry_max=int(os.getenv("PHOTOROOM_RETRY_MAX", "3")),
        photoroom_retry_backoff_seconds=int(os.getenv("PHOTOROOM_RETRY_BACKOFF", "5")),
        batch_cooldown_seconds=int(os.getenv("BATCH_COOLDOWN_SECONDS", "10")),
        rate_limit_sleep_seconds=int(os.getenv("RATE_LIMIT_SLEEP_SECONDS", "65")),
    )

    # Ensure folders exist
    for path in [
        settings.input_dir,
        settings.output_pdf_dir,
        settings.work_no_bg_dir,
        settings.work_shadow_dir,
    ]:
        os.makedirs(path, exist_ok=True)

    return settings


