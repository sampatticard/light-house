class PromptBuilder:
    def __init__(self):
        pass

    def build_ayushman_prompt(self, action_decision, form_data):
        # Example for Ayushman Bharat, can be extended for other forms
        step_index = action_decision.step_index
        base_action = action_decision.current_step_summary
        phone = form_data.get('phone', '')
        if step_index == 1 and phone:
            base_action = f"Fill mobile number: {phone}. Fill captcha if present. Click submit/verify button."
        return f"""
AYUSHMAN BHARAT AUTOMATION - STEP {step_index}

TASK: {base_action}

CRITICAL INSTRUCTIONS:
1. Wait for elements to load (max 15 seconds per element)
2. If any element not found, report: "Element not found: [description]"
3. If any action fails, report: "Action failed: [description]"
4. If page shows errors, report: "Page error: [message]"
5. Take screenshot when errors occur
6. Maximum step execution time: 2 minutes
7. Report success only when expected outcome achieved

ERROR HANDLING:
- Network issues: Report "Network error: [details]"
- Timeout issues: Report "Timeout error: [details]"
- Validation errors: Report "Validation error: [details]"
- Unexpected content: Report "Unexpected content: [details]"

SUCCESS CRITERIA:
- All required actions completed successfully
- Expected page elements appear
- No error messages on page
- Progression to next step is possible

Stop immediately if any critical error occurs and report the specific issue.
"""

    def build_insurance_prompt(self, action_decision, form_data):
        step_index = action_decision.step_index
        base_action = action_decision.current_step_summary
        name = form_data.get('name', '')
        dob = form_data.get('dob', '')
        policy_number = form_data.get('policy_number', '')
        if step_index == 1 and name and dob and policy_number:
            base_action = f"Fill name: {name}. Fill date of birth: {dob}. Fill policy number: {policy_number}. Click next."
        return f"""
INSURANCE FORM AUTOMATION - STEP {step_index}

TASK: {base_action}

CRITICAL INSTRUCTIONS:
1. Wait for elements to load (max 15 seconds per element)
2. If any element not found, report: "Element not found: [description]"
3. If any action fails, report: "Action failed: [description]"
4. If page shows errors, report: "Page error: [message]"
5. Take screenshot when errors occur
6. Maximum step execution time: 2 minutes
7. Report success only when expected outcome achieved

ERROR HANDLING:
- Network issues: Report "Network error: [details]"
- Timeout issues: Report "Timeout error: [details]"
- Validation errors: Report "Validation error: [details]"
- Unexpected content: Report "Unexpected content: [details]"

SUCCESS CRITERIA:
- All required actions completed successfully
- Expected page elements appear
- No error messages on page
- Progression to next step is possible

Stop immediately if any critical error occurs and report the specific issue.
""" 