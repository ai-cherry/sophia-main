"""Vector Database Integration for semantic search."""
from __future__ import annotations

import logging
from typing import Any, Dict, Iterable, List

import pinecone
import weaviate
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class VectorIntegration:
    """Handle embedding generation and search across Pinecone and Weaviate."""

    MODEL_NAME = "all-MiniLM-L6-v2"
    INDEX_NAME = "sophia-payready"
    DIMENSIONS = 1536

    def __init__(self, pinecone_key: str, weaviate_url: str, weaviate_key: str) -> None:
        self.model = SentenceTransformer(self.MODEL_NAME)
        pinecone.init(api_key=pinecone_key, environment="us-west1-gcp")
        self.pinecone = pinecone.Index(self.INDEX_NAME)
        self.weaviate = weaviate.Client(url=weaviate_url, auth_client_secret=weaviate.AuthApiKey(weaviate_key))
        logger.info("VectorIntegration initialized")

    def embed(self, texts: Iterable[str]) -> List[List[float]]:
        return self.model.encode(list(texts)).tolist()

    def index(self, items: Iterable[Dict[str, Any]]) -> None:
        vectors = [(str(i["id"]), self.embed([i["text"]])[0], i) for i in items]
        if vectors:
            self.pinecone.upsert(vectors)
            self.weaviate.batch.add_data_object_batch(
                [v for _, _, v in vectors], "SophiaPayReady"
            )
        logger.debug("Indexed %s items", len(vectors))

    def search(self, text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        vec = self.embed([text])[0]
        pine = self.pinecone.query(vector=vec, top_k=top_k, include_metadata=True)
        wea = (
            self.weaviate.query.get("SophiaPayReady", ["text"])\
            .with_near_vector({"vector": vec})\
            .with_limit(top_k)\
            .do()
        )
        results = [*pine.get("matches", []), *wea.get("data", {}).get("Get", {}).get("SophiaPayReady", [])]
        return results
