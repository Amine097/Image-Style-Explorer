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


# ------------------------------------------------------------
# Theming: light / dark with sci-fi blue/purple accents
# ------------------------------------------------------------

def inject_theme_css(mode: str):
    """Inject global CSS depending on light/dark theme."""
    if mode == "dark":
        bg_app = "#020617"
        bg_card = "rgba(15, 23, 42, 0.98)"
        bg_card_muted = "rgba(15, 23, 42, 0.90)"
        text_main = "#e5e7eb"
        text_sub = "#9ca3af"
        border = "rgba(148, 163, 184, 0.35)"
        accent_blue = "#38bdf8"
        accent_purple = "#a855f7"
        header_grad = "radial-gradient(circle at 0 0, #1d2340, #020617 60%)"
        app_bg_grad = (
            "radial-gradient(circle at top, #020617 0, #020617 40%, #020617 100%)"
        )
    else:  # light
        bg_app = "#f4f4fb"
        bg_card = "#ffffff"
        bg_card_muted = "#f9fafb"
        text_main = "#0f172a"
        text_sub = "#6b7280"
        border = "rgba(148, 163, 184, 0.6)"
        accent_blue = "#2563eb"
        accent_purple = "#7c3aed"
        header_grad = "linear-gradient(135deg, #eef2ff, #e0f2fe)"
        app_bg_grad = "linear-gradient(180deg, #f4f4fb 0, #eef2ff 40%, #f9fafb 100%)"

    st.markdown(
        f"""
        <style>
        .stApp {{
            background: {app_bg_grad};
            color: {text_main};
        }}

        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}

        .main-header {{
            padding: 0.9rem 1.2rem 1.2rem 1.2rem;
            border-radius: 1.1rem;
            background: {header_grad};
            color: {text_main};
            margin-bottom: 1.0rem;
            border: 1px solid {border};
            box-shadow: 0 18px 45px rgba(15, 23, 42, 0.65);
        }}
        .main-header h1 {{
            font-size: 1.9rem;
            margin: 0 0 0.25rem 0;
        }}
        .main-header p {{
            font-size: 0.9rem;
            opacity: 0.9;
            margin: 0;
        }}

        .pill {{
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            padding: 0.15rem 0.6rem;
            border-radius: 999px;
            font-size: 0.7rem;
            font-weight: 500;
            background: rgba(56, 189, 248, 0.10);
            color: {accent_blue};
        }}
        .pill span.dot {{
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: {accent_blue};
        }}

        .card {{
            background: {bg_card};
            border-radius: 1rem;
            padding: 1rem 1.25rem;
            border: 1px solid {border};
            margin-bottom: 1rem;
        }}

        .card-muted {{
            background: {bg_card_muted};
            border-radius: 0.9rem;
            padding: 0.9rem 1.1rem;
            border: 1px dashed {border};
            margin-bottom: 0.9rem;
        }}

        .subtitle {{
            font-size: 0.85rem;
            color: {text_sub};
        }}

        .breadcrumb {{
            font-size: 0.85rem;
            color: {text_sub};
        }}
        .breadcrumb strong {{
            color: {text_main};
        }}

        .preview-title {{
            font-size: 0.95rem;
            font-weight: 600;
            margin-bottom: 0.4rem;
        }}

        .download-box {{
            background: {bg_card};
            border-radius: 0.9rem;
            padding: 0.85rem 1rem;
            border: 1px solid {border};
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 0.75rem;
        }}
        .download-box span {{
            font-size: 0.85rem;
            color: {text_sub};
        }}

        section[data-testid="stSidebar"] h2 {{
            font-size: 0.95rem !important;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: {text_sub};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------
# MAIN APP
# ------------------------------------------------------------

def main():
    st.set_page_config(
        page_title="Image Style Explorer",
        page_icon="🎨",
        layout="wide",
    )

    # Init all state (projects + discussions)
    init_pipeline_state()

    projects = get_projects()
    discussions = get_discussions()
    current_project_id = get_current_project_id()
    current_discussion_id = get_current_discussion_id()

    # ------------- Theme handling (session) -------------
    if "theme_mode" not in st.session_state:
        st.session_state["theme_mode"] = "dark"

    theme_mode = st.session_state["theme_mode"]
    inject_theme_css(theme_mode)

    # ---------------------------------------
    # Top bar: header + theme toggle
    # ---------------------------------------
    header_col1, header_col2 = st.columns([5, 1])

    with header_col1:
        st.markdown(
            """
            <div class="main-header">
              <div style="display:flex;flex-direction:column;gap:0.45rem;">
                <div>
                  <h1>Image Style Explorer</h1>
                  <p>Organise your work into projects and discussions, then experiment with visual styles on your images.</p>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with header_col2:
        st.write("")
        st.write("")
        dark_default = theme_mode == "dark"
        toggled = st.toggle("Dark mode", value=dark_default, key="theme_toggle")
        new_mode = "dark" if toggled else "light"
        if new_mode != theme_mode:
            st.session_state["theme_mode"] = new_mode
            st.rerun()

    # ---------------------------------------
    # Handle pending project creation (name screen)
    # ---------------------------------------
    if st.session_state.get("pending_project_creation", False):
        st.markdown(
            """
            <div class="card">
              <div class="breadcrumb"><strong>New project</strong></div>
              <p class="subtitle">Name your project to start grouping related discussions and styles.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        name = st.text_input(
            "Project name",
            value=st.session_state.get("pending_project_name", ""),
            key="pending_project_name_input",
        )
        st.session_state["pending_project_name"] = name

        cols = st.columns([1, 4])
        with cols[0]:
            create_disabled = not name.strip()
            if st.button("Create project", disabled=create_disabled, use_container_width=True):
                finalize_project_creation(name)
                st.rerun()

        return  # nothing else renders until project is named

    # ---------------------------------------
    # SIDEBAR
    # ---------------------------------------

    # 1) Quality toggle
    st.sidebar.markdown("#### Rendering mode")
    quality_mode = st.sidebar.radio(
        "Quality",
        ("Fast", "High quality"),
        horizontal=True,
        key="quality_mode",
    )

    st.sidebar.markdown("---")

    # 2) Projects section
    st.sidebar.markdown("#### Projects")

    if st.sidebar.button("➕ New project", use_container_width=True):
        start_project_creation()
        st.rerun()

    project_ids = list(projects.keys())

    for proj_id in project_ids:
        proj_name = projects[proj_id]["name"]
        if st.sidebar.button(f"📁 {proj_name}", key=f"proj_btn_{proj_id}", use_container_width=True):
            set_current_project(proj_id)
            set_current_discussion(None)
            st.rerun()

    # If we are inside a project discussion, show its discussions nested
    if current_project_id is not None and current_discussion_id is not None:
        disc = discussions.get(current_discussion_id)
        if disc and disc.get("project_id") == current_project_id:
            st.sidebar.markdown(
                f"**{projects[current_project_id]['name']} – discussions**"
            )
            proj_disc_ids = get_project_discussion_ids(current_project_id)

            if proj_disc_ids:
                selected_proj_disc = st.sidebar.radio(
                    "Select",
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
    st.sidebar.markdown("#### Discussions")

    if st.sidebar.button("➕ New discussion", use_container_width=True):
        global_ids = get_global_discussion_ids()
        has_blank_global = any(
            discussions[d]["image_bytes"] is None for d in global_ids
        )
        if not has_blank_global:
            create_new_discussion(project_id=None)
            set_current_project(None)
            st.rerun()

    global_ids = get_global_discussion_ids()
    if global_ids:
        selected_global_disc = st.sidebar.radio(
            "Select",
            options=global_ids,
            format_func=lambda did: discussions[did]["name"],
            key="global_disc_selector",
        )

        prev_selected = st.session_state.get("last_global_disc_selected")
        if prev_selected is None:
            st.session_state["last_global_disc_selected"] = selected_global_disc
        elif selected_global_disc != prev_selected:
            st.session_state["last_global_disc_selected"] = selected_global_disc
            set_current_project(None)
            set_current_discussion(selected_global_disc)
            st.rerun()

    # ---------------------------------------
    # MAIN AREA LOGIC
    # ---------------------------------------
    projects = get_projects()
    discussions = get_discussions()
    current_project_id = get_current_project_id()
    current_discussion_id = get_current_discussion_id()
    disc_id, disc = get_current_discussion()

    # Case A: project mode, no specific discussion selected
    if current_project_id is not None and current_discussion_id is None:
        proj = projects[current_project_id]

        st.markdown(
            f"""
            <div class="card">
              <div class="breadcrumb">
                <strong>Project</strong> &nbsp;›&nbsp; <strong>{proj["name"]}</strong>
              </div>
              <p class="subtitle">Browse existing discussions in this project or spawn a new one.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        proj_disc_ids = get_project_discussion_ids(current_project_id)

        if proj_disc_ids:
            st.markdown("#### Discussions in this project")
            for d_id in proj_disc_ids:
                d = discussions[d_id]
                with st.container():
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"**{d['name']}**")
                        if d["image_bytes"] is None:
                            st.caption("Awaiting first image upload.")
                        else:
                            st.caption("Image uploaded · style configurable")
                    with col2:
                        if st.button("Open", key=f"proj_disc_btn_{d_id}", use_container_width=True):
                            set_current_discussion(d_id)
                            st.rerun()
        else:
            st.markdown(
                """
                <div class="card-muted">
                  <span class="subtitle">This project has no discussions yet. Create one to start experimenting with styles.</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("---")
        if st.button("➕ New discussion in this project", use_container_width=True):
            create_new_discussion(project_id=current_project_id)
            st.rerun()

        return

    # Case B: safety – no discussion at all
    if disc is None:
        st.markdown(
            """
            <div class="card-muted">
              <span class="subtitle">No active discussion. Create or select one from the sidebar.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # ---------------------------------------
    # Inside a discussion (default or project)
    # ---------------------------------------

    breadcrumb_parts = []
    if current_project_id is not None:
        breadcrumb_parts.append(projects[current_project_id]["name"])
    breadcrumb_parts.append(disc["name"])
    breadcrumb_html = " &nbsp;›&nbsp; ".join(
        f"<strong>{part}</strong>" for part in breadcrumb_parts
    )

    st.markdown(
        f"""
        <div class="card">
          <div style="display:flex;flex-direction:column;gap:0.45rem;">
            <div class="breadcrumb">{breadcrumb_html}</div>
            <div>
              <span class="pill"><span class="dot"></span><span>{quality_mode} mode</span></span>
              <span class="subtitle" style="margin-left:0.5rem;">Upload an image (if not done yet) and configure the style pipeline.</span>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---- Upload handling ----
    if disc["image_bytes"] is None:
        st.markdown(
            """
            <div class="card-muted">
              <span class="subtitle">This discussion doesn't have an image yet. Upload one to unlock styling controls.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

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

    # Discussion has an image
    image_bytes = disc["image_bytes"]

    # ---- Style controls ----
    with st.container():
        st.markdown(
            """
            <div class="card">
              <div style="display:flex;justify-content:space-between;align-items:center;gap:0.75rem;">
                <div>
                  <div class="preview-title">Style configuration</div>
                  <div class="subtitle">Choose a style and fine-tune its parameters.</div>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

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
        "Style",
        options=style_options,
        index=current_style_index,
        key=f"style_{disc_id}",
    )

    blur_strength = disc.get("blur_strength", 9)
    painting_detail = disc.get("painting_detail", 60)
    painting_color_smooth = disc.get("painting_color_smooth", 0.6)

    col_controls = st.columns(2)
    with col_controls[0]:
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
    with col_controls[1]:
        if filter_label == "Painting":
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

    with st.spinner("Running style pipeline..."):
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

    # ---- Preview ----
    st.markdown("#### Preview")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Before**")
        st.image(original_resized, use_container_width=True)
    with col2:
        st.markdown("**After**")
        st.image(styled_image, use_container_width=True)

    st.caption(
        f"Rendering mode: {quality_mode}. Images are processed up to {max_dim}px on the longest side."
    )

    # ---- Download ----
    st.markdown("---")

    out_buf = io.BytesIO()
    styled_image.save(out_buf, format="PNG")
    out_bytes = out_buf.getvalue()

    orig_name = disc.get("orig_name") or "image"
    style_suffix = filter_label.lower().replace(" ", "-")
    download_name = f"{orig_name}_{style_suffix}.png"

    st.markdown(
        f"""
        <div class="download-box">
          <span>Export the styled image for this discussion.</span>
          <span>Output: <code>{download_name}</code></span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.download_button(
        label="📥 Download styled image",
        data=out_bytes,
        file_name=download_name,
        mime="image/png",
    )


if __name__ == "__main__":
    main()
