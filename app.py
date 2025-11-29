import io
import os

import streamlit as st
from PIL import Image

from styles import apply_filter, FilterName, painting


# -------------------------------
# Processing helpers
# -------------------------------

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
):
    """
    Cached image processing:
    - rebuild PIL image from bytes
    - resize
    - apply chosen style
    Returns (original_resized, styled_resized).
    """
    img = Image.open(io.BytesIO(image_bytes))
    img = resize_for_processing(img, max_dim=max_dim)

    label_to_name = {
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
        filter_name: FilterName = label_to_name[filter_label]  # type: ignore
        styled = apply_filter(
            img,
            filter_name,
            blur_ksize=blur_strength,
        )

    return img, styled


# -------------------------------
# Discussion management
# -------------------------------

def create_new_discussion():
    discussions = st.session_state["discussions"]
    next_id = st.session_state["next_discussion_id"]

    disc_id = f"disc_{next_id}"
    st.session_state["next_discussion_id"] = next_id + 1

    discussions[disc_id] = {
        "name": f"Discussion {next_id}",
        "image_bytes": None,
        "orig_name": None,
        "orig_ext": ".png",
        "filter_label": "None",
        "blur_strength": 9,
        "painting_detail": 60,
        "painting_color_smooth": 0.6,
    }
    st.session_state["current_discussion_id"] = disc_id


def init_session_state():
    if "discussions" not in st.session_state:
        st.session_state["discussions"] = {}
    if "next_discussion_id" not in st.session_state:
        st.session_state["next_discussion_id"] = 1

    discussions = st.session_state["discussions"]

    # If no discussions at all, create the first one
    if not discussions:
        create_new_discussion()
        discussions = st.session_state["discussions"]

    if "current_discussion_id" not in st.session_state:
        # pick first existing discussion
        st.session_state["current_discussion_id"] = list(discussions.keys())[0]


def get_current_discussion():
    disc_id = st.session_state.get("current_discussion_id")
    if not disc_id:
        return None, None
    discussions = st.session_state["discussions"]
    return disc_id, discussions[disc_id]


# -------------------------------
# Streamlit app
# -------------------------------

def main():
    st.set_page_config(
        page_title="Image Style Explorer",
        page_icon="🎨",
        layout="wide",
    )

    init_session_state()

    st.title("🎨 Image Style Explorer")
    st.write("Upload an image, choose a style, and compare before vs after.")

    discussions = st.session_state["discussions"]

    # -------- Sidebar: quality + discussions --------

    # 1) Quality toggle
    quality_mode = st.sidebar.radio(
        "Quality mode",
        ("Fast", "High quality"),
        horizontal=True,
        key="quality_mode",
    )

    st.sidebar.markdown("---")

    # 2) New discussion button
    if st.sidebar.button("➕ New discussion"):
        # Only create new if there is NO blank discussion already
        has_blank = any(d["image_bytes"] is None for d in discussions.values())
        if not has_blank:
            create_new_discussion()

    # 3) Discussions list
    st.sidebar.markdown("### Discussions")

    disc_ids = list(discussions.keys())

    def format_discussion(did: str) -> str:
        return discussions[did]["name"]

    current_id = st.session_state["current_discussion_id"]
    selected_id = st.sidebar.radio(
        "Select a discussion",
        options=disc_ids,
        index=disc_ids.index(current_id),
        format_func=format_discussion,
        key="discussion_selector",
    )

    if selected_id != current_id:
        st.session_state["current_discussion_id"] = selected_id
        current_id = selected_id

    # -------- Main area --------

    current_id, disc = get_current_discussion()
    if not current_id or disc is None:
        st.info("No discussion selected.")
        return

    st.subheader(disc["name"])

    # ---- Upload / image handling ----
    if disc["image_bytes"] is None:
        # Only show upload when no image
        st.write("Start this discussion by uploading an image.")
        uploaded_file = st.file_uploader(
            "Upload an image (PNG/JPG)",
            type=["png", "jpg", "jpeg"],
            key=f"uploader_{current_id}",
        )

        if uploaded_file is not None:
            image_bytes = uploaded_file.getvalue()

            filename = uploaded_file.name
            base, ext = os.path.splitext(filename)
            if not ext:
                ext = ".png"

            disc["image_bytes"] = image_bytes
            disc["orig_name"] = base
            disc["orig_ext"] = ext
            disc["name"] = base  # rename discussion to image name

            discussions[current_id] = disc
            st.session_state["discussions"] = discussions

            # After updating state, we can just stop; next interaction will show style UI
            st.rerun()

        return

    # If we reach here, this discussion HAS an image
    image_bytes = disc["image_bytes"]

    # ---- Style selection ----
    st.markdown("### Style")

    style_options = ["None", "Black & White", "Sketch", "Cartoon", "Blur", "Painting"]
    current_style_index = style_options.index(disc.get("filter_label", "None"))

    filter_label = st.selectbox(
        "Choose a style",
        options=style_options,
        index=current_style_index,
        key=f"style_{current_id}",
    )

    # Sliders per discussion
    blur_strength = disc.get("blur_strength", 9)
    painting_detail = disc.get("painting_detail", 60)
    painting_color_smooth = disc.get("painting_color_smooth", 0.6)

    if filter_label == "Blur":
        blur_strength = st.slider(
            "Blur intensity",
            min_value=3,
            max_value=31,
            value=blur_strength,
            step=2,
            help="Higher values = stronger blur.",
            key=f"blur_{current_id}",
        )
    elif filter_label == "Painting":
        painting_detail = st.slider(
            "Painting detail",
            min_value=10,
            max_value=200,
            value=painting_detail,
            step=10,
            help="Higher values = a stronger painting effect.",
            key=f"paint_detail_{current_id}",
        )
        painting_color_smooth = st.slider(
            "Color smoothing",
            min_value=0.1,
            max_value=1.0,
            value=painting_color_smooth,
            step=0.1,
            help="Higher values = smoother colors.",
            key=f"paint_color_{current_id}",
        )

    # Resolution based on quality mode
    max_dim = 600 if quality_mode == "Fast" else 1200

    # ---- Process image ----
    with st.spinner("Processing image..."):
        original_resized, styled_image = process_image(
            image_bytes=image_bytes,
            filter_label=filter_label,
            blur_strength=blur_strength,
            painting_detail=painting_detail,
            painting_color_smooth=painting_color_smooth,
            max_dim=max_dim,
        )

    # Save latest settings
    disc["filter_label"] = filter_label
    disc["blur_strength"] = blur_strength
    disc["painting_detail"] = painting_detail
    disc["painting_color_smooth"] = painting_color_smooth
    discussions[current_id] = disc
    st.session_state["discussions"] = discussions

    # ---- Before vs after ----
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Before")
        st.image(original_resized, use_container_width=True)

    with col2:
        st.subheader("After")
        st.image(styled_image, use_container_width=True)

    st.caption(
        f"Mode: {quality_mode}. Images are processed up to {max_dim}px on the longest side."
    )

    # ---- Download button ----
    st.markdown("---")
    st.subheader("Download stylized image")

    out_buf = io.BytesIO()
    styled_image.save(out_buf, format="PNG")
    out_bytes = out_buf.getvalue()

    orig_name = disc.get("orig_name") or "image"
    style_suffix = filter_label.lower().replace(" ", "-")
    download_name = f"{orig_name}_{style_suffix}.png"

    st.download_button(
        label=f"📥 Download ({download_name})",
        data=out_bytes,
        file_name=download_name,
        mime="image/png",
    )


if __name__ == "__main__":
    main()
