import pytest
from formfiller.form_filler import FormFiller
from fastapi import UploadFile

class DummyFile:
    def __init__(self, content, filename):
        self.file = content
        self.filename = filename

@pytest.mark.asyncio
def test_fill_form(monkeypatch):
    # Patch LLM to return a known JSON
    class DummyLLM:
        async def query(self, prompt, model=None):
            return '{"field1": "value1", "field2": "value2"}'
    monkeypatch.setattr("formfiller.form_filler.get_llm_client", lambda llm_type: DummyLLM())
    form_filler = FormFiller(llm_type="ollama")
    dummy_file = DummyFile(content=open(__file__, "rb"), filename="dummy.pdf")
    result = pytest.run(form_filler.fill_form("test_form", dummy_file, user_data={}))
    assert "matched" in result
    assert "llm_data" in result
