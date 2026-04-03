# scripts/generate_logs.py

import json
import random
from datetime import datetime, timedelta
import uuid

services = ["auth-service", "payment-service", "order-service", "ui-frontend"]

errors = [
    ("401 Unauthorized", "AUTH_FAILURE"),
    ("Timeout while calling payment API", "TIMEOUT"),
    ("Database connection refused", "DB_ERROR"),
    ("503 Service Unavailable", "SERVICE_DOWN"),
]

def generate_trace():
    trace_id = str(uuid.uuid4())
    logs = []

    base_time = datetime.utcnow()

    flow = [
        ("ui-frontend", "User clicked checkout"),
        ("auth-service", "Validating token"),
        ("payment-service", "Processing payment"),
        ("order-service", "Creating order"),
    ]

    # Inject random failure
    failure = random.choice(errors)

    for i, (service, msg) in enumerate(flow):
        log = {
            "timestamp": (base_time + timedelta(seconds=i)).isoformat(),
            "service": service,
            "level": "INFO",
            "message": msg,
            "trace_id": trace_id
        }

        logs.append(log)

        # Inject failure in middle
        if i == random.randint(1, 3):
            logs.append({
                "timestamp": (base_time + timedelta(seconds=i)).isoformat(),
                "service": service,
                "level": "ERROR",
                "message": failure[0],
                "trace_id": trace_id
            })
            break

    return logs


def generate_logs(n=1000):
    with open("logs.json", "w") as f:
        for _ in range(n):
            trace_logs = generate_trace()
            for log in trace_logs:
                f.write(json.dumps(log) + "\n")


if __name__ == "__main__":
    generate_logs(2000)