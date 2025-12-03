import os

from util import determine_item_type

def make_menu(path, host, port, root_config, context):
    """
    Build a Gopher menu for a directory.

    - Adds a Search item (type 7) if root_config['search'] is True.
    - Uses override_type if provided; otherwise guesses per file.
    - Host and port are passed so links are accurate for multi-server setups.
    """
    menu_items = []
    override_type = None

    if root_config.get("search", False):
        menu_items.append(f"7Search\t{context}/search\t{host}\t{port}")

    if root_config.get("override_type", None):
        ot = root_config.get("override_type", None)
        if ot and isinstance(ot, str) and len(ot) == 1: # Single character
            override_type = ot

    for name in os.listdir(path):
        full = os.path.join(path, name)
        item_type = override_type if override_type else determine_item_type(full)
        menu_items.append(f"{item_type}{name}\t{context}{name}\t{host}\t{port}")

    if root_config.get("back_link", False):
        menu_items.append(f"1.. (back)\t{context}\t{host}\t{port}")

    menu_items.append(".")
    return "\r\n".join(menu_items)