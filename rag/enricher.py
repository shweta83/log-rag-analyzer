def enrich_log(log):
    message = log["text"].lower()
    log["tags"] = []

    if log["level"] == "ERROR":
        if "401" in message:
            log["error_type"] = "AUTH_FAILURE"
            log["tags"].append("auth")
        elif "timeout" in message:
            log["error_type"] = "TIMEOUT"
            log["tags"].append("timeout")
        elif "database" in message or "connection refused" in message:
             log["error_type"] = "DB_ERROR"
             log["tags"].append("db")
        else:
            log["error_type"] = "UNKNOWN_ERROR"
    else:
        log["error_type"] = None  # IMPORTANT CHANGE

    return log