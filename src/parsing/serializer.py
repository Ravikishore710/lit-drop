# Canonical JSONL Serializer and Deserializer

import json
from pathlib import Path
from typing import Iterator, Union

from src.parsing.models import (
    CanonicalDocument,
    DocumentMetadata,
    ElementObject,
    PageObject,
    RelationObject,
)


class CanonicalSerializer:
    @staticmethod
    def serialize_document(doc: CanonicalDocument, output_dir: Union[str, Path]) -> Path:
        out_path = Path(output_dir)
        doc_dir = out_path / "documents"
        pages_dir = out_path / "pages"
        elements_dir = out_path / "elements"
        relations_dir = out_path / "relations"

        for d in (doc_dir, pages_dir, elements_dir, relations_dir):
            d.mkdir(parents=True, exist_ok=True)

        clean_id = doc.document_id.replace("sha256:", "")

        doc_file = doc_dir / f"{clean_id}.json"
        with open(doc_file, "w", encoding="utf-8") as f:
            f.write(doc.model_dump_json(indent=2))

        pages_jsonl = pages_dir / f"{clean_id}_pages.jsonl"
        with open(pages_jsonl, "w", encoding="utf-8") as f:
            for page in doc.pages:
                f.write(page.model_dump_json() + "\n")

        elements_jsonl = elements_dir / f"{clean_id}_elements.jsonl"
        with open(elements_jsonl, "w", encoding="utf-8") as f:
            for elem in doc.elements:
                f.write(elem.model_dump_json() + "\n")

        relations_jsonl = relations_dir / f"{clean_id}_relations.jsonl"
        with open(relations_jsonl, "w", encoding="utf-8") as f:
            for rel in doc.relations:
                f.write(rel.model_dump_json() + "\n")

        return doc_file

    @staticmethod
    def load_document(doc_json_path: Union[str, Path]) -> CanonicalDocument:
        path = Path(doc_json_path)
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return CanonicalDocument.model_validate(raw)

    @staticmethod
    def iter_elements(elements_jsonl_path: Union[str, Path]) -> Iterator[ElementObject]:
        with open(elements_jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    yield ElementObject.model_validate_json(line)
