import io
import os
import tempfile
from pathlib import Path
from PIL import Image
import pdfplumber
import easyocr
import yaml
from fastapi import UploadFile

FORM_CONFIG_DIR = Path(__file__).parent.parent / "configs" / "forms"
MAX_CHARS = 5000

def load_form_config(form_type: str):
    path = FORM_CONFIG_DIR / f"{form_type}.yaml"
    if not path.exists(): raise ValueError(f"No config for {form_type}")
    return yaml.safe_load(path.read_text())

def extract_text_from_upload(file: UploadFile) -> str:
    data = file.file.read() ; name = file.filename.lower()
    if name.endswith(".pdf"):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(data); tmp.flush(); pdf_path=tmp.name
            txts=[]
        with pdfplumber.open(pdf_path) as pdf:
            for p in pdf.pages:
                t=p.extract_text() or ""; txts.append(t)
                img=p.to_image(resolution=300).original; txts.append(easyocr.ocr_image(img))
            os.remove(pdf_path)
        return "\n".join(txts)
    else:
        img=Image.open(io.BytesIO(data)); return easyocr.ocr_image(img)
