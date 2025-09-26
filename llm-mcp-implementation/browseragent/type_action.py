from pydantic import BaseModel
from typing import Literal, Optional

class TypeAction(BaseModel):
    action: Literal["type"]
    selector: str
    text: str
    clear: bool = True
    delay: Optional[int] = None
