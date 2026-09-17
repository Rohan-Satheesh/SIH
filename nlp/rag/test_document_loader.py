from pathlib import Path

import pytest

from nlp.rag.document_loader import (
    load_document,
    load_documents,
)


def test_load_document(tmp_path):
    file_path = tmp_path / "marine.txt"
    file_path.write_text(
        "Sea safety information",
        encoding="utf-8",
    )

    result = load_document(str(file_path))

    assert result["source"] == "marine.txt"
    assert result["text"] == "Sea safety information"


def test_load_markdown_document(tmp_path):
    file_path = tmp_path / "marine.md"
    file_path.write_text(
        "# Marine Safety",
        encoding="utf-8",
    )

    result = load_document(str(file_path))

    assert result["text"] == "# Marine Safety"


def test_missing_file():
    with pytest.raises(FileNotFoundError):
        load_document("does_not_exist.txt")


def test_unsupported_file(tmp_path):
    file_path = tmp_path / "data.csv"
    file_path.write_text(
        "a,b,c",
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        load_document(str(file_path))


def test_load_documents(tmp_path):
    first_file = tmp_path / "first.txt"
    second_file = tmp_path / "second.md"
    ignored_file = tmp_path / "ignored.csv"

    first_file.write_text("First", encoding="utf-8")
    second_file.write_text("Second", encoding="utf-8")
    ignored_file.write_text("Ignored", encoding="utf-8")

    result = load_documents(str(tmp_path))

    assert len(result) == 2
    assert result[0]["source"] == "first.txt"
    assert result[1]["source"] == "second.md"


def test_missing_folder():
    with pytest.raises(FileNotFoundError):
        load_documents("does_not_exist")