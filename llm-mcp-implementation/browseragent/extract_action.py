from pydantic import BaseModel
from typing import Literal, Optional

class ExtractAction(BaseModel):
    action: Literal["extract"]
    selector: str
    attribute: Optional[str] = None
