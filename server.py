import socket
import os

from menu import make_menu
from config import get_default_root_object

def make_response(selector, conn, config):
    ''' Make and send a Gopher response based on the config and selector '''

    if config.get("root", False):
        if type(config["root"]) is str:
            directory_config = get_default_root_object(config["root"]) # Convert to full config
        else:
            directory_config = config["root"]
        path = os.path.join(directory_config.get("directory"), selector.lstrip('/'))

        if os.path.isdir(path):
            response = make_menu(path)
            conn.sendall(response.encode('utf-8') + b"\r\n")
        elif os.path.isfile(path):
            with open(path, 'rb') as f:
                conn.sendfile(f)
        else:
            conn.sendall(b"3Error: Not found\r\n.\r\n")
    elif config.get("selectors", False):
        config_selectors = list(config["selectors"].keys())
        for sel in config_selectors:
            if selector.startswith(sel):
                new_selector = selector[len(sel):] # Remove matched selector from start
                new_config = config["selectors"][sel]
                make_response(new_selector, conn, new_config) # Recursive
                return
        # If no selector matched, use default
        if "default" in config["selectors"]:
            new_config = config["selectors"]["default"]
            make_response(selector, conn, new_config)
        else:
            conn.sendall(b"3Error: Bad config (no default selector)\r\n.\r\n")
    else:
        conn.sendall(b"3Error: Not found\r\n.\r\n")


def start_gopher_server(config):
    HOST = config.get('host') # Mandatory
    PORT = config.get('port') # Mandatory

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((HOST, PORT))
            s.listen(5)
            print(f"Gopher server running on port {PORT}...")
            while True:
                conn, addr = s.accept()
                with conn:
                    selector = conn.recv(1024).decode('utf-8').strip()
                    if not selector: # Empty selector defaults to root
                        selector = '/'
                    make_response(selector, conn, config["serve"])
        except KeyboardInterrupt:
            print(f"Shutting down Gopher server on port {PORT}...")
        except Exception as e:
            print(f"Error on Gopher server on port {PORT}: {e}")