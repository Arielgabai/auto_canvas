import os
from typing import List, Tuple
from PIL import Image, ImageFilter

from .config import load_settings
from .utils import file_basename_without_ext


def add_shadow_batch(
    input_paths: List[str],
    offset: Tuple[int, int] = (10, 10),
    blur_radius: int = 10,
) -> List[str]:
    settings = load_settings()
    os.makedirs(settings.work_shadow_dir, exist_ok=True)

    outputs: List[str] = []
    for inp in input_paths:
        name = file_basename_without_ext(inp)
        out_path = os.path.join(settings.work_shadow_dir, f"{name}.png")

        with Image.open(inp) as base_img:
            img = base_img.convert("RGBA")

            # Downscale to reduce memory footprint if very large
            max_side = 1600
            if max(img.width, img.height) > max_side:
                scale = max_side / float(max(img.width, img.height))
                new_size = (int(img.width * scale), int(img.height * scale))
                img = img.resize(new_size, Image.LANCZOS)

            alpha = img.split()[3]

            # Create shadow from alpha
            shadow = Image.new("RGBA", img.size, (0, 0, 0, 255))
            shadow.putalpha(alpha)
            shadow = shadow.resize((int(img.width * 1.01), int(img.height * 1.01)), Image.LANCZOS)
            shadow = shadow.filter(ImageFilter.GaussianBlur(float(blur_radius * 3)))

            # Compose
            new_size = (img.width + offset[0] * 4, img.height + offset[1] * 4)
            new_img = Image.new("RGBA", new_size, (0, 0, 0, 0))
            for _ in range(2):
                new_img.paste(shadow, (offset[0] * 2, offset[1] * 2), shadow)
            new_img.paste(img, (offset[0] * 2, offset[1] * 2), img)

            new_img.save(out_path, format="PNG")
            outputs.append(out_path)

    return outputs


