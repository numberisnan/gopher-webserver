import socket
import os
import ssl

from menu import make_menu
from config import get_default_root_object
from search import parse_search_selector, make_search_results

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
        keys = list(config["selectors"].keys())
        # Collect all prefix matches
        matches = [k for k in keys if selector.startswith(k)]
        if matches:
            best = max(matches, key=len)  # longest prefix
            new_selector = selector[len(best):] or '/'
            new_config = config["selectors"][best]
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
    """
    Read a single Gopher selector line from the socket.
    - Accumulates bytes until newline or max_bytes.
    - Decodes ignoring control/negotiation bytes (Telnet safe).
    - Normalizes CRLF and returns '/' if empty.
    """
    data = b''
    while b'\n' not in data and len(data) < max_bytes:
        chunk = conn.recv(1024)
        if not chunk:
            break
        data += chunk
    line = data.decode('utf-8', errors='ignore')
    return line.replace('\r', '').split('\n', 1)[0].strip() or '/'

def start_gopher_server(config, stop_event=None):    
    HOST = config.get('host')
    PORT = config.get('port')

    # TLS config
    use_tls = bool(config.get('tls', False))
    tls_certfile = config.get('tls_certfile')
    tls_keyfile = config.get('tls_keyfile')

    context = None
    if use_tls:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certfile=tls_certfile, keyfile=tls_keyfile)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((HOST, PORT))
            s.listen(5)
            print(f"Gopher server running on port {PORT}...")
            while stop_event is None or not stop_event.is_set():
                try:
                    conn, addr = s.accept()

                    # wrap connection in TLS if enabled
                    if use_tls:
                        conn = context.wrap_socket(conn, server_side=True)

                except socket.timeout:
                    continue
                with conn:
                    # Read exactly one selector line from the client
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