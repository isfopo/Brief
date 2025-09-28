"""Tests for the summarizer service."""

import pytest
from services.summarizer import chunk_text, summarize_text, summarize_chunks, summarize_book


class TestChunkText:
    """Test chunk_text function."""

    def test_empty_text(self):
        """Test chunking empty text."""
        assert chunk_text("") == []

    def test_short_text(self):
        """Test chunking text shorter than max_tokens."""
        text = "This is a short text."
        chunks = chunk_text(text, max_tokens=100)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_long_text(self):
        """Test chunking long text."""
        # Create text longer than max_tokens
        long_text = "This is a test sentence. " * 200  # Should be > 1000 tokens
        chunks = chunk_text(long_text, max_tokens=100, min_tokens=50)
        assert len(chunks) > 1
        # Check that chunks are reasonable
        for chunk in chunks:
            assert len(chunk) > 0


class TestSummarizeText:
    """Test summarize_text function."""

    def test_empty_text(self):
        """Test summarizing empty text."""
        assert summarize_text("") == ""

    def test_short_text(self):
        """Test summarizing short text."""
        text = "This is a test sentence for summarization."
        summary = summarize_text(text)
        assert isinstance(summary, str)
        assert len(summary) > 0
        # Summary should be shorter or equal
        assert len(summary) <= len(text)

    def test_long_text(self):
        """Test summarizing long text."""
        long_text = "This is a test sentence. " * 50
        summary = summarize_text(long_text)
        assert isinstance(summary, str)
        assert len(summary) > 0


class TestSummarizeChunks:
    """Test summarize_chunks function."""

    def test_empty_chunks(self):
        """Test summarizing empty chunks."""
        assert summarize_chunks([]) == ""

    def test_single_chunk(self):
        """Test summarizing single chunk."""
        chunks = ["This is a test chunk."]
        summary = summarize_chunks(chunks)
        assert isinstance(summary, str)
        assert len(summary) > 0

    def test_multiple_chunks(self):
        """Test summarizing multiple chunks."""
        chunks = [
            "This is the first chunk with some content.",
            "This is the second chunk with different content.",
            "This is the third chunk to test hierarchical summarization."
        ]
        summary = summarize_chunks(chunks)
        assert isinstance(summary, str)
        assert len(summary) > 0

    def test_many_chunks(self):
        """Test hierarchical summarization with many chunks."""
        chunks = [f"Chunk number {i} with some content." for i in range(10)]
        summary = summarize_chunks(chunks, group_size=3)
        assert isinstance(summary, str)
        assert len(summary) > 0


class TestSummarizeBook:
    """Test summarize_book function."""

    def test_empty_book(self):
        """Test summarizing empty book."""
        assert summarize_book("") == ""

    def test_short_book(self):
        """Test summarizing short book."""
        text = "This is a short book with minimal content."
        summary = summarize_book(text)
        assert isinstance(summary, str)
        assert len(summary) > 0

    def test_long_book(self):
        """Test summarizing long book."""
        long_text = "This is a sentence in the book. " * 1000  # Long text
        summary = summarize_book(long_text)
        assert isinstance(summary, str)
        assert len(summary) > 0
