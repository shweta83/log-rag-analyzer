"""
embedder.py — Embedding and vector store module
-------------------------------------------------
Converts chunk dicts into vectors using OpenAI embeddings,
builds an in-memory FAISS index, and retrieves relevant chunks by query.

Each chunk dict: { "text": str, "source": str }

Used by main.py — not intended to be run directly.
"""

import os
import numpy as np
import faiss
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM   = 1536
BATCH_SIZE      = 20


def _get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """
    Call the OpenAI embeddings API for a batch of texts.
    Returns a list of embedding vectors in the same order as input.
    """
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts
    )
    # API guarantees results are in the same order as input
    return [item.embedding for item in response.data]


def embed_chunks(chunks: list[dict]) -> np.ndarray:
    """
    Embed all chunks and return as a float32 numpy array.

    Accepts: list of chunk dicts [{ "text": str, "source": str }, ...]
    Returns: np.ndarray of shape (n_chunks, EMBEDDING_DIM)

    Processes in batches to stay within API rate limits.
    """
    texts      = [chunk["text"] for chunk in chunks]
    embeddings = []

    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i: i + BATCH_SIZE]
        batch_embeddings = _get_embeddings_batch(batch)
        embeddings.extend(batch_embeddings)
        print(f"  Embedded {min(i + BATCH_SIZE, len(texts))}/{len(texts)} chunks...")

    return np.array(embeddings, dtype="float32")


def build_faiss_index(embeddings: np.ndarray) -> faiss.IndexFlatL2:
    """
    Build an in-memory FAISS index from embedding vectors.

    Uses L2 (Euclidean) distance — appropriate for OpenAI embeddings
    which are not normalised by default.

    Returns a FAISS index ready for similarity search.
    """
    index = faiss.IndexFlatL2(EMBEDDING_DIM)
    index.add(embeddings)
    print(f"  FAISS index built — {index.ntotal} vectors indexed.")
    return index


def retrieve(
    query: str,
    index: faiss.IndexFlatL2,
    chunks: list[dict],
    top_k: int = 5
) -> list[dict]:
    """
    Find the top-k most relevant chunks for a given query.

    Accepts: plain-English query string
    Returns: list of chunk dicts [{ "text": str, "source": str }, ...]
             in order of relevance (most relevant first)

    These chunks are passed directly to llm_client.analyze_logs().
    """
    query_embedding = np.array(
        [_get_embeddings_batch([query])[0]],
        dtype="float32"
    )
    distances, indices = index.search(query_embedding, top_k)

    return [
        chunks[i]
        for i in indices[0]
        if i < len(chunks)
    ]