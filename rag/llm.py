import requests

class LLMAnalyzer:
    def __init__(self):
        self.url = "http://localhost:11434/api/generate"

    def analyze(self, query, context):
        prompt = f"""
            You are a log analysis expert.

            User Query:
            {query}

            Logs:
            {context}

            Return output in JSON:
            {{
            "root_cause": "",
            "affected_service": "",
            "suggested_fix": ""
            }}
            """

        response = requests.post(self.url, json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False
        })

        return response.json()["response"]