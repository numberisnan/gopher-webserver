import mimetypes
import os

def determine_item_type(full_path):
    mime_type, _ = mimetypes.guess_type(full_path)
    if not mime_type:
        mime_type = ''
    file_extension = os.path.splitext(full_path)[1].lower()

    if os.path.isdir(full_path) or file_extension == '.gopher':
        return '1'  # Directory / menu
    if mime_type.startswith('text/'):
        return '0'  # Text file
    if mime_type.startswith('image/'):
        if mime_type == 'image/gif':
            return 'g'      # GIF
        elif mime_type == 'image/bitmap':
            return ':'      # BMP (Gopher+)
        else:
            return 'I'      # Generic image
    if mime_type.startswith('video/'):
        return ';'          # Video (Gopher+)
    if mime_type.startswith('audio/'):
        return '<'          # Audio (Gopher+)
    return '9'              # Binary / unknown

def make_menu(path, host='localhost', port=70, root_config=None):
    """
    Build a Gopher menu for a directory.

    - Adds a Search item (type 7) if root_config['search'] is True.
    - Uses override_type if provided; otherwise guesses per file.
    - Host and port are passed so links are accurate for multi-server setups.
    """
    menu_items = []

    if root_config and root_config.get("search"):
        menu_items.append(f"7Search\t/search\t{host}\t{port}")

    override_type = None
    if root_config:
        ot = root_config.get("override_type")
        if ot and isinstance(ot, str) and len(ot) == 1:
            override_type = ot

    for name in os.listdir(path):
        full = os.path.join(path, name)
        item_type = override_type if override_type else determine_item_type(full)
        menu_items.append(f"{item_type}{name}\t{name}\t{host}\t{port}")

    menu_items.append(".")
    return "\r\n".join(menu_items)