# app/schemas.py

from pydantic import BaseModel, Field, HttpUrl, field_validator
from app.actions import ActionName

class BaseActionParams(BaseModel):
    pass

class CheckHomeLoansParams(BaseActionParams):
    annual_income: float = Field(..., gt=0, description="Annual income in INR")
    credit_score: int = Field(..., ge=300, le=900)

class CheckMSMELoansParams(BaseActionParams):
    annual_revenue: float = Field(..., gt=0, description="Annual revenue in INR")
    industry: str = Field(..., min_length=2)

class ExtractRateBankParams(BaseActionParams):
    loan_type: str = Field(..., description="E.g., 'home loan', 'car loan'")
    bank_domain: str = Field(..., description="Domain without protocol, e.g. examplebank.com")

    @field_validator("bank_domain")
    def validate_whitelist(cls, v):
        # Whitelist domains; you can load from config
        allowed = {"examplebank.com", "anotherbank.in"}
        if v not in allowed:
            raise ValueError(f"Domain {v} not in allowed list")
        return v

# Map action names to their param model classes
ACTION_PARAM_MODELS = {
    ActionName.CHECK_HOME_LOANS: CheckHomeLoansParams,
    ActionName.CHECK_MSME_LOANS: CheckMSMELoansParams,
    ActionName.EXTRACT_RATE_BANK: ExtractRateBankParams,
    # ...
}
