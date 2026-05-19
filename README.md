# AI-Powered Log Analyzer

A retrieval-augmented generation (RAG) tool that automatically ingests log files, 
finds the most relevant error patterns, and produces a plain-English root cause 
analysis using GPT-4o.

Built as a practical AI engineering project by an SDET to reduce manual log 
triage time after CI/CD pipeline failures.

---

## The Problem

When a CI pipeline fails, engineers spend 15–30 minutes manually reading hundreds 
of log lines to find the root cause. This tool does it in seconds.

---

## How It Works

```
logs/                    ← drop your log files here
  │
  ▼
┌─────────────┐     ┌──────────────┐     ┌──────────────────┐
│   Chunker   │────▶│   Embedder   │────▶│   Vector Store   │
│             │     │              │     │   (FAISS)        │
│ splits logs │     │ converts to  │     │                  │
│ into blocks │     │ vectors via  │     │ stores embeddings│
│             │     │ OpenAI API   │     │ in memory        │
└─────────────┘     └──────────────┘     └────────┬─────────┘
                                                   │
                                              retrieval
                                                   │
                                                   ▼
                                         ┌──────────────────┐
                                         │   LLM Client     │
                                         │   (GPT-4o)       │
                                         │                  │
                                         │ root cause +     │
                                         │ suggested fix    │
                                         └──────────────────┘
```

**Chunker** — splits raw log files into meaningful blocks, keeping multi-line 
entries (e.g. stack traces) grouped with their parent log line.

**Embedder** — converts each chunk into a vector using OpenAI's 
`text-embedding-3-small` model, then stores them in a FAISS index for fast 
similarity search.

**Retriever** — given a query, finds the top-K most semantically relevant 
log chunks — not just keyword matches.

**LLM Client** — sends the retrieved chunks to GPT-4o with a structured prompt 
that returns ROOT CAUSE, DETAILS, and SUGGESTED FIX every time.

---

## Tech Stack

| Component       | Technology                        |
|----------------|-----------------------------------|
| Language        | Python 3.11+                      |
| Embeddings      | OpenAI `text-embedding-3-small`   |
| Vector Store    | FAISS (local, no server needed)   |
| LLM             | OpenAI GPT-4o                     |
| Architecture    | RAG (Retrieval-Augmented Generation) |

---

## Setup

**1. Clone the repo**
```bash
git clone https://github.com/shweta83/log-rag-analyzer.git
cd log-rag-analyzer
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Set your OpenAI API key**
```bash
cp .env.example .env
# Edit .env and add your key
export OPENAI_API_KEY=sk-...
```

**4. Add log files**
```bash
# Drop your .log or .txt files into the logs/ directory
cp /path/to/your/app.log logs/
```

**5. Run**
```bash
python main.py
```

---

## Usage

```bash
# Analyze logs in the default logs/ directory
python main.py

# Analyze logs from a custom directory
python main.py --logs-dir /path/to/logs

# Ask a specific question instead of the default summary
python main.py --query "Were there any authentication failures?"

# Retrieve more context for complex log files
python main.py --top-k 8

# Use fixed-line chunking for unstructured log formats
python main.py --strategy fixed
```

---

## Example Output

**Input logs:**
```
2024-01-15 14:32:10 WARN  - DB connection pool exhausted (max: 10)
2024-01-15 14:32:11 ERROR - NullPointerException in PaymentService.java:142
    at com.app.PaymentService.processPayment(PaymentService.java:142)
    at com.app.OrderController.checkout(OrderController.java:87)
2024-01-15 14:33:01 ERROR - Timeout waiting for DB connection after 30s
```

**Tool output:**
```
ROOT CAUSE:
The database connection pool was exhausted, causing a NullPointerException
in PaymentService when it attempted to acquire a connection that wasn't available.

DETAILS:
The connection pool hit its maximum limit of 10 concurrent connections,
likely due to a spike in checkout requests. When PaymentService tried to
process a payment at line 142, the connection object returned was null,
triggering the NullPointerException. The 30-second timeout error confirms
the pool remained saturated after the initial failure.

SUGGESTED FIX:
1. Increase the DB connection pool size in application.properties
   (spring.datasource.hikari.maximum-pool-size=20)
2. Add null-check and retry logic in PaymentService.java around line 142
3. Add connection pool monitoring/alerting to catch exhaustion before it causes failures
```

---

## Jenkins Integration

Add this as a post-build **Execute Shell** step in your Jenkins job:

```bash
cd $WORKSPACE
pip install -r requirements.txt
python main.py --logs-dir $WORKSPACE/logs
```

Store `OPENAI_API_KEY` as a Jenkins **Secret Text** credential and inject it 
into the build environment — never hardcode it in the Jenkinsfile.

---


---

## Future Improvements

- [ ] Add an enricher module to inject service metadata and severity tags 
      into chunks before LLM inference
- [ ] Stream logs directly from Jenkins API instead of reading from disk
- [ ] Add a LangGraph agent that detects failures, retrieves relevant code, 
      and suggests a fix autonomously
- [ ] Support real-time log watching with automatic re-ingestion on file change
- [ ] Add a web UI for non-terminal users

---

## Author

**Shweta Singh** — Senior SDET