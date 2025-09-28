"""AI summarization service using Hugging Face transformers."""

from transformers import pipeline

# Global summarizer instance for reuse
_summarizer = None


def get_summarizer():
    """Get or create the summarization pipeline."""
    global _summarizer
    if _summarizer is None:
        try:
            _summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
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