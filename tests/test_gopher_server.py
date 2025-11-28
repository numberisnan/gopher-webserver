"""
Integration-style tests for the Gopher server.

Tests:
- Server lifecycle: start on a free localhost port in a background thread; clean shutdown via stop event and a final 'poke' connection.
- Root menu: ensures directory listing renders, includes expected file, and uses proper Gopher termination (CRLF + final '.' line).
- Search feature: verifies a query returns both filename matches and content matches when recursive search is enabled.
- File retrieval: requesting '/hello.txt' yields the raw bytes (not a menu).
Environment notes:
- Uses a temporary directory so tests are isolated and portable (Linux/WSL friendly).
- Uses IPv4 127.0.0.1 and a wait loop instead of fixed sleeps for robustness.
"""

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

    # Verifies root directory menu renders, lists files, and ends with the Gopher .\r\n terminator
    def test_root_menu_lists_files(self):
        text = gopher_request(self.host, self.port, '/').decode('utf-8', errors='ignore')
        self.assertIn('\r\n.\r\n', text)    # proper Gopher termination
        self.assertIn('hello.txt', text)    # menu shows file

    # Confirms search returns both a filename match (hello.txt) and a recursive content match
    def test_search_finds_results(self):
        text = gopher_request(self.host, self.port, '/search\thello').decode('utf-8', errors='ignore')
        self.assertIn('Search results for', text)
        self.assertIn('hello.txt', text)          # filename match
        self.assertIn('sub/info.txt', text)       # content match (recursive)

    # Ensures fetching a file selector returns raw file bytes (not a menu)
    def test_fetch_file_bytes(self):
        data = gopher_request(self.host, self.port, '/hello.txt')
        self.assertIn(b'hello world', data)
    
    # Checks missing selectors return a gopher error menu and proper .\r\n termination
    def test_not_found_selector(self):
        text = gopher_request(self.host, self.port, '/nope').decode('utf-8', errors='ignore')
        self.assertIn('3Error: Not found', text)
        self.assertTrue(text.endswith('\r\n.\r\n'))
    
    # Validates /search with no query returns usage/help lines and terminates correctly
    def test_search_help_when_no_query(self):
        text = gopher_request(self.host, self.port, '/search').decode('utf-8', errors='ignore')
        self.assertIn('Search usage:', text)
        self.assertIn('/search<TAB>term', text)
        self.assertTrue(text.endswith('\r\n.\r\n'))
    
    # Asserts disabling recursion omits matches in subdirectories while still finding root-level hits
    def test_search_non_recursive_excludes_subdir_matches(self):
        # Flip recursion off and restart the server for this test
        self.stop.set()
        try:
            with socket.create_connection((self.host, self.port), timeout=0.2):
                pass
        except Exception:
            pass
        self.thread.join(timeout=2)

        self.config['serve']['root']['search_recursive'] = False
        self.stop = threading.Event()
        self.thread = threading.Thread(
            target=start_gopher_server,
            args=(self.config, self.stop),
            daemon=True
        )
        self.thread.start()
        self.assertTrue(wait_for_port(self.host, self.port), 'server did not restart')

        text = gopher_request(self.host, self.port, '/search\thello').decode('utf-8', errors='ignore')
        self.assertIn('Search results for', text)
        self.assertIn('hello.txt', text)          # filename match in root
        self.assertNotIn('sub/info.txt', text)    # subdir match should be excluded

    # Verifies search result menus end with the \r\n.\r\n gopher terminator
    def test_search_results_terminate_with_period(self):
            text = gopher_request(self.host, self.port, '/search\thello').decode('utf-8', errors='ignore')
            self.assertTrue(text.endswith('\r\n.\r\n'))
    
    def test_longest_prefix_routing(self):
        # Reconfigure server with overlapping selectors
        self.stop.set()
        try:
            with socket.create_connection((self.host, self.port), timeout=0.2):
                pass
        except Exception:
            pass
        self.thread.join(timeout=2)

        # Build nested selector tree
        base = self.tmpdir.name
        extra_dir = os.path.join(base, 'extra')
        os.makedirs(extra_dir, exist_ok=True)
        with open(os.path.join(extra_dir, 'x.txt'), 'w') as f:
            f.write('x')

        self.config['serve'] = {
            'selectors': {
                '/doc': {'root': {'directory': base}},
                '/docs': {'root': {'directory': extra_dir}}
            },
            'host': self.host,
            'port': self.port
        }

        self.stop = threading.Event()
        self.thread = threading.Thread(target=start_gopher_server, args=(self.config, self.stop), daemon=True)
        self.thread.start()
        self.assertTrue(wait_for_port(self.host, self.port), 'server did not restart')

        text = gopher_request(self.host, self.port, '/docs').decode('utf-8', errors='ignore')
        self.assertIn('x.txt', text)          # Should route to /docs (longer) not /doc
