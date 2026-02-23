"""Summarization module using Qwen via DashScope SDK.

Generates editorial summaries for collections, brand profiles,
and fashion trend analysis.
"""

from tokyoradar_shared.config import settings


class Summarizer:
    def __init__(self):
        self.api_key = settings.DASHSCOPE_API_KEY

    def summarize_collection(self, collection_data: dict) -> str:
        """Generate an editorial summary for a fashion collection."""
        # TODO: Phase 2 — integrate dashscope SDK
        raise NotImplementedError

    def summarize_brand(self, brand_data: dict) -> str:
        """Generate a brand profile summary."""
        # TODO: Phase 2 — integrate dashscope SDK
        raise NotImplementedError
