import socket
import os

from menu import make_menu

HOST = '0.0.0.0'
PORT = 70
ROOT = './serve'

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen(5)
    print(f"Gopher server running on port {PORT}...")
    try:
        while True:
            conn, addr = s.accept()
            with conn:
                selector = conn.recv(1024).decode('utf-8').strip()
                if not selector:
                    selector = '/'
                path = os.path.join(ROOT, selector.lstrip('/'))
                if os.path.isdir(path):
                    response = make_menu(path)
                    conn.sendall(response.encode('utf-8') + b"\r\n")
                elif os.path.isfile(path):
                    with open(path, 'rb') as f:
                        conn.sendfile(f)
                else:
                    conn.sendall(b"3Error: Not found\r\n.\r\n")
    except KeyboardInterrupt: # Graceful shutdown on Ctrl+C, closing socket
        print("Server stopped by user...")
    except Exception as e:
        print(f"An error occurred: {e}")