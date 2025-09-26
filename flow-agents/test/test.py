import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import asyncio
from typing import Optional
from pydantic import BaseModel
from browser_use import Agent, BrowserSession, Controller
from browser_use.llm import ChatOpenAI

# === Form status model ===
class FormFillingStatusOutput(BaseModel):
    success: bool
    step_index: int
    current_step_summary: str
    next_expected_action: str
    page_state: str
    requested_input_type: Optional[str] = None
    error_message: Optional[str] = None
    task_complete: bool = False

# === Ayushman Bharat step template builder ===
def get_ayushman_step_templates(phone, otp, aadhaar, family_id, dob):
    return [
        "Navigate to https://beneficiary.nha.gov.in/ and verify that the homepage has fully loaded.",
        f"Enter mobile number: {phone}. Solve the captcha (if present) and click the 'Submit' or 'Verify' button.",
        f"Enter the received OTP: {otp} in the OTP field and click 'Login' or 'Verify'." if otp else "Awaiting user input: OTP is required to proceed.",
        "Find and click the appropriate registration or enrollment option for the beneficiary.",
        f"Enter Aadhaar number: {aadhaar}. Also enter Family ID: {family_id} if the field exists, then click 'Search'.",
        "Select 'Aadhaar OTP' eKYC method, if available.",
        "Click 'Verify' or 'Start eKYC' to begin Aadhaar authentication.",
        "On the consent screen, check 'I Agree' and click 'Allow' or 'Proceed'.",
        f"Enter the Aadhaar OTP: {otp} received on linked phone number." if otp else "Awaiting user input: Aadhaar OTP required for eKYC.",
        "Review Aadhaar details shown on screen and click 'Confirm' if correct.",
        "Enable camera access and capture the live photo. Then click 'Proceed'.",
        f"Fill final form fields such as DOB: {dob}, Phone: {phone}, and submit the application.",
        "Complete any remaining KYC checks as prompted.",
        "Click the 'Download' button to download Ayushman Bharat card PDF."
    ]

# === Async browser runner ===
async def execute_ayushman_step(step_index: int, form_data: dict) -> FormFillingStatusOutput:
    steps = get_ayushman_step_templates(
        phone=form_data.get("phone"),
        otp=form_data.get("otp"),
        aadhaar=form_data.get("aadhaar_number"),
        family_id=form_data.get("family_id"),
        dob=form_data.get("dob"),
    )

    if step_index >= len(steps):
        return FormFillingStatusOutput(
            success=True,
            step_index=step_index,
            current_step_summary="All steps completed.",
            next_expected_action="None",
            page_state="Final confirmation screen.",
            task_complete=True,
        )

    current_instruction = steps[step_index]

    prompt = f"""
You are an assistant helping to fill out the Ayushman Bharat form on the Indian government portal.

🧾 Current Step ({step_index + 1} of {len(steps)}):
{current_instruction}
"""

    prompt += """

🧠 Based on the web page and browser context, return a JSON status object in the following format:

```json
{
  "success": true,
  "step_index": %d,
  "current_step_summary": "Short description of the current step status",
  "next_expected_action": "What needs to be done next",
  "page_state": "What the page currently shows",
  "requested_input_type": "otp" | "captcha" | null,
  "error_message": "If anything failed",
  "task_complete": true | false
}
```

Only return valid JSON output.
""" % step_index

    llm = ChatOpenAI(model="gpt-4o")
    browser_session = BrowserSession(cdp_url="http://localhost:9222", keep_alive=True)
    await browser_session.start()

    controller = Controller(output_model=FormFillingStatusOutput)
    agent = Agent(
        task=prompt,
        llm=llm,
        browser_session=browser_session,
        controller=controller,
    )

    history = await agent.run()
    result_json = history.final_result()

    return FormFillingStatusOutput.model_validate_json(result_json)

# === Flask App ===
app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

form_state = {
    "step_index": 0,
    "phone": "",
    "otp": None,
    "aadhaar_number": "",
    "family_id": "",
    "dob": ""
}

@app.route("/api/browser/execute", methods=["POST"])
def handle_browser_task():
    data = request.get_json()
    if not data:
        return jsonify({"error": "form_data is required"}), 400

    form_state.update({k: data.get(k, form_state.get(k)) for k in form_state})

    try:
        # Run the async step in the event loop
        status = asyncio.run(execute_ayushman_step(form_state["step_index"], form_state))
        form_state["step_index"] += 1 if not status.task_complete else 0

        return jsonify({
            "status": "completed" if status.task_complete else "in_progress",
            **status.model_dump()
        })
    except Exception as e:
        logger.error(f"Error executing browser task: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/browser/submit_input", methods=["POST"])
def submit_user_input():
    data = request.get_json()
    input_type = data.get('input_type')
    input_value = data.get('input_value')

    if input_type in form_state:
        form_state[input_type] = input_value

    return jsonify({"success": True, "message": f"{input_type} received."})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
