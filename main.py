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

# print("Sample processed logs:\n")
# for log in logs[:5]:
#     print(log)

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
# for chunk in chunks:
#     error_logs = tuple(
#         log["text"] for log in chunk["logs"] if log["level"] == "ERROR"
#     )

#     if error_logs not in seen_errors:
#         seen_errors.add(error_logs)
#         unique_chunks.append(chunk)

# # Step 4: Create embeddings
# embeddings = []
# texts = []

# for chunk in unique_chunks:
#     error_logs = [log["text"] for log in chunk["logs"] if log["level"] == "ERROR"]

#     text = f"""
#     Service Flow:
#     {chunk['content']}

#     Errors:
#     {"; ".join(error_logs)}

#     Trace ID: {chunk['trace_id']}
#     """
#     emb = get_embedding(text)

#     embeddings.append(emb)
#     texts.append(chunk)

# # Initialize FAISS
# vector_db = VectorStore(dim=len(embeddings[0]))

# # Store embeddings
# vector_db.add(embeddings, texts)

# # Test query
# query = "payment service error 401 unauthorized"
# query_embedding = get_embedding(query)

# results = vector_db.search(query_embedding)

# print("\nSearch Results:\n")
# for r in results:
#     print(r["content"])
#     print("------")
