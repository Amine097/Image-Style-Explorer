# pipeline/projects.py

from typing import Dict, Any, Optional
import streamlit as st

Project = Dict[str, Any]


def init_project_state() -> None:
    """Ensure base project structures exist."""
    if "projects" not in st.session_state:
        st.session_state["projects"] = {}
    if "next_project_id" not in st.session_state:
        st.session_state["next_project_id"] = 1
    if "current_project_id" not in st.session_state:
        # None = default mode (no project currently open)
        st.session_state["current_project_id"] = None
    if "pending_project_creation" not in st.session_state:
        st.session_state["pending_project_creation"] = False
    if "pending_project_name" not in st.session_state:
        st.session_state["pending_project_name"] = ""


def get_projects() -> Dict[str, Project]:
    init_project_state()
    return st.session_state["projects"]


def get_current_project_id() -> Optional[str]:
    init_project_state()
    return st.session_state["current_project_id"]


def set_current_project(project_id: Optional[str]) -> None:
    """Set the current project (None = default mode)."""
    init_project_state()
    st.session_state["current_project_id"] = project_id


def start_project_creation() -> None:
    """
    Start the project creation flow.
    We don't create the project until the user submits a name.
    """
    init_project_state()
    st.session_state["pending_project_creation"] = True
    st.session_state["pending_project_name"] = ""
    # When naming a project, we are not inside any discussion
    st.session_state["current_discussion_id"] = None


def finalize_project_creation(name: str) -> str:
    """Create the project after the user submits a name."""
    init_project_state()

    projects = st.session_state["projects"]
    next_id = st.session_state["next_project_id"]

    proj_id = f"proj_{next_id}"
    st.session_state["next_project_id"] = next_id + 1

    projects[proj_id] = {
        "name": name.strip(),
        "discussion_ids": [],
    }

    # Enter project mode, but no specific discussion yet
    st.session_state["current_project_id"] = proj_id
    st.session_state["current_discussion_id"] = None

    # Clear pending state
    st.session_state["pending_project_creation"] = False
    st.session_state["pending_project_name"] = ""

    return proj_id


def get_project_discussion_ids(project_id: str) -> list[str]:
    init_project_state()
    projects = st.session_state["projects"]
    if project_id not in projects:
        return []
    return list(projects[project_id].get("discussion_ids", []))
