import pytest
from llm.llm_factory import get_llm_client

@pytest.mark.asyncio
def test_ollama_llm():
    llm = get_llm_client("ollama")
    result = pytest.run(llm.query("Say hello!"))
    assert isinstance(result, str)
    assert len(result) > 0

@pytest.mark.asyncio
def test_mcp_llm():
    llm = get_llm_client("mcp")
    result = pytest.run(llm.query("Say hello!"))
    assert isinstance(result, str)
    assert len(result) > 0
