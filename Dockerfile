FROM python:3.12-slim

# Install wkhtmltopdf deps and wkhtmltopdf
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    xz-utils wget gnupg ca-certificates \
    libjpeg62-turbo libxrender1 libxext6 libfontconfig1 libfreetype6 \
    libx11-6 libxcb1 libxau6 libxdmcp6 \
 && rm -rf /var/lib/apt/lists/*

# wkhtmltopdf static build
RUN wget -O /tmp/wkhtml.deb https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox_0.12.6-1.bookworm_amd64.deb \
 && apt-get update \
 && apt-get install -y --no-install-recommends /tmp/wkhtml.deb \
 && rm -rf /var/lib/apt/lists/* /tmp/wkhtml.deb

ENV WKHTMLTOPDF_PATH=/usr/local/bin/wkhtmltopdf

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
   python -m auto_canvas.watch_gdrive; \
 else \
   python -m auto_canvas.watch; \
 fi "]


