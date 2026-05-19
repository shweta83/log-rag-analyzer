"""
llm_client.py — LLM analysis module
--------------------------------------
Takes retrieved chunk dicts and produces a structured plain-English
root cause analysis using GPT-4o.

Each chunk dict: { "text": str, "source": str }

Used by main.py — not intended to be run directly.
"""

import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

LLM_MODEL   = "gpt-4o"
TEMPERATURE = 0.2   # low = factual, grounded output; avoid hallucinated line numbers

SYSTEM_PROMPT = """You are an expert DevOps and software quality engineer 
specialising in log analysis, root cause investigation, and CI/CD pipelines.

You will be given log chunks retrieved from one or more log files.
Each chunk is labelled with the file it came from.

Your job is to:
1. Identify all errors and failures across all provided log files
2. Determine the root cause of each failure
3. Explain each clearly in plain English
4. Suggest a concrete fix or next step

Always structure your response exactly as follows:

SUMMARY:
<one paragraph overview of what failed and across which files>

ERRORS FOUND:
<for each distinct error:>
  • File: <source filename>
    Error: <error description>
    Root cause: <why it happened>
    Suggested fix: <concrete actionable steps>

If the logs do not contain enough information to determine a root cause,
say so clearly rather than guessing. Never fabricate file paths, line numbers,
or error details that are not present in the provided log chunks."""


def _build_user_prompt(query: str, chunks: list[dict]) -> str:
    """
    Build the user prompt by combining the query with retrieved chunks.
    Each chunk is labelled with its source filename so the LLM can
    attribute errors to the correct log file.
    """
    formatted_chunks = "\n\n---\n\n".join(
        f"[Source: {chunk['source']}]\n{chunk['text']}"
        for chunk in chunks
    )

    return f"""Query: {query}

Retrieved log chunks (with source file labels):

{formatted_chunks}

Based only on the log chunks above, answer the query."""


def analyze_logs(query: str, chunks: list[dict]) -> str:
    """
    Analyze retrieved log chunks and return a structured analysis string.

    Accepts:
        query  — the user's question or the default summary query
        chunks — list of chunk dicts [{ "text": str, "source": str }, ...]

    Returns:
        Plain-English analysis string (ROOT CAUSE / DETAILS / SUGGESTED FIX)

    Use this when you need the result as a string (e.g. writing to a file,
    sending to JIRA, or further processing).
    """
    if not chunks:
        return "No relevant log chunks were retrieved. Check your logs/ directory and query."

    response = client.chat.completions.create(
        model=LLM_MODEL,
        temperature=TEMPERATURE,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": _build_user_prompt(query, chunks)}
        ]
    )
    return response.choices[0].message.content


def analyze_logs_streaming(query: str, chunks: list[dict]) -> None:
    """
    Stream the GPT-4o analysis token by token to stdout.

    Accepts:
        query  — the user's question or the default summary query
        chunks — list of chunk dicts [{ "text": str, "source": str }, ...]

    Use this in main.py for terminal output — much better UX than
    waiting for the full response before printing anything.
    """
    if not chunks:
        print("No relevant log chunks were retrieved. Check your logs/ directory and query.")
        return

    stream = client.chat.completions.create(
        model=LLM_MODEL,
        temperature=TEMPERATURE,
        stream=True,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": _build_user_prompt(query, chunks)}
        ]
    )

    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            print(delta, end="", flush=True)

    print()  # newline after streaming completes