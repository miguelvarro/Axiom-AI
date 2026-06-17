# Axiom AI

Axiom AI is an AI-powered scientific search engine designed to help users find, analyze and synthesize evidence from academic literature.

Inspired by platforms such as Consensus, Axiom AI combines paper retrieval, evidence extraction, stance classification and AI-generated synthesis to provide concise and evidence-based answers to research questions.

---

## Features

### Scientific Literature Search
- Retrieve academic papers from OpenAlex.
- Rank results by relevance and citation impact.
- Deduplicate retrieved publications.

### Evidence Extraction
- Extract relevant evidence snippets from scientific papers.
- Highlight the most relevant findings for a given query.

### Stance Classification
Each paper is automatically classified as:

- Supporting
- Contradicting
- Neutral

This allows users to quickly understand the scientific consensus surrounding a topic.

### Consensus Analysis
- Aggregate evidence from multiple studies.
- Generate a consensus score.
- Display supporting, contradicting and neutral counts.

### AI Synthesis
Generate concise summaries that synthesize findings across multiple studies using a local Large Language Model.

### REST API
Axiom AI exposes its functionality through a FastAPI backend with interactive Swagger documentation.

---

## Technology Stack

### Backend
- Python
- FastAPI
- Uvicorn

### Information Retrieval
- OpenAlex API
- BM25 Ranking
- Semantic Re-ranking

### Artificial Intelligence
- Ollama
- Qwen 2.5 Instruct
- Evidence Aggregation Pipeline

### Frontend
- HTML
- CSS
- JavaScript

---

## Architecture

User Query
↓
OpenAlex Retrieval
↓
Ranking & Filtering
↓
Evidence Extraction
↓
Stance Classification
↓
Consensus Analysis
↓
LLM Synthesis
↓
Final Response

---

## Example Output

Question:

> Is breastfeeding beneficial for newborns?

Result:

- Supporting: 8
- Contradicting: 0
- Neutral: 2
- Confidence: 90%

AI Synthesis:

> Multiple studies consistently support the hypothesis that breastfeeding provides significant benefits for newborns.

---

## API Endpoints

### Health Check

```http
GET /health
```

### Search Papers

```http
POST /search
```

### Generate Evidence-Based Answer

```http
POST /answer
```

---

## Local Installation

### Clone Repository

```bash
git clone https://github.com/miguelvarro/axiom-ai.git
cd axiom-ai
```

### Create Virtual Environment

```bash
python -m venv venv
```

### Activate Environment

Windows:

```bash
venv\Scripts\activate
```

Linux:

```bash
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Start Backend

```bash
uvicorn src.main:app --reload
```

---

## Project Goals

The objective of Axiom AI is to improve access to scientific evidence by combining information retrieval techniques and local AI models into a single research assistant capable of providing transparent and evidence-based answers.

---

## Author

Miguel Ángel Vargas Rodríguez

Higher Technician in Multiplatform Application Development (DAM)

Valencia, Spain
