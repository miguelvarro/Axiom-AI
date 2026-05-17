import orjson
from ai_consensus_clone.core.domain.paper import Paper
from ai_consensus_clone.core.enrichment.fulltext_service import FullTextService

INPUT = "data/processed/openalex_creatine_oa_fulltext.jsonl"
OUTPUT = "data/processed/openalex_creatine_oa_fulltext_v2.jsonl"

fts = FullTextService()

with open(INPUT, "rb") as f_in, open(OUTPUT, "wb") as f_out:
    for line in f_in:
        if not line.strip():
            continue

        obj = orjson.loads(line)
        paper = Paper(**obj)

        paper = fts.enrich_paper(paper)

        f_out.write(orjson.dumps(paper.model_dump()) + b"\n")

print("DONE")
