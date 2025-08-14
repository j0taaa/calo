import json
import os
import re
from dataclasses import dataclass
from typing import List, Dict, Any

import fitz  # PyMuPDF
import requests
from rank_bm25 import BM25Okapi
from tqdm import tqdm

DATA_DIR = "/workspace/data"
PDF_PATH = os.path.join(DATA_DIR, "hcip_cloud_service_solutions_architect_v3.pdf")
INDEX_DIR = os.path.join(DATA_DIR, "pdf_index")
INDEX_JSON = os.path.join(INDEX_DIR, "index.json")


@dataclass
class RetrievedChunk:
    chunk_id: int
    score: float
    text: str


def ensure_dirs() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(INDEX_DIR, exist_ok=True)


def download_pdf(url: str, dest_path: str = PDF_PATH, chunk_size: int = 1 << 14) -> str:
    ensure_dirs()
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
        return dest_path
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        with open(dest_path, "wb") as f, tqdm(total=total, unit="B", unit_scale=True, desc="Downloading PDF") as pbar:
            for chunk in r.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))
    return dest_path


def extract_text_from_pdf(pdf_path: str = PDF_PATH) -> List[str]:
    doc = fitz.open(pdf_path)
    pages: List[str] = []
    for page in tqdm(doc, desc="Extracting text"):
        pages.append(page.get_text())
    return pages


def chunk_text(text: str, chunk_size: int = 1500, overlap: int = 200) -> List[str]:
    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = max(end - overlap, 0)
    return chunks


def tokenize(text: str) -> List[str]:
    return re.findall(r"\w+", text.lower())


def build_index(pages: List[str]) -> Dict[str, Any]:
    # Flatten pages into chunks
    all_chunks: List[str] = []
    for page_text in pages:
        all_chunks.extend(chunk_text(page_text))

    index_payload = {
        "chunks": [
            {"id": i, "text": chunk}
            for i, chunk in enumerate(all_chunks)
        ]
    }

    ensure_dirs()
    with open(INDEX_JSON, "w", encoding="utf-8") as f:
        json.dump(index_payload, f)

    return index_payload


def load_index() -> Dict[str, Any]:
    if not os.path.exists(INDEX_JSON):
        raise FileNotFoundError("PDF index not found. Run setup to create it.")
    with open(INDEX_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def ensure_pdf_index(pdf_url: str) -> None:
    ensure_dirs()
    download_pdf(pdf_url, PDF_PATH)
    if os.path.exists(INDEX_JSON):
        return
    pages = extract_text_from_pdf(PDF_PATH)
    build_index(pages)


def _bm25_from_index(idx: Dict[str, Any]) -> BM25Okapi:
    tokenized_corpus = [tokenize(item["text"]) for item in idx["chunks"]]
    return BM25Okapi(tokenized_corpus)


def query_pdf(question: str, top_k: int = 5) -> List[RetrievedChunk]:
    idx = load_index()
    bm25 = _bm25_from_index(idx)
    tokenized_query = tokenize(question)
    scores = bm25.get_scores(tokenized_query)
    ranked = sorted(
        [(i, float(score)) for i, score in enumerate(scores)],
        key=lambda x: x[1],
        reverse=True,
    )[:top_k]

    results: List[RetrievedChunk] = []
    for i, score in ranked:
        text = idx["chunks"][i]["text"]
        results.append(RetrievedChunk(chunk_id=i, score=score, text=text))
    return results


def build_context_snippet(question: str, top_k: int = 5, max_chars: int = 5000) -> str:
    chunks = query_pdf(question, top_k=top_k)
    pieces: List[str] = []
    for c in chunks:
        pieces.append(f"[Chunk {c.chunk_id} | score={c.score:.2f}]\n{c.text.strip()}\n")
    context = "\n\n".join(pieces)
    if len(context) > max_chars:
        context = context[:max_chars]
    return context