# Step templates for generic and Ayushman Bharat form automation

def get_ayushman_step_templates(phone, otp, aadhaar, family_id, dob):
    return [
        "Navigate to https://beneficiary.nha.gov.in/ and verify successful page load. If already opened, do not reopen. If not accessible, retry once or show minimal fallback.",
        f"Fill mobile number: {phone}. Solve captcha if present. Click submit/verify button.",
        f"Enter OTP: {otp} in OTP field. Click login/verify button." if otp else "Awaiting user input: OTP is required to proceed.",
        "Find and click enrollment/registration option appropriate for age and eligibility.",
        f"Enter Aadhaar number: {aadhaar}. Fill Family ID: {family_id} if field exists. Click search.",
        "Select 'Aadhaar OTP' eKYC method if available.",
        "Click 'Verify' or 'Start eKYC' button to begin verification.",
        "Accept consent form by checking 'I Agree' and clicking 'Allow' or 'Proceed'.",
        f"Enter Aadhaar OTP: {otp} for eKYC verification." if otp else "Awaiting user input: Aadhaar OTP is required for eKYC verification.",
        "Review displayed Aadhaar details and click 'Confirm' if correct.",
        "Enable camera access and capture photo. Click 'Proceed' after photo taken.",
        f"Fill final form with: Phone={phone}, DOB={dob}, etc. Submit form.",
        "Complete any additional KYC requirements as prompted.",
        "Click 'Download' button to download Ayushman Bharat card PDF."
    ] 