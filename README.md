# log-rag-analyzer
RAG pipeline for intelligent log analysis

## What problem does this solve?
When a CI pipeline fails, engineers spend 15–30 min manually reading 
logs to find the root cause. This tool does it in seconds.

## How it works (architecture)
Log file → chunking → embedding → vector store → LLM → plain English summary

## Tech stack
- Python 3.11
- OpenAI API
- FAISS
- RAG architecture

## Demo


## How to run it
pip install -r requirements.txt
export OPENAI_API_KEY=...

## Sample output

