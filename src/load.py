import os
import json

# CAN DELETE:  Left this here for now in case for placeholder
# Setup project root path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
print("Project root:", project_root)

# CAN DELETE:  Left this here for now in case for placeholder
def load_arc_agi_data(filepath):
    """Load ARC AGI data from a JSON file"""
    full_path = os.path.join(project_root, filepath)

    with open(full_path, 'r') as f:
        data = json.load(f)

    return data