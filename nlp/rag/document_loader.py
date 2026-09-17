"""
ORCA RAG Document Loader

Loads text documents from a folder and optionally splits them
into smaller chunks for retrieval.
"""

from pathlib import Path
import re


SUPPORTED_EXTENSIONS = {".txt", ".md"}


def load_document(file_path: str) -> dict:
    """
    Load one text or Markdown document.

    Returns:
        {
            "source": filename,
            "text": document_content
        }
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: {path.suffix}"
        )

    text = path.read_text(
        encoding="utf-8"
    )

    return {
        "source": path.name,
        "text": text,
    }


def load_documents(folder_path: str) -> list[dict]:
    """
    Load all supported documents from a folder.
    """
    candidates = [
        Path(folder_path),
        Path(__file__).resolve().parent.parent / "data" / "knowledge",
        Path("data/knowledge"),
        Path("nlp/data/knowledge")
    ]
    folder = None
    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            folder = candidate
            break

    if not folder:
        raise FileNotFoundError(
            f"Folder not found: {folder_path}"
        )

    documents = []

    for file_path in sorted(folder.iterdir()):
        if (
            file_path.is_file()
            and file_path.suffix.lower() in SUPPORTED_EXTENSIONS
        ):
            documents.append(
                load_document(str(file_path))
            )

    return documents


def _extract_section_title(
    text: str,
    current_title: str,
) -> str:
    """
    Extract a Markdown heading from a line.

    Example:
        "# Marine Safety" -> "Marine Safety"

    If the line is not a Markdown heading, the previous
    section title is retained.
    """

    line = text.strip()

    heading_match = re.match(
        r"^#{1,6}\s+(.+?)\s*$",
        line,
    )

    if heading_match:
        return heading_match.group(1).strip()

    return current_title


def _split_into_paragraphs(text: str) -> list[str]:
    """
    Split text into non-empty paragraphs.

    Multiple blank lines are treated as paragraph separators.
    """

    paragraphs = re.split(
        r"\n\s*\n",
        text.strip(),
    )

    return [
        paragraph.strip()
        for paragraph in paragraphs
        if paragraph.strip()
    ]


def chunk_document(
    document: dict,
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[dict]:
    """
    Split one document into smaller chunks.

    Args:
        document:
            {
                "source": str,
                "text": str
            }

        chunk_size:
            Maximum approximate number of words per chunk.

        overlap:
            Number of words repeated between consecutive chunks.

    Returns:
        A list of chunk dictionaries:

        {
            "source": str,
            "text": str,
            "chunk_id": str,
            "section": str,
        }

    Notes:
        - Existing document dictionaries remain unchanged.
        - Chunking is optional.
        - Markdown headings are preserved as section metadata.
        - Chunks are created using paragraphs and word limits.
    """

    if not isinstance(document, dict):
        raise TypeError(
            "document must be a dictionary"
        )

    if "source" not in document or "text" not in document:
        raise ValueError(
            "document must contain source and text"
        )

    if not isinstance(document["source"], str):
        raise TypeError(
            "document source must be a string"
        )

    if not isinstance(document["text"], str):
        raise TypeError(
            "document text must be a string"
        )

    if not isinstance(chunk_size, int):
        raise TypeError(
            "chunk_size must be an integer"
        )

    if not isinstance(overlap, int):
        raise TypeError(
            "overlap must be an integer"
        )

    if chunk_size <= 0:
        raise ValueError(
            "chunk_size must be greater than zero"
        )

    if overlap < 0:
        raise ValueError(
            "overlap cannot be negative"
        )

    if overlap >= chunk_size:
        raise ValueError(
            "overlap must be smaller than chunk_size"
        )

    source = document["source"]
    text = document["text"].strip()

    if not text:
        return []

    paragraphs = _split_into_paragraphs(text)

    chunks = []

    current_words = []
    current_section = "General"

    chunk_number = 0

    for paragraph in paragraphs:
        lines = paragraph.splitlines()

        paragraph_section = current_section

        for line in lines:
            extracted_title = _extract_section_title(
                line,
                current_section,
            )

            if extracted_title != current_section:
                current_section = extracted_title
                paragraph_section = extracted_title

        paragraph_words = paragraph.split()

        # If the paragraph itself is larger than the chunk size,
        # split it into word-based pieces.
        paragraph_parts = []

        for start in range(
            0,
            len(paragraph_words),
            chunk_size - overlap,
        ):
            paragraph_parts.append(
                paragraph_words[
                    start:start + chunk_size
                ]
            )

        for part in paragraph_parts:
            if not part:
                continue

            if (
                len(current_words) + len(part)
                <= chunk_size
            ):
                current_words.extend(part)
                continue

            chunk_text = " ".join(current_words)

            chunks.append(
                {
                    "source": source,
                    "text": chunk_text,
                    "chunk_id": (
                        f"{Path(source).stem}_{chunk_number}"
                    ),
                    "section": paragraph_section,
                }
            )

            chunk_number += 1

            overlap_words = current_words[
                -overlap:
            ] if overlap > 0 else []

            current_words = (
                overlap_words + part
            )

    if current_words:
        chunks.append(
            {
                "source": source,
                "text": " ".join(current_words),
                "chunk_id": (
                    f"{Path(source).stem}_{chunk_number}"
                ),
                "section": current_section,
            }
        )

    return chunks


def chunk_documents(
    documents: list[dict],
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[dict]:
    """
    Split multiple documents into chunks.

    Returns one flat list containing chunks from all documents.
    """

    if not isinstance(documents, list):
        raise TypeError(
            "documents must be a list"
        )

    all_chunks = []

    for document in documents:
        all_chunks.extend(
            chunk_document(
                document=document,
                chunk_size=chunk_size,
                overlap=overlap,
            )
        )

    return all_chunks