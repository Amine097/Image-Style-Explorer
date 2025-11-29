# styles/artistic.py

from PIL import Image
import numpy as np
import cv2


def _pil_to_cv2(pil_img: Image.Image) -> np.ndarray:
    rgb = np.array(pil_img.convert("RGB"))
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    return bgr


def _cv2_to_pil(bgr_img: np.ndarray) -> Image.Image:
    rgb = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb)


def painting(image: Image.Image, sigma_s: int = 60, sigma_r: float = 0.6) -> Image.Image:
    """
    Advanced 'painting' style using OpenCV stylization.
    sigma_s: spatial extent of the effect (0–200)
    sigma_r: range for color (0–1)
    """
    bgr = _pil_to_cv2(image)

    painted_bgr = cv2.stylization(
        bgr,
        sigma_s=sigma_s,
        sigma_r=sigma_r,
    )

    return _cv2_to_pil(painted_bgr)
