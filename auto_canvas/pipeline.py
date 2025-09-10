from __future__ import annotations

import argparse
import os
from typing import List

from .config import load_settings
from .utils import load_state, save_state, file_signature
from .bg import remove_background_batch
from .shadow import add_shadow_batch
from .pdfgen import images_to_pdf_3x3


def process_batch(input_images: List[str]) -> str:
    """Process a batch of images end-to-end and return output PDF path."""
    settings = load_settings()

    # Track processing in state to avoid duplicates on restart
    state = load_state(settings.state_file)
    processing_set = set(state.get("processing", []))
    processed_set = set(state.get("processed", []))

    # Mark as processing
    for p in input_images:
        if p not in processing_set and p not in processed_set:
            processing_set.add(p)
    state["processing"] = sorted(processing_set)
    save_state(settings.state_file, state)

    # Steps
    no_bg = remove_background_batch(input_images)
    with_shadow = add_shadow_batch(no_bg)
    pdf_path = images_to_pdf_3x3(with_shadow)

    # Mark processed
    for p in input_images:
        processed_set.add(p)
        processing_set.discard(p)
        sig = file_signature(p)
        state.setdefault("processed_signatures", {})[p] = sig
    state["processing"] = sorted(processing_set)
    state["processed"] = sorted(processed_set)
    save_state(settings.state_file, state)

    return pdf_path


def main_once() -> None:
    settings = load_settings()
    # Example manual run: take first 9 images from input
    files = [
        os.path.join(settings.input_dir, f)
        for f in os.listdir(settings.input_dir)
        if os.path.isfile(os.path.join(settings.input_dir, f))
    ]
    files = files[: settings.batch_size]
    if not files:
        print("No images to process.")
        return
    out = process_batch(files)
    print(f"Generated PDF: {out}")

def main() -> None:
    parser = argparse.ArgumentParser(description="Process images into 3x3 PDF")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Process a single batch from INPUT_DIR (default behavior)",
    )
    parser.add_argument(
        "--paths",
        nargs="+",
        help="Explicit image paths to process (up to batch size)",
    )
    args = parser.parse_args()

    if args.paths:
        settings = load_settings()
        files = args.paths[: settings.batch_size]
        out = process_batch(files)
        print(f"Generated PDF: {out}")
    else:
        main_once()


if __name__ == "__main__":
    main()


