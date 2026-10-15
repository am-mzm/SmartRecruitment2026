"""Isolated functional test of SmartRecruitment's actual search functions.

Run from the SmartRecruitment venv in Process_Upload_Functions.
Creates only an ephemeral in-memory Chroma collection; no Azure access or writes.
"""
import ast
import asyncio
import contextlib
import io
import math
import os
import re
import sys
import time
from pathlib import Path

import chromadb
import numpy as np
from flashtext import KeywordProcessor
from rank_bm25 import BM25Okapi
from sklearn.metrics.pairwise import cosine_similarity

from candidate_geographic_search import filter_eligible_candidates

SOURCE = (Path(__file__).resolve().parents[1] / "vector_bm25_search_revised.py")
assert SOURCE.is_file(), f"Search source not found: {SOURCE}"
code = SOURCE.read_text(encoding="utf-8-sig")
tree = ast.parse(code)

# Compile exact function bodies from the working search module, without importing
# heavyweight production sentence-transformer models or changing production code.
required = {
    "initialize_bm25_from_chromadb", "query_by_word",
    "compile_list_per_keyword", "present_list", "vector_rank_list",
    "build_geographic_chroma_filter", "_process_resumes_unlocked",
}
functions = [
    node for node in tree.body
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    and node.name in required
]
found = {node.name for node in functions}
assert found == required, f"Missing source functions: {required - found}"

# Fixed synthetic model, so the semantic similarity is deterministic. Real
# ChromaDB vector queries and actual BM25Okapi scoring still execute.
class DeterministicModel:
    def encode(self, text):
        return np.array([0.2, 0.5, 0.8], dtype=np.float32)


def custom_tokenize(text, synonyms):
    return re.findall(r"[a-z0-9]+", str(text).lower())


def parse_keywords_and_weights(items):
    return [key for key, _ in items], dict(items)


# Return one matching job title to exercise the exact-keyword supplemental path.
# Actual production title-filtering behavior is outside this test's scope.
def filter_job_title(filtered, title, compare_all_titles, similarity_threshold=0.5):
    return filtered["metadatas"][:1]


class AsyncCollectionAdapter:
    def __init__(self, collection):
        self.collection = collection
        self.query_calls = 0
        self.get_calls = 0

    async def query(self, **kwargs):
        self.query_calls += 1
        return self.collection.query(**kwargs)

    async def get(self, **kwargs):
        self.get_calls += 1
        return self.collection.get(**kwargs)


# Uses the actual project geographic eligibility function against real Chroma
# metadata, but a fixed test center rather than a live GeoNames city lookup.
async def build_geographic_candidate_pool(collection, *, city, state, country, radius_miles):
    if not any((city, state, country)):
        return None
    records = await collection.get(include=["metadatas"])
    selected, distances = filter_eligible_candidates(
        records["metadatas"],
        city=city, state=state, country=country,
        center=(42.27756, -83.74088), radius_miles=radius_miles,
    )
    return {
        "filenames": {m["filename"] for m in selected},
        "distances": distances,
        "total_scanned": len(records["metadatas"]),
    }


namespace = {
    "model": DeterministicModel(), "np": np, "os": os,
    "time": time, "re": re, "math": math,
    "cosine_similarity": cosine_similarity,
    "BM25Okapi": BM25Okapi, "KeywordProcessor": KeywordProcessor,
    "custom_tokenize": custom_tokenize,
    "parse_keywords_and_weights": parse_keywords_and_weights,
    "filter_job_title": filter_job_title,
    "build_geographic_candidate_pool": build_geographic_candidate_pool,
    "resume_filenames": [], "resume_texts": [],
}
exec(compile(ast.Module(body=functions, type_ignores=[]), str(SOURCE), "exec"), namespace)

# Real ChromaDB operations, confined to an ephemeral instance.
client = chromadb.EphemeralClient()
collection = client.create_collection(name="smartrec_geo_complete_pipeline")

# Filename, state, country, latitude, longitude, experience, resume text.
rows = [
    ("AnnArbor.pdf", "MI", "USA", 42.2808, -83.7430, 7,
     "python python snowflake architecture analytics"),
    ("Toledo.pdf", "OH", "USA", 41.6528, -83.5379, 9,
     "python cloud warehousing implementation"),
    ("DetroitJunior.pdf", "MI", "USA", 42.3314, -83.0458, 3,
     "python software development"),
    ("Chicago.pdf", "IL", "USA", 41.8781, -87.6298, 8,
     "python python data modeling"),
    ("Windsor.pdf", "ON", "Canada", 42.3149, -83.0364, 7,
     "snowflake data engineering pipelines"),
    ("Flint.pdf", "MI", "USA", 43.0125, -83.6875, 7,
     "python data pipeline automation"),
    ("Cleveland.pdf", "OH", "USA", 41.4993, -81.6944, 8,
     "oracle finance reporting"),
    ("GrandRapids.pdf", "MI", "USA", 42.9634, -85.6681, 7,
     "java backend microservices"),
    ("LondonOntario.pdf", "ON", "Canada", 42.9849, -81.2453, 8,
     "java architecture integration"),
    ("UnknownLocation.pdf", "MI", "USA", None, None, 7,
     "python python ai architect"),
]
metadatas = []
for filename, state, country, lat, lon, years, document in rows:
    m = {
        "filename": filename, "candidate_city": {"AnnArbor.pdf": "Ann Arbor", "DetroitJunior.pdf": "Detroit", "GrandRapids.pdf": "Grand Rapids", "LondonOntario.pdf": "London", "UnknownLocation.pdf": ""}.get(filename, filename.removesuffix(".pdf")), "candidate_state": state,
        "candidate_country": country, "candidate_name": filename,
        "years_of_experience": years, "most_recent_job_title": "Data Architect",
        "core_technologies": "Python, Snowflake", "location": state,
    }
    if lat is not None:
        m["candidate_latitude"] = lat
        m["candidate_longitude"] = lon
    metadatas.append(m)

collection.add(
    ids=[r[0] for r in rows],
    documents=[r[6] for r in rows],
    metadatas=metadatas,
    embeddings=[[0.2, 0.5, 0.8]] * len(rows),
)
assert collection.count() == len(rows)
adapter = AsyncCollectionAdapter(collection)
os.environ.setdefault("FIRST_POOL_VALUE", "1000")

async def main():
    params = dict(
        collection=adapter, compare_all_titles=False,
        keywords_with_weights=[("python", 1.0)], boolean_synonym={},
        job_title="Data Architect", pool_value=1000,
        min_experience=5, max_experience=10, top_n=20,
        candidate_city="Ann Arbor", candidate_state="MI",
        candidate_country="USA", radius_miles=200,
    )
    with contextlib.redirect_stdout(io.StringIO()) as captured:
        results = await namespace["_process_resumes_unlocked"](**params)

    names = [r["filename"] for r in results]
    expected_keyword_matches = {"AnnArbor.pdf", "Toledo.pdf", "Flint.pdf"}
    assert set(names) == expected_keyword_matches, (names, captured.getvalue())
    assert set(namespace["resume_filenames"]).issubset({
        "AnnArbor.pdf", "Toledo.pdf", "Windsor.pdf", "Flint.pdf",
        "Cleveland.pdf", "GrandRapids.pdf", "LondonOntario.pdf"
    }), namespace["resume_filenames"]
    assert "Chicago.pdf" not in names
    assert "DetroitJunior.pdf" not in names
    assert "UnknownLocation.pdf" not in names
    assert all(r["experience_years"] >= 5 for r in results)
    assert all(0 <= r["distance_miles"] <= 200 for r in results)
    assert [r["rank"] for r in results] == list(range(1, len(results) + 1))
    assert all(r["relevance_score"] > 0 for r in results)
    assert adapter.query_calls >= 1

    scores = namespace["bm25"].get_scores(["python"])
    assert len(scores) == len(namespace["resume_filenames"])

    # Geographic empty pool: the real orchestrator must short-circuit.
    before = adapter.query_calls
    empty_params = dict(params, radius_miles=0.01)
    # Ann Arbor candidate coordinates are ~0.3 mi from the test center.
    with contextlib.redirect_stdout(io.StringIO()):
        empty = await namespace["_process_resumes_unlocked"](**empty_params)
    assert empty == [], empty
    assert adapter.query_calls == before

    # Country and exact-city integration checks using the actual search pipeline.
    scenarios = [
        ("Canada only", dict(candidate_city="", candidate_state="",
                             candidate_country="Canada", radius_miles=None), "Canada"),
        ("USA only", dict(candidate_city="", candidate_state="",
                          candidate_country="USA", radius_miles=None), "USA"),
        ("Any", dict(candidate_city="", candidate_state="",
                     candidate_country="Any", radius_miles=None), "Any"),
        ("Exact Ann Arbor", dict(candidate_city="Ann Arbor", candidate_state="MI",
                                 candidate_country="USA", radius_miles=None), "AnnArbor.pdf"),
    ]

    country_by_filename = {
        row[0]: row[2] for row in rows
    }

    for label, location_args, expected in scenarios:
        test_params = dict(params, **location_args)
        with contextlib.redirect_stdout(io.StringIO()):
            scenario_results = await namespace["_process_resumes_unlocked"](**test_params)

        scenario_names = [result["filename"] for result in scenario_results]

        if expected == "Canada":
            assert all(country_by_filename[name] == "Canada" for name in scenario_names), scenario_names
        elif expected == "USA":
            assert all(country_by_filename[name] == "USA" for name in scenario_names), scenario_names
        elif expected == "Any":
            assert all(country_by_filename[name] in {"Canada", "USA"} for name in scenario_names), scenario_names
        else:
            assert all(name == expected for name in scenario_names), scenario_names

        print(f"{label}: PASS ({len(scenario_names)} results)")

    print("COUNTRY AND EXACT-CITY INTEGRATION: PASS")
    print("=== ACTUAL PIPELINE + EPHEMERAL CHROMADB ===")
    print("Synthetic records:", collection.count())
    print("Returned candidates:", names)
    print("Real ChromaDB semantic query: PASS")
    print("Actual two-stage semantic/BM25 functions: PASS")
    print("Exact-keyword supplemental matching: PASS")
    print("200-mile geographic and experience restrictions: PASS")
    print("Cross-state inclusion and missing-location exclusion: PASS")
    print("Sequential ranks and distance_miles fields: PASS")
    print("Empty-pool early exit: PASS")
    print("PRODUCTION CHROMADB: NOT CONNECTED")
    print("APPLICATION FILES: UNCHANGED")

asyncio.run(main())
