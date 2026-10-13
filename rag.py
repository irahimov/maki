#!/usr/bin/env python3
"""MAKI lokal RAG. İstifadə: rag.py index | rag.py query "sual" """
import sys
from pathlib import Path

import chromadb
import ollama

EMBED = "nomic-embed-text"
EXT = {".py", ".md", ".js", ".ts", ".html", ".css", ".json", ".toml", ".txt", ".sh"}
SKIP = {".git", "__pycache__", "node_modules", ".venv", ".pytest_cache", ".ruff_cache"}
ROOT = Path.cwd().resolve()
DB = Path.home() / ".maki-rag" / ROOT.name
LINES, OVERLAP, BATCH = 40, 5, 16


def embed(texts: list[str], prefix: str) -> list[list[float]]:
    r = ollama.embed(model=EMBED, input=[prefix + t for t in texts], keep_alive=0)
    return r["embeddings"]


def files() -> list[Path]:
    out: list[Path] = []
    for p in sorted(ROOT.rglob("*")):
        if not p.is_file() or p.suffix not in EXT:
            continue
        parts = p.relative_to(ROOT).parts
        hidden = any(x.startswith(".") for x in parts)
        if SKIP & set(parts) or hidden or p.stat().st_size > 200_000:
            continue
        out.append(p)
    return out


def chunks(p: Path) -> list[tuple[str, str, int]]:
    lines = p.read_text(errors="ignore").splitlines()
    res: list[tuple[str, str, int]] = []
    step = LINES - OVERLAP
    for start in range(0, max(len(lines), 1), step):
        text = "\n".join(lines[start:start + LINES]).strip()
        if text:
            rel = str(p.relative_to(ROOT))
            res.append((f"{rel}:{start + 1}", f"# {rel}\n{text}", start + 1))
    return res


def index() -> None:
    DB.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(DB))
    try:
        client.delete_collection("code")
    except Exception:
        pass
    col = client.create_collection("code")
    items = [c for f in files() for c in chunks(f)]
    for i in range(0, len(items), BATCH):
        part = items[i:i + BATCH]
        col.upsert(
            ids=[x[0] for x in part],
            documents=[x[1] for x in part],
            embeddings=embed([x[1] for x in part], "search_document: "),
            metadatas=[{"line": x[2]} for x in part],
        )
    print(f"✅ {len(items)} parça indeksləndi: {DB}")


def search(q: str, k: int = 4) -> list[tuple[str, str]]:
    client = chromadb.PersistentClient(path=str(DB))
    col = client.get_collection("code")
    r = col.query(query_embeddings=embed([q], "search_query: "), n_results=k)
    return list(zip(r["ids"][0], r["documents"][0]))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "index":
        index()
    elif cmd == "query" and len(sys.argv) > 2:
        for pid, doc in search(" ".join(sys.argv[2:])):
            print(f"\n── {pid} ──\n{doc[:500]}")
    else:
        print('İstifadə: rag.py index | rag.py query "sual"')
        sys.exit(1)
