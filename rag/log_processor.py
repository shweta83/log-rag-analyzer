import json

def process_log(line):
    log = json.loads(line)

    return {
        "text": log["message"],
        "service": log["service"],
        "level": log["level"],
        "trace_id": log["trace_id"],
        "timestamp": log["timestamp"]
    }