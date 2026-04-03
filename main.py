from rag.log_processor import process_log
from rag.enricher import enrich_log
from rag.chunker import chunk_logs
from rag.embedder import Embedder
from rag.vector_store import VectorStore
from rag.llm import LLMAnalyzer


logs = []
unique_chunks = []
seen_errors = set()

with open("logs.json", "r") as f:
    for line in f:
        processed = process_log(line)
        enriched = enrich_log(processed)
        logs.append(enriched)

chunks = chunk_logs(logs)

# print("\nSample chunk:\n")
# print(chunks[0])

embedder = Embedder()

texts = [chunk["content"] for chunk in chunks]

embeddings = embedder.embed(texts)


# Initialize
vector_store = VectorStore(dim=384)

# Add data
vector_store.add(embeddings, texts)

# Query
query = "authentication failure"
query_embedding = embedder.embed([query])

results = vector_store.search(query_embedding, k=3)

print("\nSearch Results:\n")
for r in results:
    print(r)
    print("------")


llm = LLMAnalyzer()

context = "\n\n".join(results[:3])

analysis = llm.analyze(query, context)

print("\nFinal Analysis:\n")
print(analysis)
