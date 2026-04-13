"""
Document Ingestion Pipeline — Loads knowledge documents from backend/knowledge/
Extracts text, chunks into ~500-token segments, and stores in ChromaDB.
"""

import os
import uuid
from pathlib import Path

import fitz  # PyMuPDF
import pandas as pd

from backend.config import KNOWLEDGE_DIR
from backend.core.rag import add_knowledge, get_collection

# Category mapping based on filename patterns
CATEGORY_MAP = {
    "WELL": "well_building",
    "CIBSE": "cibse",
    "Universal Design": "universal_design",
    "WHO": "who_housing",
    "Falls": "falls_prevention",
    "Montessori": "montessori",
    "SAP": "cso_disability",
}

CHUNK_SIZE = 500  # tokens (~words)
CHUNK_OVERLAP = 50


def _get_category(filename: str) -> str:
    for key, cat in CATEGORY_MAP.items():
        if key.lower() in filename.lower():
            return cat
    return "general"


def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks of approximately chunk_size words."""
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        if len(chunk.strip()) > 50:  # Skip tiny fragments
            chunks.append(chunk.strip())
        start = end - overlap
    return chunks


def _extract_pdf_text(filepath: str) -> str:
    """Extract all text from a PDF using PyMuPDF."""
    text = ""
    try:
        doc = fitz.open(filepath)
        for page in doc:
            text += page.get_text() + "\n"
        doc.close()
    except Exception as e:
        print(f"[Ingest] Error reading PDF {filepath}: {e}")
    return text


def _extract_csv_text(filepath: str) -> str:
    """Extract meaningful text from the CSO disability statistics CSV."""
    try:
        df = pd.read_csv(filepath, encoding="utf-8", on_bad_lines="skip")
        # Convert to a descriptive text block
        lines = []
        lines.append(f"CSO Ireland Disability Statistics — {len(df)} records")
        lines.append(f"Columns: {', '.join(df.columns.tolist())}")
        # Sample key rows as text
        for _, row in df.head(100).iterrows():
            row_text = " | ".join([f"{col}: {val}" for col, val in row.items() if pd.notna(val)])
            lines.append(row_text)
        return "\n".join(lines)
    except Exception as e:
        print(f"[Ingest] Error reading CSV {filepath}: {e}")
        return ""


def ingest_documents():
    """
    Main ingestion function. Scans backend/knowledge/ for PDFs and CSVs,
    extracts text, chunks it, and stores in ChromaDB.
    Skips if documents are already ingested.
    """
    collection = get_collection()

    # Check if already ingested
    if collection.count() > 10:
        print(f"[Ingest] Knowledge base already has {collection.count()} documents. Skipping.")
        return collection.count()

    knowledge_path = Path(KNOWLEDGE_DIR)
    if not knowledge_path.exists():
        print("[Ingest] Knowledge directory not found.")
        return 0

    total_chunks = 0
    files = list(knowledge_path.glob("*"))

    for filepath in files:
        filename = filepath.name

        if filename.startswith("."):
            continue

        category = _get_category(filename)

        # Extract text
        if filepath.suffix.lower() == ".pdf":
            print(f"[Ingest] Processing PDF: {filename}")
            raw_text = _extract_pdf_text(str(filepath))
        elif filepath.suffix.lower() == ".csv":
            print(f"[Ingest] Processing CSV: {filename}")
            raw_text = _extract_csv_text(str(filepath))
        else:
            continue

        if not raw_text.strip():
            print(f"[Ingest] No text extracted from {filename}")
            continue

        # Chunk text
        chunks = _chunk_text(raw_text)
        print(f"[Ingest] {filename}: {len(chunks)} chunks")

        # Store in ChromaDB
        for i, chunk in enumerate(chunks):
            doc_id = f"{category}_{i}_{uuid.uuid4().hex[:8]}"
            metadata = {
                "source": filename,
                "category": category,
                "chunk_index": i,
                "total_chunks": len(chunks),
            }
            try:
                add_knowledge(text=chunk, metadata=metadata, doc_id=doc_id)
            except Exception as e:
                print(f"[Ingest] Error storing chunk {i} from {filename}: {e}")

        total_chunks += len(chunks)

    print(f"[Ingest] Done! Ingested {total_chunks} document chunks from {len(files)} files.")
    return total_chunks
