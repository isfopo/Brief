"""AI summarization service using Hugging Face transformers."""

import logging
import threading
import os
import torch
from transformers import AutoTokenizer, pipeline


# Configuration - can be overridden via environment variables
MODEL = os.getenv("SUMMARIZER_MODEL", "facebook/bart-large-cnn")
MAX_MODEL_TOKENS = int(os.getenv("MAX_MODEL_TOKENS", "1024"))
USE_SMALL_MODEL = os.getenv("USE_SMALL_MODEL", "false").lower() == "true"

# Use smaller model for testing if requested
if USE_SMALL_MODEL:
    MODEL = "sshleifer/distilbart-cnn-6-6"

# Force CPU usage to avoid MPS/GPU issues
os.environ["CUDA_VISIBLE_DEVICES"] = ""
torch.set_default_device('cpu')

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
                logging.info(f"Loading summarization model: {MODEL}")
                start_time = __import__('time').time()
                _summarizer = pipeline("summarization", model=MODEL, device='cpu')
                load_time = __import__('time').time() - start_time
                logging.info(f"Model loaded successfully in {load_time:.2f} seconds")
            except Exception as e:
                logging.error(f"Failed to load summarization model: {e}")
                raise RuntimeError(f"Failed to load summarization model: {e}")
    return _summarizer


def get_tokenizer():
    """Get or create the tokenizer."""
    global _tokenizer
    with _model_lock:
        if _tokenizer is None:
            try:
                logging.info(f"Loading tokenizer: {MODEL}")
                start_time = __import__('time').time()
                _tokenizer = AutoTokenizer.from_pretrained(MODEL)
                load_time = __import__('time').time() - start_time
                logging.info(f"Tokenizer loaded successfully in {load_time:.2f} seconds")
            except Exception as e:
                logging.error(f"Failed to load tokenizer: {e}")
                raise RuntimeError(f"Failed to load tokenizer: {e}")
    return _tokenizer


def preload_model():
    """Pre-download and cache the model and tokenizer.

    Call this function early in the application startup to avoid
    delays when summarization is first requested.
    """
    try:
        logging.info("Preloading summarization model and tokenizer...")
        start_time = __import__('time').time()

        # Preload both model and tokenizer
        get_summarizer()
        get_tokenizer()

        total_time = __import__('time').time() - start_time
        logging.info(f"Model preloading completed in {total_time:.2f} seconds")
        return True
    except Exception as e:
        logging.error(f"Failed to preload model: {e}")
        return False


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
        logging.info("Chunking: Empty text provided")
        return []

    logging.info(f"Chunking: Starting tokenization of {len(text)} characters")
    tokenizer = get_tokenizer()
    tokens = tokenizer.encode(text, add_special_tokens=False)
    logging.info(f"Chunking: Encoded into {len(tokens)} tokens")

    chunks = []
    start = 0
    chunk_num = 1

    while start < len(tokens):
        logging.info(f"Chunking: Creating chunk {chunk_num}, starting at token {start}")

        # Try to take up to max_tokens
        end = min(start + max_tokens, len(tokens))
        logging.info(f"Chunking: Initial end position: {end}")

        # If the chunk would be too small and we're not at the end, extend it
        if end - start < min_tokens and end < len(tokens):
            old_end = end
            end = min(start + min_tokens, len(tokens))
            logging.info(f"Chunking: Extended chunk from {old_end} to {end} to meet min_tokens")

        chunk_tokens = tokens[start:end]
        chunk_text = tokenizer.decode(chunk_tokens, skip_special_tokens=True)
        chunks.append(chunk_text)

        logging.info(f"Chunking: Created chunk {chunk_num} with {len(chunk_tokens)} tokens ({len(chunk_text)} chars)")

        start = end
        chunk_num += 1

    logging.info(f"Chunking: Completed, created {len(chunks)} chunks")
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
        logging.info("No chunks provided")
        return ""

    logging.info(f"Summarizing {len(chunks)} chunks")

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
    logging.info("Chunking complete")
    return summarize_chunks(chunks)
