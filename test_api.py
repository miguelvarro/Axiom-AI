import httpx
import json

BASE = "http://localhost:8000"

# Test 1: health
print("=" * 50)
print("TEST 1: Health check")
r = httpx.get(f"{BASE}/health")
print(f"Status: {r.status_code}")
print(f"Response: {r.text}")

# Test 2: answer
print()
print("=" * 50)
print("TEST 2: Answer endpoint")
payload = {"q": "Does creatine improve strength?", "k": 3}
r = httpx.post(f"{BASE}/answer", json=payload, timeout=300)
print(f"Status: {r.status_code}")

if r.status_code == 200:
    data = r.json()
    print()
    print(f"  q:               {data.get('q')}")
    print(f"  conclusion:      {str(data.get('conclusion',''))[:100]}...")
    print(f"  confidence:      {data.get('confidence')}")
    print(f"  dominant_stance: {data.get('dominant_stance')}")
    print(f"  consensus_label: {data.get('consensus_label')}")
    print(f"  consensus_score: {data.get('consensus_score')}")
    print(f"  top_papers:      {len(data.get('top_papers') or [])} papers")
    print(f"  supporting_ev:   {len(data.get('supporting_evidence') or [])} items")
    print(f"  contradicting:   {len(data.get('contradicting_evidence') or [])} items")
    print(f"  neutral_ev:      {len(data.get('neutral_evidence') or [])} items")
    print(f"  methodology:     {data.get('methodology')}")

    # Campos que necesita el frontend
    required = [
        "q", "conclusion", "confidence", "dominant_stance",
        "consensus_label", "confidence_numeric", "consensus_score",
        "top_papers", "supporting_evidence", "contradicting_evidence",
        "neutral_evidence", "contradictions_present", "contradiction_summary",
        "methodology",
    ]
    print()
    print("Campos del frontend:")
    for f in required:
        present = f in data
        val = data.get(f)
        status = "✅" if present else "❌ FALTA"
        print(f"  {status}  {f}: {repr(val)[:60] if present else ''}")
else:
    print(f"ERROR: {r.text[:500]}")