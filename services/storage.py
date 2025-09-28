"""Summary storage service for local file system."""

import hashlib
import json
import gzip
import logging
import threading
from pathlib import Path
from collections import OrderedDict
from dataclasses import dataclass, asdict
from typing import Optional

# Storage directory in user's home
STORAGE_DIR = Path.home() / ".brief" / "summaries"

# Global cache for loaded summaries (LRU with max size)
MAX_CACHE_SIZE = 100
_cache = OrderedDict()
_cache_lock = threading.Lock()

@dataclass
class SummaryData:
    """Data structure for book summary storage."""
    title: str
    author: str
    path: str  # Original book file path
    timestamp: str  # ISO 8601 timestamp
    summary: str  # Full summary text

def get_file_path(book_path: str) -> Path:
    """Generate unique file path for a book based on MD5 hash of its path.

    Args:
        book_path: Absolute path to the book file

    Returns:
        Path to the compressed summary file
    """
    book_hash = hashlib.md5(book_path.encode('utf-8')).hexdigest()
    return STORAGE_DIR / f"{book_hash}.summary.json.gz"

def save_summary(metadata: dict, summary: str) -> None:
    """Save summary data to compressed JSON file.

    Args:
        metadata: Dict with title, author, path, timestamp
        summary: Summary text

    Raises:
        ValueError: If metadata is invalid
    """
    try:
        title = metadata['title']
        author = metadata['author']
        path = metadata['path']
        timestamp = metadata['timestamp']
    except KeyError as e:
        raise ValueError(f"Missing metadata field: {e}")

    data = SummaryData(title=title, author=author, path=path, timestamp=timestamp, summary=summary)
    file_path = get_file_path(path)

    # Ensure directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)

    data_dict = asdict(data)
    json_str = json.dumps(data_dict, ensure_ascii=False)

    try:
        with gzip.open(file_path, 'wt', encoding='utf-8') as f:
            f.write(json_str)
    except Exception as e:
        logging.error(f"Failed to save summary for {path}: {e}")
        raise

def load_summary(book_path: str) -> Optional[SummaryData]:
    """Load summary data from compressed JSON file.

    Args:
        book_path: Path to the book file

    Returns:
        SummaryData if found, None otherwise
    """
    if not book_path or not isinstance(book_path, str):
        return None

    with _cache_lock:
        if book_path in _cache:
            _cache.move_to_end(book_path)
            return _cache[book_path]

    file_path = get_file_path(book_path)
    if not file_path.exists():
        return None

    try:
        with gzip.open(file_path, 'rt', encoding='utf-8') as f:
            json_str = f.read()
        data_dict = json.loads(json_str)
        data = SummaryData(**data_dict)
        with _cache_lock:
            _cache[book_path] = data
            _cache.move_to_end(book_path)
            if len(_cache) > MAX_CACHE_SIZE:
                _cache.popitem(last=False)
        return data
    except (OSError, json.JSONDecodeError, gzip.BadGzipFile, TypeError) as e:
        logging.error(f"Failed to load summary for {book_path}: {e}")
        return None


def clear_cache(book_path: Optional[str] = None) -> None:
    """Clear cache entries.

    Args:
        book_path: Specific path to clear, or None to clear all
    """
    with _cache_lock:
        if book_path:
            _cache.pop(book_path, None)
        else:
            _cache.clear()