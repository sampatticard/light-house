from pydantic import BaseModel, HttpUrl
from typing import Literal

class NavigateAction(BaseModel):
    action: Literal["navigate"]
    url: HttpUrl
