import os
import socket
import tempfile
import threading
import time
import unittest

from server import start_gopher_server

def wait_for_port(host, port, timeout=2.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.2):
                return True
        except (ConnectionRefusedError, OSError):
            time.sleep(0.05)
    return False

def free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]

def gopher_request(host, port, selector='/'):
    with socket.create_connection((host, port), timeout=2) as s:
        s.sendall((selector + '\r\n').encode('utf-8'))
        chunks = []
        while True:
            data = s.recv(4096)
            if not data:
                break
            chunks.append(data)
    return b''.join(chunks)

class TestGopherServer(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        base = self.tmpdir.name

        os.makedirs(os.path.join(base, 'sub'), exist_ok=True)
        with open(os.path.join(base, 'hello.txt'), 'w', encoding='utf-8') as f:
            f.write('hello world\n')
        with open(os.path.join(base, 'sub', 'info.txt'), 'w', encoding='utf-8') as f:
            f.write('some info\nhello there')

        self.host = '127.0.0.1'
        self.port = free_port()
        self.config = {
            'host': self.host,
            'port': self.port,
            'serve': {
                'root': {
                    'directory': base,
                    'search': True,
                    'search_recursive': True,
                }
            }
        }

        self.stop = threading.Event()
        self.thread = threading.Thread(
            target=start_gopher_server,
            args=(self.config, self.stop),
            daemon=True
        )
        self.thread.start()
        self.assertTrue(wait_for_port(self.host, self.port), 'server did not start')

    def tearDown(self):
        self.stop.set()
        # poke server so accept() returns once
        try:
            with socket.create_connection((self.host, self.port), timeout=0.2):
                pass
        except Exception:
            pass
        self.thread.join(timeout=2)
        self.tmpdir.cleanup()

    def test_root_menu_lists_files(self):
        text = gopher_request(self.host, self.port, '/').decode('utf-8', errors='ignore')
        self.assertIn('\r\n.\r\n', text)    # proper Gopher termination
        self.assertIn('hello.txt', text)    # menu shows file

    def test_search_finds_results(self):
        text = gopher_request(self.host, self.port, '/search\thello').decode('utf-8', errors='ignore')
        self.assertIn('Search results for', text)
        self.assertIn('hello.txt', text)          # filename match
        self.assertIn('sub/info.txt', text)       # content match (recursive)

    def test_fetch_file_bytes(self):
        data = gopher_request(self.host, self.port, '/hello.txt')
        self.assertIn(b'hello world', data)