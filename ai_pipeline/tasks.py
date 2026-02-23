from ai_pipeline.celery_app import app


@app.task(name="ai_pipeline.tasks.translate_text")
def translate_text(text: str, source_lang: str = "ja", target_lang: str = "en") -> dict:
    """Translate text using Qwen via DashScope."""
    # TODO: Phase 2 implementation
    return {
        "status": "not_implemented",
        "source_lang": source_lang,
        "target_lang": target_lang,
        "original_length": len(text),
    }


@app.task(name="ai_pipeline.tasks.summarize_collection")
def summarize_collection(collection_id: int) -> dict:
    """Generate an AI summary for a collection."""
    # TODO: Phase 2 implementation
    return {"status": "not_implemented", "collection_id": collection_id}
