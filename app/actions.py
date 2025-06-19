# app/actions.py

from enum import Enum
from typing import TypedDict, Dict

class ActionName(str, Enum):
    CHECK_HOME_LOANS = "check_home_loans"
    CHECK_MSME_LOANS = "check_msme_loans"
    EXTRACT_RATE_BANK = "extract_rate_bank"
    # ... add more as needed

# Define the parameters expected per action:
# We’ll use Pydantic models for validation (next section).

# Prompt templates: use Python format strings.
PROMPT_TEMPLATES: Dict[ActionName, str] = {
    ActionName.CHECK_HOME_LOANS: """
You are a browser automation generator. Output ONLY a JSON array of actions in the DSL:
  - navigate, click, type, wait, extract.
Your goal: find home loan eligibility requirements for a borrower with:
  - annual_income: {annual_income}
  - credit_score: {credit_score}
On a known, whitelisted site (e.g., examplebank.com). Only navigate to examplebank.com URLs.
Generate actions to navigate the site’s home loan page, extract key eligibility criteria (e.g., min income, max loan amount).
Return a JSON array only.
""".strip(),
    ActionName.CHECK_MSME_LOANS: """
You are a browser automation generator. Output ONLY a JSON array of actions in the DSL.
Goal: find MSME loan schemes for a business with:
  - annual_revenue: {annual_revenue}
  - industry: "{industry}"
Search on examplebank.com’s MSME section. Only navigate within examplebank.com domain.
Return JSON array only.
""".strip(),
    ActionName.EXTRACT_RATE_BANK: """
You are a browser automation generator. Output ONLY a JSON array of actions in the DSL.
Goal: extract the current interest rate for {loan_type} from {bank_domain}. 
Only navigate to URLs under {bank_domain}. 
Generate actions to go to the homepage of {bank_domain}, click “Loans” → "{loan_type}" section, extract the main interest rate element.
Return JSON array only.
""".strip(),
    # ...more templates
}
