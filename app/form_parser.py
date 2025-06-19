# app/form_parser.py

import io
import os
import tempfile
import logging
from typing import Dict, Any
from pydantic import BaseModel, ValidationError
from fastapi import UploadFile, HTTPException

from PIL import Image
import pytesseract
import pdfplumber

from app.ollama_client import query_ollama

logger = logging.getLogger(__name__)

# 4.1 Define Pydantic models for different form types

class StudentLoanForm(BaseModel):
    applicant_name: str
    date_of_birth: str  # ISO date or specific format
    institution_name: str
    course_name: str
    course_duration_years: str
    annual_tuition_fee: str
    co_signer_name: str | None = None
    # ... add fields required by the student loan application

# Map form_type to the Pydantic model
FORM_MODELS = {
    "student_loan": StudentLoanForm,
    # Add other form types: e.g., "home_loan": HomeLoanForm, etc.
}

# 4.2 OCR function

def ocr_image(img: Image.Image) -> str:
    """
    Run Tesseract OCR on a PIL Image, return extracted text.
    """
    # You can pass configs to tesseract if needed, e.g., '--psm 1'
    text = pytesseract.image_to_string(img)
    return text

def extract_text_from_upload(file: UploadFile) -> str:
    """
    Given an UploadFile (PDF or image), return concatenated raw text via OCR (and PDF text if available).
    """
    filename = file.filename.lower()
    data = file.file.read()
    # Work in a temp file or BytesIO
    if filename.endswith(".pdf"):
        text_chunks = []
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(data)
            tmp.flush()
            tmp_path = tmp.name
        try:
            with pdfplumber.open(tmp_path) as pdf:
                for page in pdf.pages:
                    # First try extracting embedded text
                    page_text = page.extract_text()
                    if page_text:
                        text_chunks.append(page_text)
                    # Also run OCR on page image if needed
                    try:
                        pil_img = page.to_image(resolution=300).original
                        ocr_txt = ocr_image(pil_img)
                        text_chunks.append(ocr_txt)
                    except Exception as e:
                        logger.warning(f"OCR on PDF page failed: {e}")
        finally:
            os.remove(tmp_path)
        return "\n".join(text_chunks)
    else:
        # Assume image
        try:
            img = Image.open(io.BytesIO(data))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Cannot open image: {e}")
        return ocr_image(img)

# 4.3 Build prompt for SLM to extract desired fields

def build_extraction_prompt(form_type: str, raw_text: str) -> str:
    """
    Given form_type and raw_text, construct a prompt for the SLM to extract required fields.
    """
    model = FORM_MODELS.get(form_type)
    if not model:
        raise ValueError(f"Unsupported form_type: {form_type}")
    # List fields and types
    fields = list(model.model_fields.keys()) if hasattr(model, "model_fields") else list(model.__fields__.keys())
    # Build instruction: ask SLM to output a JSON with exactly these keys.
    prompt = f"""
You are a form-filling assistant. Given the OCR-extracted text from a document, extract the following fields exactly in JSON, no extra keys or commentary:
Fields: {fields}
Text:
\"\"\"
{raw_text[:5000]}  # truncate if too long; you may pass more in chunks
\"\"\"
Return a JSON object with keys {fields}. If a field cannot be found, return an empty string for its value.
Do NOT output anything else.
"""
    return prompt.strip()

# 4.4 Main parse function

async def parse_uploaded_form(form_type: str, file: UploadFile) -> Dict[str, Any]:
    """
    Process the uploaded file, run OCR+SLM extraction, validate via Pydantic, and return dict.
    """
    # 1. Extract raw text
    raw_text = extract_text_from_upload(file)

    # 2. Build prompt
    prompt = build_extraction_prompt(form_type, raw_text)

    # 3. Query local SLM
    raw_output = query_ollama(prompt)
    # 4. Parse JSON
    import json
    try:
        parsed = json.loads(raw_output)
    except json.JSONDecodeError as e:
        logger.error(f"SLM output not valid JSON: {e}: {raw_output}")
        raise HTTPException(status_code=500, detail="Failed to parse SLM output as JSON")

    # 5. Validate against Pydantic
    Model = FORM_MODELS[form_type]
    try:
        validated = Model(**parsed)
    except ValidationError as ve:
        logger.error(f"Validation error on extracted fields: {ve}")
        # Optionally: you could return partial data or ask for manual corrections.
        raise HTTPException(status_code=500, detail=f"Extracted data invalid: {ve}")

    # 6. Return dict of validated fields
    return validated.model_dump() if hasattr(validated, "model_dump") else validated.dict()
