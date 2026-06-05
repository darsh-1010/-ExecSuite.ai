"""
Root test suite that exposes the core backend tests to pytest runner.
"""

from backend.tests.test_core import (
    test_shared_memory_blackboard,
    test_shared_memory_file_operations,
    test_llm_wrapper_initialization,
    test_organization_setup,
    test_organization_setup_marketing_campaign,
    test_organization_setup_dynamic_change,
)

__all__ = [
    "test_shared_memory_blackboard",
    "test_shared_memory_file_operations",
    "test_llm_wrapper_initialization",
    "test_organization_setup",
    "test_organization_setup_marketing_campaign",
    "test_organization_setup_dynamic_change",
]
