# pipeline/__init__.py
# Unified initializer for projects + discussions

from .projects import init_project_state
from .discussions import init_discussion_state, get_discussions, create_new_discussion


def init_pipeline_state():
    """Initialize required session_state keys and ensure at least one default discussion."""
    init_project_state()
    init_discussion_state()

    discussions = get_discussions()
    if not discussions:
        # Create an initial default discussion (no project)
        create_new_discussion(project_id=None)
