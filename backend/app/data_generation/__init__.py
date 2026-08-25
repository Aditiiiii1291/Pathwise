"""
Pathwise Data Generation Module (Backend Package)

Provides self-contained synthetic student cohort generation for demonstrations,
local development, testing, and production initializations.
"""

from app.data_generation.generator import (
    SyntheticDataGenerator,
    TRAJECTORY_DISTRIBUTION,
    DEPARTMENTS,
    SUBJECTS_POOL,
    EXAM_TYPES,
)

__all__ = [
    "SyntheticDataGenerator",
    "TRAJECTORY_DISTRIBUTION",
    "DEPARTMENTS",
    "SUBJECTS_POOL",
    "EXAM_TYPES",
]
