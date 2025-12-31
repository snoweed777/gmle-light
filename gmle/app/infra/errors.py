"""Domain-specific exception categories."""

class ConfigError(Exception):
    """Configuration related failure."""


class InfraError(Exception):
    """Infrastructure (I/O, lock, OS) failure."""


class AnkiError(Exception):
    """AnkiConnect failure."""


class SOTError(Exception):
    """Source of Truth (items/ledger) failure."""


class CycleError(Exception):
    """Cycle selection/apply failure."""


class DegradeTrigger(Exception):
    """Triggers Safe-Degrade path."""
