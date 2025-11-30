# pipeline/discussions.py

from typing import Tuple, Optional, Dict, Any

import streamlit as st

Discussion = Dict[str, Any]


def init_discussion_state() -> None:
    """Ensure discussion-related session_state fields exist."""
    if "discussions" not in st.session_state:
        st.session_state["discussions"] = {}
    if "next_discussion_id" not in st.session_state:
        st.session_state["next_discussion_id"] = 1
    if "current_discussion_id" not in st.session_state:
        st.session_state["current_discussion_id"] = None


def get_discussions() -> Dict[str, Discussion]:
    init_discussion_state()
    return st.session_state["discussions"]


def get_current_discussion_id() -> Optional[str]:
    init_discussion_state()
    return st.session_state["current_discussion_id"]


def set_current_discussion(disc_id: Optional[str]) -> None:
    init_discussion_state()
    st.session_state["current_discussion_id"] = disc_id


def create_new_discussion(project_id: Optional[str]) -> str:
    """
    Create a new discussion.

    - If project_id is None, it's a default (non-project) discussion.
    - Otherwise it belongs to that project.
    """
    init_discussion_state()

    discussions = st.session_state["discussions"]
    next_id = st.session_state["next_discussion_id"]

    disc_id = f"disc_{next_id}"
    st.session_state["next_discussion_id"] = next_id + 1

    discussions[disc_id] = {
        "name": f"New Discussion",
        "image_bytes": None,
        "orig_name": None,
        "orig_ext": ".png",
        "filter_label": "None",
        "blur_strength": 9,
        "painting_detail": 60,
        "painting_color_smooth": 0.6,
        "project_id": project_id,
    }

    st.session_state["current_discussion_id"] = disc_id

    # Attach to project if applicable
    if project_id is not None:
        projects = st.session_state["projects"]
        projects[project_id]["discussion_ids"].append(disc_id)

    return disc_id


def get_current_discussion() -> Tuple[Optional[str], Optional[Discussion]]:
    disc_id = get_current_discussion_id()
    if not disc_id:
        return None, None
    discussions = st.session_state["discussions"]
    return disc_id, discussions.get(disc_id)


def get_global_discussion_ids() -> list[str]:
    """Discussions not attached to any project (default mode)."""
    discussions = get_discussions()
    return [did for did, d in discussions.items() if d.get("project_id") is None]
