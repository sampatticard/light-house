from steps.step_templates import get_ayushman_step_templates
import logging
logger = logging.getLogger(__name__)

def get_form_step(status: dict, form_data: dict):
    step_index = status.get("step_index", 0)
    phone = form_data.get("phone", "9330575742")
    otp = form_data.get("otp")
    aadhaar = form_data.get("aadhaar_number", "")
    family_id = form_data.get("family_id", "")
    dob = form_data.get("dob", "")

    steps = get_ayushman_step_templates(phone, otp, aadhaar, family_id, dob)

    if step_index >= len(steps):
        logger.info(f"[get_form_step] step_index={step_index}, returning: All steps completed.")
        return "All steps completed.", False, None

    current_step = steps[step_index]
    logger.info(f"[get_form_step] step_index={step_index}, current_step: {current_step}")

    # If this is the OTP step and no OTP is present, explicitly request OTP input
    if step_index == 2 and not otp:
        logger.info(f"[get_form_step] Awaiting user input: otp (explicit OTP step)")
        return current_step, True, "otp"

    # Explicitly check for OTP step (fallback for other OTP steps)
    if ("OTP" in current_step and ("enter" in current_step.lower() or "input" in current_step.lower())) or "otp" in current_step.lower():
        logger.info(f"[get_form_step] Awaiting user input: otp")
        return current_step, True, "otp"

    # Generic user input detection fallback
    if "Awaiting user input" in current_step:
        input_type = "manual_action"
        logger.info(f"[get_form_step] Awaiting user input: {input_type}")
        return current_step, True, input_type

    return current_step, False, None 