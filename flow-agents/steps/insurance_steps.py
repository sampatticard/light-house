def get_insurance_step_templates(name, dob, policy_number, otp):
    return [
        "Navigate to the insurance portal and verify successful page load.",
        f"Fill name: {name}. Fill date of birth: {dob}. Fill policy number: {policy_number}. Click next.",
        f"Enter OTP: {otp} in OTP field. Click verify button." if otp else "Awaiting user input: OTP is required to proceed.",
        "Review policy details and confirm.",
        "Download or print the insurance document."
    ]

def get_form_step(status: dict, form_data: dict):
    step_index = status.get("step_index", 0)
    name = form_data.get("name", "John Doe")
    dob = form_data.get("dob", "1990-01-01")
    policy_number = form_data.get("policy_number", "POL123456")
    otp = form_data.get("otp")

    steps = get_insurance_step_templates(name, dob, policy_number, otp)

    if step_index >= len(steps):
        return "All steps completed.", False, None

    current_step = steps[step_index]
    if "Awaiting user input" in current_step:
        input_type = "otp" if "OTP" in current_step else "manual_action"
        return current_step, True, input_type

    return current_step, False, None 