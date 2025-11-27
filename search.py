"""
Search helpers for the Gopher server.

Provides:
- parse_search_selector: extracts a search query from /search selector variants.
- search_files: finds filenames or text content containing a query (case-insensitive).
- make_search_results: builds a Gopher menu with matches (or a 'No matches' line).
"""

import os
from menu import determine_item_type


def parse_search_selector(selector):
    """
    Extract the search query only from '/search<TAB>term'.
    Any other form is considered invalid (returns None).
    """
    if not selector.startswith('/search'):
        return None
    remainder = selector[len('/search'):]
    if not remainder or not remainder.startswith('\t'):
        return None
    q = remainder[1:].strip()
    return q or None

def search_files(base_dir, query, recursive):
    """
    Scan directory for matches on filename OR file text content (UTF-8, errors ignored).
    Case-insensitive search.
    Args:
      base_dir (str): root directory to search
      query (str): search term
      recursive (bool): include subdirectories if True
    Returns:
      list[str]: relative paths of matching files
    """
    matches = []
    q = query.lower()
    for root, dirs, files in os.walk(base_dir):
        for fname in files:
            rel = os.path.relpath(os.path.join(root, fname), base_dir)
            full = os.path.join(root, fname)
            if q in fname.lower():
                matches.append(rel); continue
            try:
                with open(full, 'r', encoding='utf-8', errors='ignore') as f:
                    if q in f.read().lower():
                        matches.append(rel)
            except Exception:
                pass
        if not recursive:
            break
    return matches

def make_search_results(base_dir, host, port, query, recursive):
    """
    Build a Gopher menu (CRLF lines + final '.') for search results.
    Lines are:
      info header
      either 'No matches found.' or one line per result with inferred type + selector
      terminating '.'
    Args:
      base_dir (str): directory to search
      host (str): host to embed in menu lines
      port (int): port to embed in menu lines
      query (str): search term
      recursive (bool): recurse into subdirectories if True
    Returns:
      str: complete Gopher menu for the search results
    """
    lines = [f"iSearch results for: {query}\tfake\t{host}\t{port}"]
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