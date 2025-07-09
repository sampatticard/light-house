from pydantic import BaseModel
from typing import Literal, Optional

class WaitAction(BaseModel):
    action: Literal["wait"]
    selector: Optional[str] = None
    timeout: int = 5000
