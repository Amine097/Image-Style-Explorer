# app.py

import io
import os

import streamlit as st

from pipeline import init_pipeline_state
from pipeline.processing import process_image
from pipeline.projects import (
    get_projects,
    get_current_project_id,
    set_current_project,
    start_project_creation,
    finalize_project_creation,
    get_project_discussion_ids,
)
from pipeline.discussions import (
    get_discussions,
    get_current_discussion,
    get_current_discussion_id,
    set_current_discussion,
    create_new_discussion,
    get_global_discussion_ids,
)


def main():
    st.set_page_config(
        page_title="Image Style Explorer",
        page_icon="🎨",
        layout="wide",
    )

    # ---------------------------------------
    # Init pipeline state
    # ---------------------------------------
    init_pipeline_state()

    projects = get_projects()
    discussions = get_discussions()
    current_project_id = get_current_project_id()
    current_discussion_id = get_current_discussion_id()

    # ---------------------------------------
    # Handle pending project creation (name screen)
    # ---------------------------------------
    if st.session_state.get("pending_project_creation", False):
        st.subheader("Create a new project")
        st.write("Please choose a name for your project:")

        name = st.text_input(
            "Project name",
            value=st.session_state.get("pending_project_name", ""),
            key="pending_project_name_input",
        )
        st.session_state["pending_project_name"] = name

        if st.button("Create project", disabled=not name.strip()):
            finalize_project_creation(name)
            st.rerun()

        return  # nothing else renders until project is named

    # ---------------------------------------
    # Page header
    # ---------------------------------------
    st.title("🎨 Image Style Explorer")
    st.write("Upload an image, choose a style, and compare before vs after.")

    # ---------------------------------------
    # SIDEBAR
    # ---------------------------------------

    # 1) Quality toggle
    quality_mode = st.sidebar.radio(
        "Quality mode",
        ("Fast", "High quality"),
        horizontal=True,
        key="quality_mode",
    )

    st.sidebar.markdown("---")

    # 2) Projects section
    st.sidebar.markdown("### Projects")

    # + New project button
    if st.sidebar.button("➕ New project"):
        # You can also prevent multiple empty projects if you want:
        # has_blank_project = any(len(p.get("discussion_ids", [])) == 0 for p in projects.values())
        # if not has_blank_project:
        start_project_creation()
        st.rerun()

    project_ids = list(projects.keys())

    # Simple list of project names (click = go to project page)
    for proj_id in project_ids:
        proj_name = projects[proj_id]["name"]
        if st.sidebar.button(proj_name, key=f"proj_btn_{proj_id}"):
            set_current_project(proj_id)
            # Going to project mode, but not yet inside a discussion
            set_current_discussion(None)
            st.rerun()

    # If we are inside a project discussion, show its discussions under the project
    if current_project_id is not None and current_discussion_id is not None:
        # Check that the current discussion belongs to this project
        disc = discussions.get(current_discussion_id)
        if disc and disc.get("project_id") == current_project_id:
            st.sidebar.markdown(f"**{projects[current_project_id]['name']} – discussions**")
            proj_disc_ids = get_project_discussion_ids(current_project_id)

            if proj_disc_ids:
                selected_proj_disc = st.sidebar.radio(
                    "Select a discussion",
                    options=proj_disc_ids,
                    index=proj_disc_ids.index(current_discussion_id),
                    format_func=lambda did: discussions[did]["name"],
                    key=f"proj_disc_selector_{current_project_id}",
                )
                if selected_proj_disc != current_discussion_id:
                    set_current_discussion(selected_proj_disc)
                    st.rerun()

    st.sidebar.markdown("---")

    # 3) Default discussions section (always visible)
    st.sidebar.markdown("### Discussions")

    # + New default discussion (not in any project)
    if st.sidebar.button("➕ New discussion"):
        # Optional: only allow one empty default discussion at a time
        global_ids = get_global_discussion_ids()
        has_blank_global = any(
            discussions[d]["image_bytes"] is None for d in global_ids
        )
        if not has_blank_global:
            create_new_discussion(project_id=None)
            # default mode: leaving project context
            set_current_project(None)
            st.rerun()

    global_ids = get_global_discussion_ids()
    if global_ids:
        selected_global_disc = st.sidebar.radio(
            "Select a discussion",
            options=global_ids,
            format_func=lambda did: discussions[did]["name"],
            key="global_disc_selector",
        )

        # Track last selected global discussion to detect real user changes
        prev_selected = st.session_state.get("last_global_disc_selected")

        if prev_selected is None:
            # First time we just record, no navigation
            st.session_state["last_global_disc_selected"] = selected_global_disc
        elif selected_global_disc != prev_selected:
            # User really changed the selection -> go to default mode
            st.session_state["last_global_disc_selected"] = selected_global_disc
            set_current_project(None)
            set_current_discussion(selected_global_disc)
            st.experimental_rerun()


    # ---------------------------------------
    # MAIN AREA
    # ---------------------------------------
    # Refresh local vars after any possible rerun request
    projects = get_projects()
    discussions = get_discussions()
    current_project_id = get_current_project_id()
    current_discussion_id = get_current_discussion_id()
    disc_id, disc = get_current_discussion()

    # Case A: In "project mode" with NO specific discussion selected
    if current_project_id is not None and current_discussion_id is None:
        proj = projects[current_project_id]
        st.subheader(proj["name"])
        st.write("This project contains the following discussions:")

        proj_disc_ids = get_project_discussion_ids(current_project_id)

        if proj_disc_ids:
            for d_id in proj_disc_ids:
                d = discussions[d_id]
                if st.button(d["name"], key=f"proj_disc_btn_{d_id}"):
                    # Enter this discussion
                    set_current_discussion(d_id)
                    st.rerun()
        else:
            st.info("This project has no discussions yet.")

        # Button to create first/new discussion in this project
        if st.button("➕ New discussion in this project"):
            create_new_discussion(project_id=current_project_id)
            st.rerun()

        return

    # Case B: No discussion at all (shouldn't really happen thanks to init, but safe)
    if disc is None:
        st.info("No discussion selected. Create or select one from the sidebar.")
        return

    # From here on, we are inside a discussion (default or project)
    st.subheader(disc["name"])

    # ---- Upload handling ----
    if disc["image_bytes"] is None:
        st.write("Start this discussion by uploading an image.")
        uploaded_file = st.file_uploader(
            "Upload an image (PNG/JPG)",
            type=["png", "jpg", "jpeg"],
            key=f"uploader_{disc_id}",
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

            discussions[disc_id] = disc
            st.session_state["discussions"] = discussions

            st.rerun()

        return

    # If we reach here, this discussion HAS an image
    image_bytes = disc["image_bytes"]

    # ---- Style selection ----
    st.markdown("### Style")

    style_options = [
        "None",
        "Black & White",
        "Sketch",
        "Cartoon",
        "Blur",
        "Painting",
        "Auto Enhance",
        "Vivid Colors",
        "Vintage",
    ]

    current_style_index = style_options.index(disc.get("filter_label", "None"))

    filter_label = st.selectbox(
        "Choose a style",
        options=style_options,
        index=current_style_index,
        key=f"style_{disc_id}",
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
            key=f"blur_{disc_id}",
        )
    elif filter_label == "Painting":
        painting_detail = st.slider(
            "Painting detail",
            min_value=10,
            max_value=200,
            value=painting_detail,
            step=10,
            help="Higher values = a stronger painting effect.",
            key=f"paint_detail_{disc_id}",
        )
        painting_color_smooth = st.slider(
            "Color smoothing",
            min_value=0.1,
            max_value=1.0,
            value=painting_color_smooth,
            step=0.1,
            help="Higher values = smoother colors.",
            key=f"paint_color_{disc_id}",
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
    discussions[disc_id] = disc
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
