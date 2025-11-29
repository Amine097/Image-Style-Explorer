# discussions.py

from typing import Tuple, Optional, Dict, Any

import streamlit as st


Discussion = Dict[str, Any]


def create_new_discussion() -> None:
    """Create a new empty discussion and select it."""
    discussions: Dict[str, Discussion] = st.session_state["discussions"]
    next_id: int = st.session_state["next_discussion_id"]

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


def init_session_state() -> None:
    """Initialize all session_state fields we need."""
    if "discussions" not in st.session_state:
        st.session_state["discussions"] = {}
    if "next_discussion_id" not in st.session_state:
        st.session_state["next_discussion_id"] = 1

    discussions: Dict[str, Discussion] = st.session_state["discussions"]

    # If no discussions at all, create the first one
    if not discussions:
        create_new_discussion()
        discussions = st.session_state["discussions"]

    if "current_discussion_id" not in st.session_state:
        # pick first existing discussion
        st.session_state["current_discussion_id"] = list(discussions.keys())[0]


def get_current_discussion() -> Tuple[Optional[str], Optional[Discussion]]:
    disc_id: Optional[str] = st.session_state.get("current_discussion_id")
    if not disc_id:
        return None, None
    discussions: Dict[str, Discussion] = st.session_state["discussions"]
    return disc_id, discussions[disc_id]
