"""
Unit tests for core backend classes, including SharedMemory, LLMWrapper, and Organization.
"""

import os
import shutil
from typing import Generator

import pytest

from core.memory import SharedMemory
from core.llm_wrapper import LLMWrapper
from core.organization import Organization

TEST_WORKSPACE = "test_workspace"


@pytest.fixture(autouse=True)
def setup_and_teardown() -> Generator[None, None, None]:
    """Fixture to ensure the test workspace directory is cleaned up before and after tests."""
    # Setup: ensure test workspace is clean
    if os.path.exists(TEST_WORKSPACE):
        shutil.rmtree(TEST_WORKSPACE)
    yield
    # Teardown
    if os.path.exists(TEST_WORKSPACE):
        shutil.rmtree(TEST_WORKSPACE)


def test_shared_memory_file_operations() -> None:
    """Test file write, read, and security path traversal validation in SharedMemory."""
    memory = SharedMemory(workspace_dir=TEST_WORKSPACE)

    # Test writing file
    filename = "test_doc.md"
    content = "# Test Content\nThis is a test file."
    filepath = memory.write_file(filename, content)

    assert os.path.exists(filepath)
    assert filename in [f["name"] for f in memory.list_files()]

    # Test reading file
    read_content = memory.read_file(filename)
    assert read_content == content

    # Test path traversal safety
    with pytest.raises(PermissionError):
        memory.read_file("../outside.txt")

    with pytest.raises(PermissionError):
        memory.write_file("../outside.txt", "evil")


def test_shared_memory_blackboard() -> None:
    """Test shared blackboard get and set operations in SharedMemory."""
    memory = SharedMemory(workspace_dir=TEST_WORKSPACE)
    memory.set_blackboard("product_name", "TestApp")
    assert memory.get_blackboard("product_name") == "TestApp"
    assert memory.get_blackboard("nonexistent", "default") == "default"


def test_llm_wrapper_initialization() -> None:
    """Test LLMWrapper fallback initialization without active environment API keys."""
    # Verify it initializes without keys (should warn but not crash)
    wrapper = LLMWrapper(provider="gemini", model="gemini-2.5-flash")
    assert wrapper.provider == "gemini"
    assert wrapper.model == "gemini-2.5-flash"


def test_organization_setup() -> None:
    """Test Organization agent collection instantiation and role definitions."""
    memory = SharedMemory(workspace_dir=TEST_WORKSPACE)
    org = Organization(memory=memory, llm_provider="gemini")

    assert "CEO" in org.agents
    assert "CFO" in org.agents
    assert "CMO" in org.agents
    assert "Developer" in org.agents

    assert org.agents["CEO"].role == "CEO"
    assert org.agents["Developer"].role == "Chief Developer"


def test_organization_setup_marketing_campaign() -> None:
    """Test Organization agent collection for marketing_campaign department."""
    memory = SharedMemory(workspace_dir=TEST_WORKSPACE)
    org = Organization(memory=memory, llm_provider="gemini", department="marketing_campaign")

    assert "Product_Marketer" in org.agents
    assert "Copywriter" in org.agents
    assert "Social_Media_Manager" in org.agents
    assert "SEO_Strategist" in org.agents

    assert org.agents["Product_Marketer"].role == "Product Marketer"
    assert org.agents["Copywriter"].role == "Marketing Copywriter"


def test_organization_setup_dynamic_change() -> None:
    """Test Organization dynamic department transition via setup_default_agents."""
    memory = SharedMemory(workspace_dir=TEST_WORKSPACE)
    org = Organization(memory=memory, llm_provider="gemini", department="c_suite")
    assert "CEO" in org.agents

    org.setup_default_agents(department="sales_campaign")
    assert "CEO" not in org.agents
    assert "Sales_Director" in org.agents
    assert org.agents["Sales_Director"].role == "Sales Director"
