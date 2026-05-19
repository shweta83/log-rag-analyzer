"""
Log RAG Analyzer — Test Failure Analyzer
--------------------------------------
1. Reads all log files from a fixed logs/ directory
2. Chunks + embeds them into a FAISS vector store
3. Runs a default query and prints the test failure analysis
 
 
Jenkins integration:
  Add as a post-build step:
    python main.py --logs-dir $WORKSPACE/logs
"""
import argparse
import os
import sys
from pathlib import Path
 
import numpy as np
 
from rag.chunker import chunk_log_file
from rag.embedder import embed_chunks, build_faiss_index, retrieve
from rag.llm_client import analyze_logs_streaming


# **************************Configuration**************************
LOGS_DIR = "logs"                          # fixed logs directory
LOG_EXTENSIONS = [".log", ".txt"]          # file types to pick up
TOP_K = 5                                  # number of chunks to retrieve
DEFAULT_QUERY = (
    "Summarize all errors and failures found in these logs. "
    "For each error, identify the root cause and suggest a fix."
)
# **************************Configuration**************************


def collect_log_files(logs_dir: str) -> list[Path]:
    """Return all log files found in the logs directory."""
    dir_path = Path(logs_dir)
    if not dir_path.exists():
        print(f"ERROR: Logs directory not found: '{logs_dir}'")
        print("Create the directory and add log files to it, or pass --logs-dir <path>")
        sys.exit(1)
 
    files = []
    for ext in LOG_EXTENSIONS:
        files.extend(dir_path.glob(f"**/*{ext}"))  # recursive — picks up subdirs too
 
    if not files:
        print(f"ERROR: No {'/'.join(LOG_EXTENSIONS)} files found in '{logs_dir}'")
        sys.exit(1)
 
    return sorted(files)
 
def ingest_all(log_files: list[Path], strategy: str = "auto") -> tuple:
    """
    Chunk and embed all log files into a single in-memory FAISS index.
    Returns (index, all_chunks) ready for querying.
    No files written to disk — index lives only for this run.
    """
    all_chunks = []
 
    print(f"\n{'─' * 50}")
    print(f"  STEP 1 — Ingesting {len(log_files)} log file(s)")
    print(f"{'─' * 50}")
 
    for i, log_file in enumerate(log_files, 1):
        print(f"\n[{i}/{len(log_files)}] {log_file.name}")
        chunks = chunk_log_file(str(log_file), strategy=strategy)
        if chunks:
            all_chunks.extend(chunks)
            print(f"  → {len(chunks)} chunks extracted")
        else:
            print(f"  → skipped (no chunks extracted)")
 
    if not all_chunks:
        print("\nERROR: No chunks extracted from any log file.")
        sys.exit(1)
 
    print(f"\nTotal chunks across all files: {len(all_chunks)}")
 
    print(f"\n{'─' * 50}")
    print(f"  STEP 2 — Embedding chunks")
    print(f"{'─' * 50}")
    embeddings = embed_chunks(all_chunks)
 
    print(f"\n{'─' * 50}")
    print(f"  STEP 3 — Building vector store")
    print(f"{'─' * 50}")
    index = build_faiss_index(embeddings)
 
    return index, all_chunks
 
def run_query(query: str, index, all_chunks: list[str], top_k: int = TOP_K):
    """
    Retrieve relevant chunks and run the LLM analysis.
    """
    print(f"\n{'─' * 50}")
    print(f"  STEP 4 — Running analysis")
    print(f"{'─' * 50}")
    print(f"\nQuery: {query}\n")
 
    relevant_chunks = retrieve(query, index, all_chunks, top_k=top_k)
 
    if not relevant_chunks:
        print("No relevant chunks found for this query.")
        sys.exit(0)
 
    print(f"Retrieved {len(relevant_chunks)} relevant chunk(s). Sending to GPT-4o...\n")
    analyze_logs_streaming(query, relevant_chunks)


def check_env():
    """Verify OPENAI_API_KEY is set before making any API calls."""
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY environment variable is not set.")
        print("  export OPENAI_API_KEY=sk-...")
        sys.exit(1)


def print_banner(logs_dir: str, log_files: list[Path]):
    print(f"""
╔══════════════════════════════════════════════════════╗
║               AI Log Analyzer                        ║
╚══════════════════════════════════════════════════════╝
  Logs directory : {logs_dir}
  Files found    : {len(log_files)}
""")
    for f in log_files:
        print(f"  • {f.name}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Automatically analyze all logs in a directory using RAG",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
Examples:
  python main.py
  python main.py --logs-dir /var/log/jenkins/jobs/my-job/builds/42/log
  python main.py --query "Were there any authentication failures?"
  python main.py --logs-dir logs/ --strategy fixed --top-k 8
 
Jenkins post-build step:
  python main.py --logs-dir $WORKSPACE/logs
        """
    )
 
    parser.add_argument("--logs-dir", type=str, default=LOGS_DIR,
                        help=f"Directory containing log files (default: '{LOGS_DIR}')")
    parser.add_argument("--query", "-q", type=str, default=DEFAULT_QUERY,
                        help="Override the default analysis query")
    parser.add_argument("--strategy", type=str, default="auto",
                        choices=["auto", "entry", "fixed"],
                        help="Chunking strategy (default: auto)")
    parser.add_argument("--top-k", type=int, default=TOP_K,
                        help=f"Number of chunks to retrieve (default: {TOP_K})")
 
    args = parser.parse_args()
 
    check_env()

 # ── Pipeline ──────────────────────────────────────────────────────────────
    log_files = collect_log_files(args.logs_dir)
    print_banner(args.logs_dir, log_files)
 
    index, all_chunks = ingest_all(log_files, strategy=args.strategy)
    run_query(args.query, index, all_chunks, top_k=args.top_k)
 
    print(f"\n{'─' * 50}")
    print("  Analysis complete.")
    print(f"{'─' * 50}\n")
 
 
if __name__ == "__main__":
    main()
    