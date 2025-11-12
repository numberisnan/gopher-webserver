import threading

from config import load_config
from server import start_gopher_server

if __name__ == "__main__":
    config = load_config("config.json")

    threads = []
    for server_cfg in config: # Main object is a list of server configs
        t = threading.Thread(
            target=start_gopher_server,
            args=(server_cfg,),
            daemon=True
        )
        t.start()
        threads.append(t)

    print("All Gopher servers are running. Press Ctrl+C to stop.")
    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        print("Stopping all servers...")
