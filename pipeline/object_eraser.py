# pipeline/object_eraser.py

import io

import numpy as np
import cv2
from PIL import Image
import streamlit as st
from streamlit_drawable_canvas import st_canvas


def run_object_eraser_tool(image_bytes: bytes, disc_id: str, max_dim: int):
    """
    Object Eraser mode (drawing directly on the image):

    - Shows the image as the background of a drawable canvas
    - User draws rectangles on top of the image
    - We build a mask from the drawn areas and perform cv2.inpaint

    Returns:
        original_resized (PIL.Image)
        inpainted_pil (PIL.Image or None if user didn't apply yet)
    """
    # Load image
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    w, h = img.size

    # Resize to max_dim while keeping aspect ratio
    longest = max(w, h)
    if longest > max_dim:
        scale = max_dim / float(longest)
        img = img.resize((int(w * scale), int(h * scale)), Image.BILINEAR)
        w, h = img.size

    st.markdown("#### Object Eraser")
    st.caption("Draw rectangles directly over the image where you want to erase, then click apply.")

    # Canvas directly on image
    canvas_result = st_canvas(
        fill_color="rgba(255, 0, 0, 0.3)",   # semi-transparent red fill
        stroke_width=2,
        stroke_color="#ff0000",
        background_image=img,                # 🔥 draw ON the image
        height=h,
        width=w,
        drawing_mode="rect",                 # change to "freedraw" if you want freehand
        key=f"eraser_canvas_{disc_id}",
    )

    inpainted_pil = None

    apply = st.button("🧽 Apply object eraser", key=f"apply_eraser_{disc_id}")

    if apply and canvas_result.image_data is not None:
        # image_data = RGBA canvas: background (image) + drawing
        rgba = canvas_result.image_data.astype("uint8")  # (H, W, 4)
        rgb = rgba[..., :3]

        # Build mask: where canvas differs from original image, that's where user drew
        orig_arr = np.array(img).astype("uint8")
        diff = np.abs(rgb.astype("int16") - orig_arr.astype("int16"))
        diff_gray = np.max(diff, axis=2)
        mask = (diff_gray > 10).astype("uint8") * 255  # threshold to ignore tiny noise

        # Inpaint
        src_bgr = cv2.cvtColor(orig_arr, cv2.COLOR_RGB2BGR)
        inpainted_bgr = cv2.inpaint(src_bgr, mask, 3, cv2.INPAINT_TELEA)
        inpainted_rgb = cv2.cvtColor(inpainted_bgr, cv2.COLOR_BGR2RGB)
        inpainted_pil = Image.fromarray(inpainted_rgb)

    # original_resized = img, inpainted_pil can be None (if not applied yet)
    return img, inpainted_pil
