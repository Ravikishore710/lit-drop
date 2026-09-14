# Cryptographic Hashing Utilities

import hashlib
from pathlib import Path
from typing import BinaryIO, Union


def compute_sha256_stream(stream: BinaryIO, chunk_size: int = 65536) -> str:
    hasher = hashlib.sha256()
    while chunk := stream.read(chunk_size):
        hasher.update(chunk)
    return hasher.hexdigest()


def compute_file_sha256(file_path: Union[str, Path]) -> str:
    path = Path(file_path)
    with open(path, "rb") as f:
        return compute_sha256_stream(f)


def compute_bytes_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def format_document_id(hex_digest: str) -> str:
    clean_hash = hex_digest.replace("sha256:", "").strip()
    return f"sha256:{clean_hash}"
