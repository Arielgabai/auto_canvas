import os
import time
from typing import List
import pdfkit
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

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

    # Try html->wkhtmltopdf first; fallback to reportlab if wkhtmltopdf not present
    ts = time.strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(output_pdf_dir, f"canvas_{ts}.pdf")
    try:
        _ = _wk_config()  # may raise if binary missing
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
                if len(row) < 3:
                    for _ in range(3 - len(row)):
                        html_parts.append("<td></td>")
                html_parts.append("</tr>")
            html_parts.append("</table></div>")
        html_parts.append("</body></html>")
        html = "".join(html_parts)
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
    except Exception:
        pass

    # Fallback ReportLab 3x3 grid
    page_w, page_h = A4
    margin = 10 * mm
    cols, rows = 3, 3
    cell_w = (page_w - 2 * margin) / cols
    cell_h = (page_h - 2 * margin) / rows
    max_img_w = 55 * mm
    max_img_h = 80 * mm

    c = canvas.Canvas(out_path, pagesize=A4)
    from PIL import Image

    for page_images in chunk(images, 9):
        for idx, img_path in enumerate(page_images):
            col = idx % cols
            row = idx // cols
            x = margin + col * cell_w
            # ReportLab origin bottom-left
            y = page_h - margin - (row + 1) * cell_h

            # Compute image size preserving ratio
            with Image.open(img_path) as im:
                iw, ih = im.size
            scale = min(max_img_w / iw, max_img_h / ih)
            draw_w = iw * scale
            draw_h = ih * scale
            # Center in cell
            dx = x + (cell_w - draw_w) / 2
            dy = y + (cell_h - draw_h) / 2
            c.drawImage(img_path, dx, dy, width=draw_w, height=draw_h, preserveAspectRatio=True, mask='auto')
        c.showPage()
    c.save()
    return out_path


