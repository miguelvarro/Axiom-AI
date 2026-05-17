import httpx

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:32b-instruct"

prompt = (
    "You are classifying a scientific paper. "
    "Return ONLY valid JSON with exactly these keys: stance, strength, evidence, rationale. "
    "Question: Does creatine improve strength? "
    "Paper: Creatine supplementation significantly increased muscle strength (p<0.01)."
)

body = {
    "model": MODEL,
    "stream": False,
    "format": "json",
    "options": {"temperature": 0.1},
    "messages": [{"role": "user", "content": prompt}],
}

with httpx.Client(timeout=120) as c:
    r = c.post(OLLAMA_URL, json=body)
    print("status:", r.status_code)
    print("raw:", repr(r.text[:1000]))
    if r.status_code == 200:
        data = r.json()
        content = (data.get("message") or {}).get("content") or ""
        print("content:", repr(content[:500]))
