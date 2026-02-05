"""Threat intelligence service for IOC management."""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field

from ai_red_blue_common import generate_uuid


class IOCType(str, Enum):
    """Types of indicators of compromise."""

    IP = "ip"
    DOMAIN = "domain"
    URL = "url"
    HASH = "hash"
    EMAIL = "email"
    FILEPATH = "filepath"
    REGISTRY = "registry"
    MUTEX = "mutex"
    CERTIFICATE = "certificate"
    USER_AGENT = "user_agent"


class IOC(BaseModel):
    """Indicator of compromise."""

    id: str = Field(default_factory=generate_uuid)
    value: str
    type: IOCType
    source: str

    # Context
    description: str = ""
    tags: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    # Threat context
    threat_actor: Optional[str] = None
    campaign: Optional[str] = None
    malware_family: Optional[str] = None

    # Temporal
    first_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    # Actions
    action: str = "watch"  # watch, block, alert
    severity: str = "medium"

    # Statistics
    hit_count: int = 0
    false_positive_count: int = 0


class ThreatFeed(BaseModel):
    """Threat intelligence feed."""

    id: str = Field(default_factory=generate_uuid)
    name: str
    source_url: Optional[str] = None
    feed_type: str  # public, commercial, private, internal

    # Status
    enabled: bool = True
    last_fetched: Optional[datetime] = None
    last_updated: Optional[datetime] = None

    # Statistics
    total_iocs: int = 0
    iocs_added_today: int = 0

    # Configuration
    update_interval_hours: int = 24
    auto_update: bool = True


class ThreatIntelligenceService:
    """Service for managing threat intelligence."""

    def __init__(self):
        from ai_red_blue_common import get_logger

        self.logger = get_logger("threat-intel-service")
        self.iocs: dict[str, IOC] = {}
        self.feeds: dict[str, ThreatFeed] = {}

    async def add_ioc(
        self,
        value: str,
        ioc_type: IOCType,
        source: str,
        **kwargs,
    ) -> IOC:
        """Add a new IOC."""
        ioc = IOC(
            value=value,
            type=ioc_type,
            source=source,
            **kwargs,
        )
        self.iocs[value] = ioc
        self.logger.info(f"Added IOC: {value} ({ioc_type.value})")
        return ioc

    async def remove_ioc(self, value: str) -> bool:
        """Remove an IOC."""
        if value in self.iocs:
            del self.iocs[value]
            self.logger.info(f"Removed IOC: {value}")
            return True
        return False

    async def lookup_ioc(
        self,
        value: str,
    ) -> Optional[IOC]:
        """Look up an IOC."""
        ioc = self.iocs.get(value)
        if ioc:
            ioc.hit_count += 1
            ioc.last_seen = datetime.now(timezone.utc)
        return ioc

    async def check_iocs(
        self,
        values: list[str],
    ) -> dict[str, Optional[IOC]]:
        """Check multiple IOCs."""
        results = {}
        for value in values:
            results[value] = await self.lookup_ioc(value)
        return results

    async def register_feed(
        self,
        name: str,
        feed_type: str,
        source_url: Optional[str] = None,
    ) -> ThreatFeed:
        """Register a threat feed."""
        feed = ThreatFeed(
            name=name,
            feed_type=feed_type,
            source_url=source_url,
        )
        self.feeds[name] = feed
        self.logger.info(f"Registered threat feed: {name}")
        return feed

    async def sync_feed(self, feed_name: str) -> int:
        """Sync a threat feed."""
        feed = self.feeds.get(feed_name)
        if feed:
            feed.last_fetched = datetime.now(timezone.utc)
            self.logger.info(f"Synced threat feed: {feed_name}")
            return feed.total_iocs
        return 0

    def get_statistics(self) -> dict[str, Any]:
        """Get threat intelligence statistics."""
        return {
            "total_iocs": len(self.iocs),
            "by_type": {
                t.value: len([i for i in self.iocs.values() if i.type == t])
                for t in IOCType
            },
            "total_feeds": len(self.feeds),
            "enabled_feeds": len([f for f in self.feeds.values() if f.enabled]),
        }
