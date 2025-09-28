"""AI summarization service using Hugging Face transformers."""

from transformers import AutoTokenizer, pipeline


MODEL = "facebook/bart-large-cnn"

# Global summarizer instance for reuse
_summarizer = None


def get_summarizer():
    """Get or create the summarization pipeline."""
    global _summarizer
    if _summarizer is None:
        try:
            _summarizer = pipeline("summarization", model=MODEL)
        except Exception as e:
            raise RuntimeError(f"Failed to load summarization model: {e}")
    return _summarizer


def summarize_text(text: str, max_length: int = 150, min_length: int = 50) -> str:
    """Summarize the given text using BART model.

    Args:
        text: The text to summarize
        max_length: Maximum length of the summary
        min_length: Minimum length of the summary

    Returns:
        The summarized text

    Raises:
        ValueError: If summarization fails
    """
    if not text.strip():
        return ""

    summarizer = get_summarizer()
    try:
        summary = summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)
        return summary[0]['summary_text']
    except Exception as e:
        raise ValueError(f"Summarization failed: {e}")


def chunk_text(text: str, max_tokens: int = 1000, min_tokens: int = 500) -> list[str]:
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

    tokenizer = AutoTokenizer.from_pretrained(MODEL)
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
