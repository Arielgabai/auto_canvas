import os
import time
from typing import List
import pdfkit

from .config import load_settings
from .utils import chunk


CSS = """
@page { size: A4; }
body { background: #ffffff; }
table { width: 100%; border-collapse: collapse; page-break-inside: avoid; }
td { width: 33.33%; padding: 2mm; height: 85mm; box-sizing: border-box; vertical-align: middle; text-align: center; }
img { max-width: 55mm; max-height: 80mm; width: auto; height: auto; display: inline-block; }
.page { page-break-after: always; }
.page:last-child { page-break-after: auto; }
"""


def _wk_config():
    settings = load_settings()
    return pdfkit.configuration(wkhtmltopdf=settings.wkhtmltopdf_path)


def _to_file_uri(path: str) -> str:
    abs_path = os.path.abspath(path)
    return "file:///" + abs_path.replace("\\", "/")


def images_to_pdf_3x3(images: List[str], output_pdf_dir: str | None = None) -> str:
    settings = load_settings()
    if output_pdf_dir is None:
        output_pdf_dir = settings.output_pdf_dir
    os.makedirs(output_pdf_dir, exist_ok=True)

    # Build HTML with 9 images per page
    html_parts: List[str] = [
        "<html><head><meta charset='utf-8'><style>",
        CSS,
        "</style></head><body>",
    ]

    for page_images in chunk(images, 9):
        html_parts.append("<div class='page'><table>")
        for row_start in range(0, len(page_images), 3):
            row = page_images[row_start : row_start + 3]
            html_parts.append("<tr>")
            for img_path in row:
                html_parts.append(f"<td><img src='{_to_file_uri(img_path)}'></td>")
            # Fill empty cells if last row has < 3 images
            if len(row) < 3:
                for _ in range(3 - len(row)):
                    html_parts.append("<td></td>")
            html_parts.append("</tr>")
        html_parts.append("</table></div>")

    html_parts.append("</body></html>")
    html = "".join(html_parts)

    ts = time.strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(output_pdf_dir, f"canvas_{ts}.pdf")

    options = {
        "enable-local-file-access": None,
        "page-size": "A4",
        "margin-top": "10mm",
        "margin-right": "10mm",
        "margin-bottom": "10mm",
        "margin-left": "10mm",
    }
    pdfkit.from_string(html, out_path, configuration=_wk_config(), options=options)
    return out_path


