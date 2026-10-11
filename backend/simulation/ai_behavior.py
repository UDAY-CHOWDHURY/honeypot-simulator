


import random

def select_workflow_class():
    return random.choice(["browsing", "editing", "email"])

def generate_action_sequence(workflow_class):
    workflows = {
        "browsing": ["open_browser", "visit_website", "download_file"],
        "editing": ["open_editor", "write_notes", "save_file"],
        "email": ["check_email", "open_attachment"]
    }
    return workflows.get(workflow_class, ["move_mouse"])

