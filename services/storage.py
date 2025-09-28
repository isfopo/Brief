"""Summary storage service for local file system."""

import hashlib
import json
import gzip
import logging
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional

# Storage directory in user's home
STORAGE_DIR = Path.home() / ".brief" / "summaries"

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
    pass