import os
from .config import load_settings
from .utils import list_image_files
from .pdfgen import images_to_pdf_3x3


def main() -> None:
    settings = load_settings()
    shadow_dir = settings.work_shadow_dir
    images = [
        os.path.join(shadow_dir, f)
        for f in os.listdir(shadow_dir)
        if os.path.isfile(os.path.join(shadow_dir, f))
    ]
    if not images:
        print(f"No images found in {shadow_dir}")
        return
    out = images_to_pdf_3x3(images)
    print(f"Generated PDF: {out}")


if __name__ == "__main__":
    main()


