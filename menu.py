import mimetypes
import os

def make_menu(path):
    menu_items = []
    for name in os.listdir(path):
        full = os.path.join(path, name)
        if os.path.isdir(full):
            menu_items.append(f"1{name}\t{name}\tlocalhost\t70") # '1' indicates a directory or submenu

        mime_type, _ = mimetypes.guess_type(full) # Guess MIME type based on file extension
        if not mime_type:
            mime_type = ''

        file_extension = os.path.splitext(name)[1].lower() # Get file extension (for special cases)

        if file_extension == '.gopher':
            item_type = '1'  # '1' indicates a Gopher menu file (server feature)
        elif mime_type.startswith('text/'):
            item_type = '0'  # '0' indicates a text file
        elif mime_type.startswith('image/'):
            if mime_type == 'image/gif':
                item_type = 'g'  # 'g' indicates a GIF image
            elif mime_type == 'image/bitmap':
                item_type = ':'  # ':' indicates a BMP image (Gopher+)
            else:
                item_type = 'I'  # 'I' indicates an image file
        elif mime_type.startswith('video/'):
            item_type = ';'  # ';' indicates a movie file (Gopher+)
        elif mime_type.startswith('audio/'):
            item_type = '<'  # '<' indicates a sound file (Gopher+)
        else:
            item_type = '9'  # '9' indicates a binary file or unknown type
        menu_items.append(f"{item_type}{name}\t{name}\tlocalhost\t70") # Append item to menu

    menu_items.append(".")
    return "\r\n".join(menu_items) # Menu items are separated by CRLF