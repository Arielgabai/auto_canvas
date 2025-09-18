import os
import json
from fastapi import FastAPI
from pydantic import BaseModel

from .config import load_settings
from .gdrive import _service as gsvc


app = FastAPI(title="Auto Canvas Diagnostics")


class HealthResponse(BaseModel):
    status: str
    input_dir: str
    output_dir: str
    work_no_bg: str
    work_shadow: str
    state_file_exists: bool


@app.get("/health", response_model=HealthResponse)
def health():
    s = load_settings()
    return HealthResponse(
        status="ok",
        input_dir=s.input_dir,
        output_dir=s.output_pdf_dir,
        work_no_bg=s.work_no_bg_dir,
        work_shadow=s.work_shadow_dir,
        state_file_exists=os.path.exists(s.state_file),
    )


@app.get("/diagnose/env")
def diagnose_env():
    keys = [
        "PHOTOROOM_API_KEY",
        "WKHTMLTOPDF_PATH",
        "GDRIVE_SERVICE_ACCOUNT_JSON",
        "GDRIVE_INPUT_FOLDER_ID",
        "GDRIVE_OUTPUT_FOLDER_ID",
    ]
    data = {k: bool(os.getenv(k)) for k in keys}
    # Also check auto-detection presence
    data["/etc/secrets_exists"] = os.path.isdir("/etc/secrets")
    if data["/etc/secrets_exists"]:
        data["/etc/secrets_files"] = [f for f in os.listdir("/etc/secrets")]
    return data


@app.get("/diagnose/gdrive")
def diagnose_gdrive():
    try:
        svc = gsvc()
        about = svc.about().get(fields="user,storageQuota").execute()
        return {"ok": True, "user": about.get("user", {}), "storageQuota": about.get("storageQuota", {})}
    except Exception as e:
        return {"ok": False, "error": str(e)}


