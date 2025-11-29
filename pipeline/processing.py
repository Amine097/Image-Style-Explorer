# pipeline/processing.py

import io
from typing import Tuple

import streamlit as st
from PIL import Image

from styles import apply_filter, FilterName, painting


def resize_for_processing(image: Image.Image, max_dim: int = 800) -> Image.Image:
    """Resize image so that the longest side is max_dim (for speed)."""
    w, h = image.size
    longest = max(w, h)
    if longest <= max_dim:
        return image

    scale = max_dim / float(longest)
    new_w = int(w * scale)
    new_h = int(h * scale)
    return image.resize((new_w, new_h), Image.BILINEAR)


@st.cache_data(ttl=3600)
def process_image(
    image_bytes: bytes,
    filter_label: str,
    blur_strength: int,
    painting_detail: int,
    painting_color_smooth: float,
    max_dim: int,
) -> Tuple[Image.Image, Image.Image]:
    """
    Cached image processing:
    - rebuild PIL image from bytes
    - resize
    - apply chosen style
    Returns (original_resized, styled_resized).
    """
    img = Image.open(io.BytesIO(image_bytes))
    img = resize_for_processing(img, max_dim=max_dim)

    label_to_name: dict[str, FilterName] = {
        "None": "none",
        "Black & White": "bw",
        "Sketch": "sketch",
        "Cartoon": "cartoon",
        "Blur": "blur",
    }

    if filter_label == "Painting":
        styled = painting(
            img,
            sigma_s=painting_detail,
            sigma_r=painting_color_smooth,
        )
    else:
        filter_name = label_to_name[filter_label]
        styled = apply_filter(
            img,
            filter_name,
            blur_ksize=blur_strength,
        )

    return img, styled
