from typing import List

class MarineTextEmbedder:
    """Interface for text embeddings (supports sentence-transformers / OpenAI / local models)."""

    def embed_query(self, text: str) -> List[float]:
        # Placeholder vector hook ready for sentence-transformers
        return [0.0] * 384
