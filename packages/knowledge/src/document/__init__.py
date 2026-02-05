"""Document management service."""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field

from ai_red_blue_common import generate_uuid


class DocumentType(str, Enum):
    """Types of documents."""

    POLICY = "policy"
    PROCEDURE = "procedure"
    GUIDELINE = "guideline"
    INCIDENT_REPORT = "incident_report"
    THREAT_INTEL = "threat_intel"
    MALWARE_ANALYSIS = "malware_analysis"
    TOOL_DOCUMENTATION = "tool_documentation"
    TRAINING = "training"
    REFERENCE = "reference"


class Document(BaseModel):
    """Knowledge base document."""

    id: str = Field(default_factory=generate_uuid)
    title: str
    content: str
    document_type: DocumentType

    # Metadata
    author: Optional[str] = None
    department: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)

    # Relationships
    related_documents: list[str] = Field(default_factory=list)
    related_cves: list[str] = Field(default_factory=list)

    # Access
    access_level: str = "internal"  # public, internal, confidential, restricted
    allowed_groups: list[str] = Field(default_factory=list)

    # Temporal
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    effective_date: Optional[datetime] = None
    review_date: Optional[datetime] = None

    # Versioning
    version: str = "1.0"
    previous_versions: list[str] = Field(default_factory=list)

    # Status
    status: str = "draft"  # draft, review, approved, deprecated
    reviewed_by: Optional[str] = None
    approved_by: Optional[str] = None


class DocumentService:
    """Service for managing knowledge base documents."""

    def __init__(self):
        from ai_red_blue_common import get_logger

        self.logger = get_logger("document-service")
        self.documents: dict[str, Document] = {}

    def create_document(
        self,
        title: str,
        content: str,
        document_type: DocumentType,
        author: Optional[str] = None,
    ) -> Document:
        """Create a new document."""
        doc = Document(
            title=title,
            content=content,
            document_type=document_type,
            author=author,
        )
        self.documents[doc.id] = doc
        self.logger.info(f"Created document: {title}")
        return doc

    def get_document(self, document_id: str) -> Optional[Document]:
        """Get a document by ID."""
        return self.documents.get(document_id)

    def update_document(
        self,
        document_id: str,
        updates: dict[str, Any],
    ) -> Optional[Document]:
        """Update a document."""
        doc = self.documents.get(document_id)
        if doc:
            for key, value in updates.items():
                setattr(doc, key, value)
            doc.updated_at = datetime.now(timezone.utc)
            self.logger.info(f"Updated document: {doc.title}")
        return doc

    def delete_document(self, document_id: str) -> bool:
        """Delete a document."""
        doc = self.documents.pop(document_id, None)
        if doc:
            self.logger.info(f"Deleted document: {doc.title}")
            return True
        return False

    def get_documents_by_type(self, doc_type: DocumentType) -> list[Document]:
        """Get all documents of a specific type."""
        return [d for d in self.documents.values() if d.document_type == doc_type]

    def get_documents_by_tag(self, tag: str) -> list[Document]:
        """Get all documents with a specific tag."""
        return [d for d in self.documents.values() if tag in d.tags]

    def get_documents_by_status(self, status: str) -> list[Document]:
        """Get all documents with a specific status."""
        return [d for d in self.documents.values() if d.status == status]

    def get_statistics(self) -> dict[str, Any]:
        """Get document statistics."""
        return {
            "total_documents": len(self.documents),
            "by_type": {
                t.value: len(self.get_documents_by_type(t)) for t in DocumentType
            },
            "by_status": {
                s: len(self.get_documents_by_status(s))
                for s in set(d.status for d in self.documents.values())
            },
        }
