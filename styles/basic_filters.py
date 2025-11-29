# styles/basic_filters.py

from typing import Literal
from PIL import Image
import numpy as np
import cv2


# -------------------------------
# Internal helpers (PIL <-> OpenCV)
# -------------------------------

def _pil_to_cv2(pil_img: Image.Image) -> np.ndarray:
    """Convert a PIL RGB image to an OpenCV BGR image."""
    rgb = np.array(pil_img.convert("RGB"))
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    return bgr


def _cv2_to_pil(bgr_img: np.ndarray) -> Image.Image:
    """Convert an OpenCV BGR image to a PIL RGB image."""
    rgb = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb)


# -------------------------------
# Public filters (V1)
# All functions take & return PIL.Image.Image
# -------------------------------

def identity(image: Image.Image) -> Image.Image:
    """Return the original image (no filter)."""
    return image.copy()


def black_and_white(image: Image.Image) -> Image.Image:
    """Black & white + contrast (histogram equalization)."""
    bgr = _pil_to_cv2(image)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    gray_eq = cv2.equalizeHist(gray)
    bw_bgr = cv2.cvtColor(gray_eq, cv2.COLOR_GRAY2BGR)
    return _cv2_to_pil(bw_bgr)


def sketch(image: Image.Image) -> Image.Image:
    """
    Simple sketch effect:
    - convert to gray
    - blur
    - edge detection
    - invert edges
    """
    bgr = _pil_to_cv2(image)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    gray_blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(gray_blur, 50, 150)
    edges_inv = cv2.bitwise_not(edges)
    sketch_bgr = cv2.cvtColor(edges_inv, cv2.COLOR_GRAY2BGR)
    return _cv2_to_pil(sketch_bgr)


def cartoon(image: Image.Image) -> Image.Image:
    """
    Cartoon effect:
    - bilateral filter (smooth colors)
    - edge detection
    - combine edges + smooth image
    """
    bgr = _pil_to_cv2(image)

    # color smoothing
    color = cv2.bilateralFilter(bgr, d=9, sigmaColor=75, sigmaSpace=75)

    # edge detection
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    gray_blur = cv2.medianBlur(gray, 7)
    edges = cv2.adaptiveThreshold(
        gray_blur,
        255,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY,
        blockSize=9,
        C=2,
    )
    edges_bgr = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

    cartoon_bgr = cv2.bitwise_and(color, edges_bgr)
    return _cv2_to_pil(cartoon_bgr)


def artistic_blur(image: Image.Image, ksize: int = 9) -> Image.Image:
    """
    Artistic blur using Gaussian blur.
    ksize must be an odd integer.
    """
    if ksize % 2 == 0:
        ksize += 1
    bgr = _pil_to_cv2(image)
    blurred = cv2.GaussianBlur(bgr, (ksize, ksize), 0)
    return _cv2_to_pil(blurred)


# -------------------------------
# Helper: dispatch by name
# -------------------------------

FilterName = Literal[
    "none",
    "bw",
    "sketch",
    "cartoon",
    "blur",
]


def apply_filter(
    image: Image.Image,
    name: FilterName,
    *,
    blur_ksize: int = 9,
) -> Image.Image:
    """
    Central dispatcher used by the UI.
    Keeps app.py clean by concentrating logic here.
    """
    if name == "none":
        return identity(image)
    if name == "bw":
        return black_and_white(image)
    if name == "sketch":
        return sketch(image)
    if name == "cartoon":
        return cartoon(image)
    if name == "blur":
        return artistic_blur(image, ksize=blur_ksize)

    # fallback: no filter
    return identity(image)
