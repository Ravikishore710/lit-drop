# Common Type Definitions and Enums

from enum import Enum


class ProcessingStatus(str, Enum):
    UPLOADED = "UPLOADED"
    VALIDATING = "VALIDATING"
    PROCESSING = "PROCESSING"
    INDEXING = "INDEXING"
    READY = "READY"
    FAILED = "FAILED"


class ExtractionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


class ElementType(str, Enum):
    TITLE = "title"
    SECTION_HEADING = "section_heading"
    PARAGRAPH = "paragraph"
    LIST = "list"
    TABLE = "table"
    FIGURE = "figure"
    CHART = "chart"
    EQUATION = "equation"
    CAPTION = "caption"
    REFERENCE = "reference"
    HEADER = "header"
    FOOTER = "footer"


class RelationType(str, Enum):
    HAS_PAGE = "HAS_PAGE"
    HAS_SECTION = "HAS_SECTION"
    HAS_ELEMENT = "HAS_ELEMENT"
    AUTHORED_BY = "AUTHORED_BY"
    CITES = "CITES"
    CONTAINS_TABLE = "CONTAINS_TABLE"
    CONTAINS_FIGURE = "CONTAINS_FIGURE"
    CONTAINS_EQUATION = "CONTAINS_EQUATION"
    ASSOCIATED_WITH_CAPTION = "ASSOCIATED_WITH_CAPTION"
    MENTIONS_ENTITY = "MENTIONS_ENTITY"


class GroundingStatus(str, Enum):
    FOUND = "FOUND"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    INFERRED = "INFERRED"
    NOT_FOUND = "NOT_FOUND"
    AMBIGUOUS = "AMBIGUOUS"
    CONTRADICTORY = "CONTRADICTORY"


class QueryIntent(str, Enum):
    FACTUAL = "FACTUAL"
    EXPLANATION = "EXPLANATION"
    TABLE = "TABLE"
    CHART = "CHART"
    FIGURE = "FIGURE"
    EQUATION = "EQUATION"
    COMPARISON = "COMPARISON"
    MULTI_DOCUMENT = "MULTI_DOCUMENT"
    GRAPH = "GRAPH"
    NOT_FOUND = "NOT_FOUND"
