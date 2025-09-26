


from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from formfiller.form_filler import FormFiller
from formfiller.form_parser import parse_uploaded_form, load_form_config
from formfiller.field_matcher import match_fields
from formdiscovery import discover_form
from browseragent import generate_actions, run_browser_actions, ensure_allowed_domains
import json

class LLMChoice(str):
    pass  # for future enum if needed


class FillFormRequest(BaseModel):
    form_type: str
    llm: str = "ollama"  # or "mcp"
    prompt: str
    user_data: dict = {}
    autofill: bool = True
    form_url: str = None  # Needed for browser automation


app = FastAPI(title="Sampatti Lighthouse MCP+OCR")


@app.post("/fill_form", tags=["form"])
async def fill_form(req: FillFormRequest, file: UploadFile = File(...)):
    form_filler = FormFiller(llm_type=req.llm)
    result = await form_filler.fill_form(req.form_type, file, user_data=req.user_data, prompt=req.prompt)
    # If autofill requested, use browser agent to fill the form
    browser_results = None
    if req.autofill and req.form_url:
        domain = req.form_url.split('/')[2]
        goal = f"Login if needed then fill {result['matched']} at {req.form_url}"
        actions = generate_actions(goal, domain)
        ensure_allowed_domains(actions, [domain])
        browser_results = {"actions": [a.model_dump() for a in actions], "results": run_browser_actions(actions)}
    return {**result, "browser_automation": browser_results}




# LLM chat endpoint
class LLMRequest(BaseModel):
    prompt: str
    model: str = "phi3:mini"

class LLMResponse(BaseModel):
    response: str



from llm.llm_factory import get_llm_client

@app.post("/llm_chat", response_model=LLMResponse, tags=["llm"])
async def llm_chat(req: LLMRequest):
    try:
        llm_client = get_llm_client("ollama")
        result = await llm_client.query(req.prompt, req.model)
        return LLMResponse(response=result)
    except Exception as e:
        raise HTTPException(500, str(e))

#Step 1: Discover

class DiscoverReq(BaseModel): user_request: str
@app.post("/discover", tags=["1-discover"] )
def api_discover(r: DiscoverReq):
    try: return discover_form(r.user_request)
    except Exception as e: raise HTTPException(500,str(e))

#Step 2: Extract fields

class ExtractReq(BaseModel): form_url: str
@app.post("/extract_fields", tags=["2-extract"] )
def api_extract(r: ExtractReq):
    domain=r.form_url.split('/')[2]
    goal="extract all form inputs and labels"
    actions=generate_actions(goal,domain)
    ensure_allowed_domains(actions,[domain])
    return {"actions":[a.model_dump() for a in actions],"results":run_browser_actions(actions)}

#Step 3: Parse docs

@app.post("/parse/{form_type}", tags=["3-parse"] )
async def api_parse(form_type: str, file: UploadFile=File(...)):
    try: return {"fields":await parse_uploaded_form(form_type,file)}
    except HTTPException as he: raise he
    except Exception as e: raise HTTPException(500,str(e))

class MatchReq(BaseModel): form_type: str; extracted_fields: list[dict]; user_data: dict
@app.post("/match_fields", tags=["3-match"] )
def api_match(r: MatchReq):
    cfg=load_form_config(r.form_type)
    m,miss=match_fields(r.extracted_fields,r.user_data,cfg)
    return {"matched":m,"missing":miss}

#Step 4: Autofill

class AutoReq(BaseModel): form_url:str; matched_values:dict; login:dict|None=None
@app.post("/autofill", tags=["4-autofill"] )
def api_autofill(r: AutoReq):
    domain=r.form_url.split('/')[2]
    goal=f"Login if needed then fill {r.matched_values} at {r.form_url}"
    actions=generate_actions(goal,domain)
    ensure_allowed_domains(actions,[domain])
    return {"actions":[a.model_dump() for a in actions],"results":run_browser_actions(actions)}