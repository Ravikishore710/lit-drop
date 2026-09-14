# Domain Exceptions

class DocumentIntelligenceError(Exception):
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class FileValidationError(DocumentIntelligenceError):
    pass


class PDFParsingError(DocumentIntelligenceError):
    pass


class StorageError(DocumentIntelligenceError):
    pass


class VectorIndexError(DocumentIntelligenceError):
    pass


class GraphStoreError(DocumentIntelligenceError):
    pass


class RetrievalError(DocumentIntelligenceError):
    pass


class GroundingError(DocumentIntelligenceError):
    pass
