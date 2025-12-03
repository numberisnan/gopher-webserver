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

def process_gopher_output(output):
    """
    Process raw output from a CGI script into Gopher menu format.
    Assumes the output is already in valid Gopher format.
    """
    lines = output.splitlines()
    gopher_output = ""
    for line in lines:
        gopher_output += "i" + line + "\r\n"
    gopher_output += "."
    return gopher_output