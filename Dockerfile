FROM python:3.12-slim

# Minimal system deps for reportlab and networking
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    fonts-dejavu fontconfig ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# wkhtmltopdf optional; fallback to ReportLab if missing
ENV WKHTMLTOPDF_PATH=/usr/bin/wkhtmltopdf \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Default to local folder watcher
ENV INPUT_DIR=/app/drive_in \
    OUTPUT_PDF_DIR=/app/drive_out \
    WORK_NO_BG_DIR=/app/work/no_bg \
    WORK_SHADOW_DIR=/app/work/shadow \
    STATE_FILE=/app/.state.json

RUN mkdir -p "$INPUT_DIR" "$OUTPUT_PDF_DIR" "$WORK_NO_BG_DIR" "$WORK_SHADOW_DIR"

# Render uses PORT; not needed here but harmless
ENV PORT=8000

# Start the Drive watcher if GDRIVE_INPUT_FOLDER_ID is set, else local watcher
CMD ["/bin/bash", "-lc", "\
 if [ -n \"$GDRIVE_INPUT_FOLDER_ID\" ]; then \
   python -u -m auto_canvas.watch_gdrive; \
 else \
   python -u -m auto_canvas.watch; \
 fi "]


