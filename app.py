# app.py

import io
import os

import streamlit as st

from pipeline.discussions import (
    init_session_state,
    create_new_discussion,
    get_current_discussion,
)
from pipeline.processing import process_image



def main():
    st.set_page_config(
        page_title="Image Style Explorer",
        page_icon="🎨",
        layout="wide",
    )

    # ----------------- Init state -----------------
    init_session_state()
    discussions = st.session_state["discussions"]

    st.title("🎨 Image Style Explorer")
    st.write("Upload an image, choose a style, and compare before vs after.")

    # ----------------- Sidebar -----------------
    # 1) Quality toggle
    quality_mode = st.sidebar.radio(
        "Quality mode",
        ("Fast", "High quality"),
        horizontal=True,
        key="quality_mode",
    )

    st.sidebar.markdown("---")

    # 2) New discussion button (only if no blank exists)
    if st.sidebar.button("➕ New discussion"):
        has_blank = any(d["image_bytes"] is None for d in discussions.values())
        if not has_blank:
            create_new_discussion()
            # discussions updated via session_state

    # 3) Discussions list
    st.sidebar.markdown("### Discussions")

    disc_ids = list(discussions.keys())
    current_id = st.session_state["current_discussion_id"]

    def format_discussion(did: str) -> str:
        return discussions[did]["name"]

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

    # ----------------- Main area -----------------
    current_id, disc = get_current_discussion()
    if not current_id or disc is None:
        st.info("No discussion selected.")
        return

    st.subheader(disc["name"])

    # ---- Upload handling ----
    if disc["image_bytes"] is None:
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

            # Force a clean rebuild so we go straight to the style UI
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

    # ---- Image processing ----
    max_dim = 600 if quality_mode == "Fast" else 1200

    with st.spinner("Processing image..."):
        original_resized, styled_image = process_image(
            image_bytes=image_bytes,
            filter_label=filter_label,
            blur_strength=blur_strength,
            painting_detail=painting_detail,
            painting_color_smooth=painting_color_smooth,
            max_dim=max_dim,
        )

    # Save style settings
    disc["filter_label"] = filter_label
    disc["blur_strength"] = blur_strength
    disc["painting_detail"] = painting_detail
    disc["painting_color_smooth"] = painting_color_smooth
    discussions[current_id] = disc
    st.session_state["discussions"] = discussions

    # ---- Before vs After ----
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

    # ---- Download ----
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
