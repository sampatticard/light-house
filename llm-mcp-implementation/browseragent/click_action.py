from pydantic import BaseModel
from typing import Literal, Optional

class ClickAction(BaseModel):
    action: Literal["click"]
    selector: str
    wait_for: Optional[str] = None
