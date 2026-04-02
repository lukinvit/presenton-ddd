"""Presenton Shared Kernel — base classes and infrastructure abstractions."""

from shared.domain import (
    AggregateRoot,
    DomainEvent,
    Entity,
    EventBus,
    EventHandler,
    Repository,
    ValueObject,
)
from shared.infrastructure import (
    DatabaseConfig,
    InMemoryEventBus,
    RedisEventBus,
    Settings,
    create_engine_from_config,
    get_logger,
    get_settings,
    setup_logging,
)
from shared.mcp import DomainMCPServer, MCPClient, MCPToolCall

__all__ = [
    "AggregateRoot",
    "DatabaseConfig",
    "DomainEvent",
    "DomainMCPServer",
    "Entity",
    "EventBus",
    "EventHandler",
    "InMemoryEventBus",
    "MCPClient",
    "MCPToolCall",
    "RedisEventBus",
    "Repository",
    "Settings",
    "ValueObject",
    "create_engine_from_config",
    "get_logger",
    "get_settings",
    "setup_logging",
]
