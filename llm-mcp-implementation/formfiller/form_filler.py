from formfiller.field_matcher import match_fields
from formfiller.form_parser import extract_text_from_upload, load_form_config
from llm.llm_factory import get_llm_client
import json

class FormFiller:
    def __init__(self, llm_type: str = "ollama"):
        self.llm = get_llm_client(llm_type)

    async def fill_form(self, form_type: str, file, user_data: dict = {}, prompt: str = None):
        cfg = load_form_config(form_type)
        raw_text = extract_text_from_upload(file)
        keys = [f['name'] for f in cfg['fields']]
        llm_prompt = prompt or f"""
You are a document parser. Extract exactly these keys: {keys}\n\nText:\n{raw_text[:5000]}\n\nRespond with a JSON object with only those keys (empty string for missing).\n""".strip()
        llm_response = await self.llm.query(llm_prompt)
        llm_data = json.loads(llm_response)
        matched, missing = match_fields([], {**user_data, **llm_data}, cfg)
        return {"matched": matched, "missing": missing, "llm_data": llm_data}
