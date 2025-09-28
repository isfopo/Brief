"""AI summarization service using Hugging Face transformers."""

import logging
import threading
from transformers import AutoTokenizer, pipeline


MODEL = "facebook/bart-large-cnn"
MAX_MODEL_TOKENS = 1024

# Global instances for reuse
_summarizer = None
_tokenizer = None
_model_lock = threading.Lock()


def get_summarizer():
    """Get or create the summarization pipeline."""
    global _summarizer
    with _model_lock:
        if _summarizer is None:
            try:
                _summarizer = pipeline("summarization", model=MODEL)
            except Exception as e:
                raise RuntimeError(f"Failed to load summarization model: {e}")
    return _summarizer


def get_tokenizer():
    """Get or create the tokenizer."""
    global _tokenizer
    with _model_lock:
        if _tokenizer is None:
            _tokenizer = AutoTokenizer.from_pretrained(MODEL)
    return _tokenizer


def summarize_text(text: str, max_length: int = 150, min_length: int = 50) -> str:
    """Summarize the given text using BART model.

    Args:
        text: The text to summarize
        max_length: Maximum length of the summary
        min_length: Minimum length of the summary

    Returns:
        The summarized text
    """
    if not text.strip():
        return ""

    tokenizer = get_tokenizer()
    tokens = tokenizer.encode(text)
    if len(tokens) > MAX_MODEL_TOKENS:
        tokens = tokens[:MAX_MODEL_TOKENS]
        text = tokenizer.decode(tokens)

    summarizer = get_summarizer()
    try:
        summary = summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)
        return summary[0]['summary_text']
    except Exception as e:
        logging.error(f"Error summarizing text: {e}")
        return ""


def chunk_text(text: str, max_tokens: int = 900, min_tokens: int = 500) -> list[str]:
    """Split text into chunks based on token count.

    Args:
        text: The text to chunk
        max_tokens: Maximum tokens per chunk
        min_tokens: Minimum tokens per chunk (except for last chunk)

    Returns:
        List of text chunks
    """
    if not text.strip():
        return []

    tokenizer = get_tokenizer()
    tokens = tokenizer.encode(text, add_special_tokens=False)

    chunks = []
    start = 0

    while start < len(tokens):
        # Try to take up to max_tokens
        end = min(start + max_tokens, len(tokens))

        # If the chunk would be too small and we're not at the end, extend it
        if end - start < min_tokens and end < len(tokens):
            end = min(start + min_tokens, len(tokens))

        chunk_tokens = tokens[start:end]
        chunk_text = tokenizer.decode(chunk_tokens, skip_special_tokens=True)
        chunks.append(chunk_text)

        start = end

    return chunks


def summarize_chunks(chunks: list[str], group_size: int = 5) -> str:
    """Generate hierarchical summary from text chunks.

    Uses a recursive approach: summarize chunks in groups, then summarize
    the group summaries, repeating until a single summary is produced.

    Args:
        chunks: List of text chunks to summarize
        group_size: Number of summaries to combine at each level

    Returns:
        Hierarchical summary of all chunks
    """
    if not chunks:
        return ""

    # Base case: if few chunks, summarize directly
    if len(chunks) <= group_size:
        # Summarize each chunk
        summaries = [summarize_text(chunk) for chunk in chunks if chunk.strip()]
        if not summaries:
            return ""
        combined = " ".join(summaries)
        return summarize_text(combined)

    # Recursive case: group chunks and summarize hierarchically
    summaries = []
    for i in range(0, len(chunks), group_size):
        group = chunks[i:i + group_size]
        group_summaries = [summarize_text(chunk) for chunk in group if chunk.strip()]
        if group_summaries:
            combined_group = " ".join(group_summaries)
            group_summary = summarize_text(combined_group)
            summaries.append(group_summary)

    # Recurse on the summaries
    return summarize_chunks(summaries, group_size)


def summarize_book(text: str) -> str:
    """Summarize a full book text using chunking and hierarchical summarization.

    Args:
        text: The full text of the book

    Returns:
        Hierarchical summary of the book
    """
    chunks = chunk_text(text)
    return summarize_chunks(chunks)
