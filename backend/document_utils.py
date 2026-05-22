from __future__ import annotations

import re
import zipfile
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree

try:
    from pypdf import PdfReader
except Exception:  # pragma: no cover
    PdfReader = None


TEXT_SUFFIXES = {".txt", ".md", ".markdown", ".csv"}
WORD_XML_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def normalize_text(text: str) -> str:
    text = text.replace("\u3000", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_text(path: Path, max_chars: int | None = None) -> str:
    suffix = path.suffix.lower()
    if suffix in TEXT_SUFFIXES:
        text = path.read_text(encoding="utf-8", errors="ignore")
    elif suffix == ".docx":
        text = _extract_docx(path)
    elif suffix == ".pdf":
        text = _extract_pdf(path)
    elif suffix == ".doc":
        text = _extract_legacy_doc_best_effort(path)
    else:
        text = ""

    text = normalize_text(text)
    if max_chars and len(text) > max_chars:
        return text[:max_chars]
    return text


def _extract_docx(path: Path) -> str:
    parts: list[str] = []
    with zipfile.ZipFile(path) as zf:
        names = [n for n in zf.namelist() if n.startswith("word/") and n.endswith(".xml")]
        for name in ["word/document.xml", *[n for n in names if n != "word/document.xml"]]:
            if name not in zf.namelist():
                continue
            root = ElementTree.fromstring(zf.read(name))
            for para in root.findall(".//w:p", WORD_XML_NS):
                texts = [node.text or "" for node in para.findall(".//w:t", WORD_XML_NS)]
                if texts:
                    parts.append("".join(texts))
    return "\n".join(parts)


def _extract_pdf(path: Path) -> str:
    if PdfReader is None:
        return ""
    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages[:30]:
        pages.append(page.extract_text() or "")
    return "\n".join(pages)


def _extract_legacy_doc_best_effort(path: Path) -> str:
    # Legacy .doc is binary. This fallback is not perfect, but gives the MVP
    # something searchable until a production parser/OCR service is wired in.
    raw = path.read_bytes()
    text = raw.decode("gb18030", errors="ignore")
    text = "".join(ch if ch.isprintable() or ch in "\r\n\t" else " " for ch in text)
    return text


def chunk_text(text: str, size: int = 900, overlap: int = 120) -> list[str]:
    text = normalize_text(text)
    if not text:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + size)
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = max(0, end - overlap)
    return chunks


def find_keywords(text: str, keywords: Iterable[str]) -> list[str]:
    return [kw for kw in keywords if kw and kw in text]


def extract_amounts(text: str) -> list[float]:
    candidates = re.findall(
        r"(?:人民币|金额|价款|合同价|借款金额|总价|小写)?\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)\s*(万元|元)",
        text,
    )
    amounts: list[float] = []
    for raw, unit in candidates:
        try:
            value = float(raw.replace(",", ""))
        except ValueError:
            continue
        if unit == "万元":
            value *= 10000
        if value >= 100:
            amounts.append(value)
    return amounts[:20]
