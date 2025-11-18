import socket
import os

from menu import make_menu, determine_item_type
from config import get_default_root_object

def parse_search_selector(selector):
    """
    Accept formats:
    /search
    /search<TAB>term
    /search term
    /search/term
    Returns query string or None if missing.
    """
    if not selector.startswith('/search'):
        return None
    remainder = selector[len('/search'):]  # after '/search'
    if not remainder:
        return None
    if remainder.startswith('\t'):
        q = remainder[1:].strip()
        return q or None
    if '\t' in remainder:
        parts = remainder.split('\t', 1)
        q = parts[1].strip()
        return q or None
    if remainder.startswith(' '):
        q = remainder.strip()
        return q or None
    if remainder.startswith('/'):
        q = remainder[1:].strip()
        return q or None
    return None

def search_files(base_dir, query, recursive):
    """
    Return relative paths whose filename OR text content contains query (case-insensitive).
    """
    matches = []
    query_lower = query.lower()
    for root, dirs, files in os.walk(base_dir):
        for fname in files:
            rel = os.path.relpath(os.path.join(root, fname), base_dir)
            full = os.path.join(root, fname)

            # Filename match
            if query_lower in fname.lower():
                matches.append(rel)
                continue

            # Content match
            try:
                with open(full, 'r', encoding='utf-8', errors='ignore') as f:
                    if query_lower in f.read().lower():
                        matches.append(rel)
            except Exception:
                pass  # Skip unreadable/binary
        if not recursive:
            break
    return matches

def make_search_results(base_dir, host, port, query, recursive):
    lines = []
    lines.append(f"iSearch results for: {query}\tfake\t{host}\t{port}")
    results = search_files(base_dir, query, recursive)
    if not results:
        lines.append(f"iNo matches found.\tfake\t{host}\t{port}")
    else:
        for rel in results:
            full = os.path.join(base_dir, rel)
            item_type = determine_item_type(full)
            selector = rel.replace('\\', '/')
            lines.append(f"{item_type}{selector}\t{selector}\t{host}\t{port}")
    lines.append(".")
    return "\r\n".join(lines)

def make_response(selector, conn, config):
    """
    Respond based on config (root or selectors). Selector always starts with '/' externally.
    """
    if config.get("root", False):
        # Expand root string to full config if needed
        directory_config = get_default_root_object(config["root"]) if isinstance(config["root"], str) else config["root"]
        base_dir = directory_config.get("directory")
        host = config.get("host", "localhost")
        port = config.get("port", 70)

        # Handle search
        if directory_config.get("search") and selector.startswith('/search'):
            query = parse_search_selector(selector)
            if not query:
                # Instructional prompt
                msg = [
                    f"iSearch usage:\tfake\t{host}\t{port}",
                    f"i /search<TAB>term\tfake\t{host}\t{port}",
                    f"i /search term\tfake\t{host}\t{port}",
                    f"i /search/term\tfake\t{host}\t{port}",
                    "."
                ]
                conn.sendall("\r\n".join(msg).encode('utf-8') + b"\r\n")
                return
            recursive = directory_config.get("search_recursive", False)
            response = make_search_results(base_dir, host, port, query, recursive)
            conn.sendall(response.encode('utf-8') + b"\r\n")
            return

        # Normal directory or file serving
        path = os.path.join(base_dir, selector.lstrip('/'))
        if os.path.isdir(path):
            response = make_menu(path, host=host, port=port, root_config=directory_config)
            conn.sendall(response.encode('utf-8') + b"\r\n")
        elif os.path.isfile(path):
            with open(path, 'rb') as f:
                conn.sendfile(f)
        else:
            conn.sendall(b"3Error: Not found\r\n.\r\n")
        return

    if config.get("selectors", False):
        for sel in list(config["selectors"].keys()):
            if selector.startswith(sel):
                new_selector = selector[len(sel):] or '/'
                new_config = config["selectors"][sel]
                # Propagate host/port into nested config if absent
                if "host" not in new_config:
                    new_config["host"] = config.get("host", "localhost")
                if "port" not in new_config:
                    new_config["port"] = config.get("port", 70)
                make_response(new_selector, conn, new_config)
                return
        # Fallback
        if "default" in config["selectors"]:
            new_config = config["selectors"]["default"]
            if "host" not in new_config:
                new_config["host"] = config.get("host", "localhost")
            if "port" not in new_config:
                new_config["port"] = config.get("port", 70)
            make_response(selector, conn, new_config)
        else:
            conn.sendall(b"3Error: Bad config (no default selector)\r\n.\r\n")
        return

    conn.sendall(b"3Error: Not found\r\n.\r\n")

def recv_selector(conn, max_bytes=4096):
    data = b''
    while b'\n' not in data and len(data) < max_bytes:
        chunk = conn.recv(1024)
        if not chunk:
            break
        data += chunk
    line = data.decode('utf-8', errors='ignore')
    return line.replace('\r', '').split('\n', 1)[0].strip() or '/'

def start_gopher_server(config):    
    HOST = config.get('host')
    PORT = config.get('port')

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((HOST, PORT))
            s.listen(5)
            print(f"Gopher server running on port {PORT}...")
            while True:
                conn, addr = s.accept()
                with conn:
                    # Read exactly one selector line from the client (CRLF-terminated).
                    # Decoding ignores Telnet control bytes so it won’t crash
                    selector = recv_selector(conn)

                    # Attach host/port so downstream menu building uses the right address
                    serve_cfg = config["serve"]
                    if "host" not in serve_cfg:
                        serve_cfg["host"] = HOST
                    if "port" not in serve_cfg:
                        serve_cfg["port"] = PORT

                    make_response(selector, conn, serve_cfg)
                    
        except KeyboardInterrupt:
            print(f"Shutting down Gopher server on port {PORT}...")
        except Exception as e:
            print(f"Error on Gopher server on port {PORT}: {e}")