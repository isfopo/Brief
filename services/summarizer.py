"""AI summarization service using Hugging Face transformers."""

import logging
import threading
import os
import torch
from transformers import AutoTokenizer, pipeline


# Configuration - can be overridden via environment variables
MODEL = os.getenv("SUMMARIZER_MODEL", "facebook/bart-large-cnn")
MAX_MODEL_TOKENS = int(os.getenv("MAX_MODEL_TOKENS", "15000"))
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


def summarize_text(text: str, max_length: int = 15000, min_length: int = 1000) -> str:
    """Summarize the given text using BART model.

    Args:
        text: The text to summarize
        max_length: Maximum length of the summary
        min_length: Minimum length of the summary

    Returns:
        The summarized text
    """
    logging.info(f"Summarize: Starting summarization of {len(text)} characters, target length: {min_length}-{max_length}")

    if not text.strip():
        logging.info("Summarize: Empty text provided, returning empty summary")
        return ""

    logging.info("Summarize: Getting tokenizer")
    tokenizer = get_tokenizer()
    tokens = tokenizer.encode(text)
    logging.info(f"Summarize: Encoded text into {len(tokens)} tokens")

    if len(tokens) > MAX_MODEL_TOKENS:
        logging.warning(f"Summarize: Text too long ({len(tokens)} tokens), truncating to {MAX_MODEL_TOKENS}")
        tokens = tokens[:MAX_MODEL_TOKENS]
        text = tokenizer.decode(tokens)
        logging.info(f"Summarize: Truncated text now has {len(text)} characters")

    # Adjust max_length based on input length to avoid unnecessary long outputs
    input_tokens = len(tokenizer.encode(text))  # Recalculate after potential truncation
    # Target summary length: 1/3 of input tokens, but cap at reasonable maximum
    suggested_max = min(max(input_tokens // 3, min_length + 20), 250)
    # Use the smaller of provided max_length and suggested max
    effective_max_length = min(max_length, suggested_max)
    if effective_max_length < max_length:
        logging.info(f"Summarize: Adjusted max_length from {max_length} to {effective_max_length} for {input_tokens} input tokens")

    logging.info("Summarize: Getting summarizer model")
    summarizer = get_summarizer()

    try:
        logging.info(f"Summarize: Running model with max_length={effective_max_length}, min_length={min_length}")
        start_time = __import__('time').time()
        summary = summarizer(text, max_length=effective_max_length, min_length=min_length, do_sample=False)
        end_time = __import__('time').time()
        summary_text = summary[0]['summary_text']
        logging.info(f"Summarize: Model completed in {end_time - start_time:.2f} seconds")
        logging.info(f"Summarize: Generated summary of {len(summary_text)} characters")
        return summary_text
    except Exception as e:
        logging.error(f"Summarize: Error during summarization: {e}")
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


def summarize_chunks(chunks: list[str], group_size: int = 5, progress_callback=None) -> str:
    """Generate hierarchical summary from text chunks.

    Uses a recursive approach: summarize chunks in groups, then summarize
    the group summaries, repeating until a single summary is produced.

    Args:
        chunks: List of text chunks to summarize
        group_size: Number of summaries to combine at each level

    Returns:
        Hierarchical summary of all chunks
    """
    logging.info(f"SummarizeChunks: Starting hierarchical summarization of {len(chunks)} chunks with group_size={group_size}")

    if not chunks:
        logging.info("SummarizeChunks: No chunks provided, returning empty")
        return ""

    # Base case: if few chunks, summarize directly
    if len(chunks) <= group_size:
        logging.info(f"SummarizeChunks: Base case - {len(chunks)} chunks <= {group_size}, summarizing directly")
        valid_chunks = [chunk for chunk in chunks if chunk.strip()]
        logging.info(f"SummarizeChunks: Found {len(valid_chunks)} non-empty chunks")

        summaries = []
        for i, chunk in enumerate(valid_chunks):
            logging.info(f"SummarizeChunks: Summarizing chunk {i+1}/{len(valid_chunks)} ({len(chunk)} chars)")
            if progress_callback:
                progress = 25 + (i / len(valid_chunks)) * 40  # 25-65%
                progress_callback(int(progress))
            summary = summarize_text(chunk)
            if summary:
                summaries.append(summary)
                logging.info(f"SummarizeChunks: Chunk {i+1} summary: {len(summary)} chars")

        if not summaries:
            logging.warning("SummarizeChunks: No valid summaries generated")
            return ""

        combined = " ".join(summaries)
        logging.info(f"SummarizeChunks: Combining {len(summaries)} summaries ({len(combined)} chars total)")
        if progress_callback:
            progress_callback(70)
        final_summary = summarize_text(combined)
        logging.info(f"SummarizeChunks: Final summary: {len(final_summary)} chars")
        if progress_callback:
            progress_callback(80)
        return final_summary

    # Recursive case: group chunks and summarize hierarchically
    logging.info(f"SummarizeChunks: Recursive case - processing {len(chunks)} chunks in groups of {group_size}")
    summaries = []
    total_groups = (len(chunks) + group_size - 1) // group_size  # Ceiling division

    for group_idx in range(0, len(chunks), group_size):
        group_num = group_idx // group_size + 1
        group = chunks[group_idx:group_idx + group_size]
        logging.info(f"SummarizeChunks: Processing group {group_num}/{total_groups} with {len(group)} chunks")

        if progress_callback:
            progress = 25 + (group_num / total_groups) * 50  # 25-75%
            progress_callback(int(progress))

        valid_group_chunks = [chunk for chunk in group if chunk.strip()]
        logging.info(f"SummarizeChunks: Group {group_num} has {len(valid_group_chunks)} non-empty chunks")

        group_summaries = []
        for i, chunk in enumerate(valid_group_chunks):
            logging.info(f"SummarizeChunks: Group {group_num}, summarizing chunk {i+1}/{len(valid_group_chunks)}")
            summary = summarize_text(chunk)
            if summary:
                group_summaries.append(summary)

        if group_summaries:
            combined_group = " ".join(group_summaries)
            logging.info(f"SummarizeChunks: Group {group_num}, combining {len(group_summaries)} summaries ({len(combined_group)} chars)")
            group_summary = summarize_text(combined_group)
            summaries.append(group_summary)
            logging.info(f"SummarizeChunks: Group {group_num} final summary: {len(group_summary)} chars")

    logging.info(f"SummarizeChunks: Generated {len(summaries)} group summaries, recursing")
    if progress_callback:
        progress_callback(85)
    # Recurse on the summaries
    return summarize_chunks(summaries, group_size, progress_callback)


def summarize_book(text: str, progress_callback=None) -> str:
    """Summarize a full book text using chunking and hierarchical summarization.

    Args:
        text: The full text of the book
        progress_callback: Optional callback function to report progress (percentage)

    Returns:
        Hierarchical summary of the book
    """
    logging.info(f"SummarizeBook: Starting book summarization of {len(text)} characters")

    if progress_callback:
        progress_callback(5)  # Starting

    start_time = __import__('time').time()
    chunks = chunk_text(text)
    chunk_time = __import__('time').time()
    logging.info(f"SummarizeBook: Chunking completed in {chunk_time - start_time:.2f} seconds, created {len(chunks)} chunks")

    if progress_callback:
        progress_callback(20)  # Chunking complete

    if not chunks:
        logging.warning("SummarizeBook: No chunks created, returning empty summary")
        return ""

    summary = summarize_chunks(chunks, progress_callback=progress_callback)
    end_time = __import__('time').time()
    logging.info(f"SummarizeBook: Book summarization completed in {end_time - start_time:.2f} seconds")
    logging.info(f"SummarizeBook: Final summary length: {len(summary)} characters")

    if progress_callback:
        progress_callback(95)  # Summarization complete

    return summary
