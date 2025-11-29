# styles/basic_filters.py

from typing import Literal, Tuple

import cv2
import numpy as np
from PIL import Image

FilterName = Literal[
    "none",
    "bw",
    "sketch",
    "cartoon",
    "blur",
    "auto_enhance",
    "vivid",
    "vintage",
]


def pil_to_cv(img: Image.Image) -> np.ndarray:
    """Convert PIL Image (RGB) to OpenCV BGR array."""
    arr = np.array(img)
    if arr.ndim == 2:
        return arr
    return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)


def cv_to_pil(arr: np.ndarray) -> Image.Image:
    """Convert OpenCV BGR/RGB array to PIL Image (RGB)."""
    if arr.ndim == 2:
        rgb = cv2.cvtColor(arr, cv2.COLOR_GRAY2RGB)
    else:
        rgb = cv2.cvtColor(arr, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb)


# ---------- Base filters (what you probably already had) ----------

def bw_filter(img: Image.Image) -> Image.Image:
    cv = pil_to_cv(img)
    gray = cv2.cvtColor(cv, cv2.COLOR_BGR2GRAY)
    return cv_to_pil(gray)


def sketch_filter(img: Image.Image) -> Image.Image:
    cv = pil_to_cv(img)
    gray = cv2.cvtColor(cv, cv2.COLOR_BGR2GRAY)
    gray_blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(gray_blur, 50, 150)
    inv = cv2.bitwise_not(edges)
    return cv_to_pil(inv)


def cartoon_filter(img: Image.Image) -> Image.Image:
    cv = pil_to_cv(img)
    gray = cv2.cvtColor(cv, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 7)
    edges = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 9
    )
    color = cv2.bilateralFilter(cv, d=9, sigmaColor=150, sigmaSpace=150)
    cartoon = cv2.bitwise_and(color, color, mask=edges)
    return cv_to_pil(cartoon)


def blur_filter(img: Image.Image, ksize: int = 9) -> Image.Image:
    cv = pil_to_cv(img)
    if ksize % 2 == 0:
        ksize += 1
    blurred = cv2.GaussianBlur(cv, (ksize, ksize), 0)
    return cv_to_pil(blurred)


# ---------- New “AI-ish” filters ----------

def auto_enhance_filter(img: Image.Image) -> Image.Image:
    """
    Auto enhance:
    - CLAHE on luminance
    - Slight sharpening
    """
    cv = pil_to_cv(img)
    lab = cv2.cvtColor(cv, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    l_clahe = clahe.apply(l)

    lab_clahe = cv2.merge((l_clahe, a, b))
    enhanced = cv2.cvtColor(lab_clahe, cv2.COLOR_LAB2BGR)

    # Sharpen a bit
    kernel = np.array(
        [
            [0, -1, 0],
            [-1, 5, -1],
            [0, -1, 0],
        ],
        dtype=np.float32,
    )
    sharpened = cv2.filter2D(enhanced, -1, kernel)

    return cv_to_pil(sharpened)


def vivid_filter(img: Image.Image) -> Image.Image:
    """
    Vivid:
    - Boost saturation
    - Slight contrast stretch
    """
    cv = pil_to_cv(img)
    hsv = cv2.cvtColor(cv, cv2.COLOR_BGR2HSV).astype(np.float32)
    h, s, v = cv2.split(hsv)

    # Boost saturation
    s *= 1.4
    s = np.clip(s, 0, 255)

    # Light contrast on value channel
    v = v * 1.1 + 5
    v = np.clip(v, 0, 255)

    vivid_hsv = cv2.merge([h, s, v]).astype(np.uint8)
    vivid_bgr = cv2.cvtColor(vivid_hsv, cv2.COLOR_HSV2BGR)

    return cv_to_pil(vivid_bgr)


def vintage_filter(img: Image.Image) -> Image.Image:
    """
    Vintage:
    - Slight fade
    - Warm tone
    - Lower contrast a bit
    """
    cv = pil_to_cv(img)
    # Convert to float for gentle ops
    f = cv.astype(np.float32) / 255.0

    # Slight fade
    f = f * 0.9 + 0.05

    # Warm tone: boost red channel
    f[..., 2] *= 1.1  # R channel in BGR is index 2
    f = np.clip(f, 0.0, 1.0)

    # Back to uint8
    vintage = (f * 255).astype(np.uint8)
    return cv_to_pil(vintage)


# ---------- Dispatcher ----------

def apply_filter(
    img: Image.Image,
    name: FilterName,
    blur_ksize: int = 9,
) -> Image.Image:
    if name == "none":
        return img

    if name == "bw":
        return bw_filter(img)
    if name == "sketch":
        return sketch_filter(img)
    if name == "cartoon":
        return cartoon_filter(img)
    if name == "blur":
        return blur_filter(img, ksize=blur_ksize)

    if name == "auto_enhance":
        return auto_enhance_filter(img)
    if name == "vivid":
        return vivid_filter(img)
    if name == "vintage":
        return vintage_filter(img)

    # Fallback: no change
    return img
