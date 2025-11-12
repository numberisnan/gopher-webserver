import json

def load_config(config_path):
    with open(config_path, 'r') as f:
        config = json.load(f)
    return config

def get_default_root_object(path):
    return {
        "directory": path,
        "search": False,
        "search_recursive": False,
        "override_type": False
    }