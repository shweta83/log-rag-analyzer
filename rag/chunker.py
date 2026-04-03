from collections import defaultdict

def chunk_logs(logs):
    grouped = defaultdict(list)

    for log in logs:
        trace_id = log.get("trace_id", "no_trace")
        grouped[trace_id].append(log)

    chunks = []

    for trace_id, group in grouped.items():
        # Sort logs by timestamp
        group = sorted(group, key=lambda x: x["timestamp"])


        # Extract error
        error_logs = [l["text"] for l in group if l["level"] == "ERROR"]
        error_text = error_logs[0] if error_logs else "No error"
        
        # Build content
        combined_text = "\n".join([l["text"] for l in group])

        content = f"Error:\n{error_text}\n\nFlow:\n{combined_text}"

        chunks.append({
            "trace_id": trace_id,
            "content": content,
            "error": error_text,
            "logs": group
        })

    return chunks

