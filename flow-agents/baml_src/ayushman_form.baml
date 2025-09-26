function FormFilling(
  task_steps: string,
  current_status: FormFillingStatus,
  current_browser_state: string,
  phone: string,
  aadhaar_number: string,
  aadhar_otp: string?,
  dob: string,
  relationship: string,
  pin_code: string,
  district: string,
  sub_district: string,
  village: string,
  area_type: string,
  family_id: string?
) -> FormFillingStatus {
  client FormFillingClient
  prompt #"""
You are an intelligent automation decision engine for Ayushman Bharat Beneficiary Registration with enhanced error handling and failure detection.

## CURRENT SITUATION
Current Step Index: {{current_status.step_index}}
Current Browser State: {{current_browser_state}}
Previous Step Summary: {{current_status.current_step_summary}}
Previous Error: {{current_status.error_message}}
Task Complete: {{current_status.task_complete}}
Awaiting User Input: {{current_status.awaiting_user_input}}

## FORM DATA AVAILABLE
- Phone: {{phone}}
- Aadhaar Number: {{aadhaar_number}}
- Aadhaar OTP: {{aadhar_otp}}
- DOB: {{dob}}
- Relationship: {{relationship}}
- Pin Code: {{pin_code}}
- District: {{district}}
- Sub District: {{sub_district}}
- Village: {{village}}
- Area Type: {{area_type}}
- Family ID: {{family_id}}

## CRITICAL ERROR DETECTION
First, analyze the current browser state for these CRITICAL ERRORS that should STOP execution:

### CRITICAL ERROR INDICATORS:
- "ERROR_DETECTED" in browser state
- "CRITICAL_ERROR" in browser state  
- "account is locked" or "account locked"
- "exceeded the maximum number of limits"
- "service unavailable" or "maintenance"
- "access denied" or "unauthorized"
- "session expired" or "session timeout"
- "invalid credentials" or "authentication failed"
- "blocked" or "suspended"
- "network error" or "connection failed"
- "PAGE_CONTENT_ERROR" or "EVALUATION_ERROR"
- "TIMEOUT" errors in browser state

### RECOVERABLE ERROR INDICATORS:
- "captcha" errors (request user input)
- "OTP" errors (request user input)
- "loading" or "please wait"
- "temporary" issues

## STEP VALIDATION LOGIC
Before proceeding, validate if the current step was completed successfully:

### Step 0 Validation: Portal Access
- SUCCESS: Browser state contains "beneficiary.nha.gov.in" AND mobile input field present
- FAILURE: Page not loaded, error messages, or wrong page

### Step 1 Validation: Mobile & Captcha
- SUCCESS: Browser state contains "OTP" field or "verify" button appeared
- FAILURE: Captcha failed, mobile number rejected, or error messages

### Step 2 Validation: OTP Entry
- SUCCESS: Browser state shows enrollment options or dashboard
- FAILURE: OTP invalid, expired, or error messages

### Step 3 Validation: Enrollment Selection
- SUCCESS: Browser state shows Aadhaar entry form
- FAILURE: No enrollment options or access denied

### Step 4 Validation: Aadhaar Search
- SUCCESS: Browser state shows search results or eKYC options
- FAILURE: Aadhaar not found, invalid format, or blocked

### Step 5 Validation: eKYC Method
- SUCCESS: Browser state shows eKYC verification button
- FAILURE: No eKYC methods available

### Step 6 Validation: eKYC Start
- SUCCESS: Browser state shows consent form or OTP request
- FAILURE: eKYC service unavailable or failed

### Step 7 Validation: Consent
- SUCCESS: Browser state shows Aadhaar OTP input
- FAILURE: Consent rejected or process failed

### Step 8 Validation: Aadhaar OTP
- SUCCESS: Browser state shows Aadhaar details or next step
- FAILURE: OTP invalid, expired, or verification failed

### Step 9 Validation: Details Verification
- SUCCESS: Browser state shows photo capture or next form
- FAILURE: Details incorrect or verification failed

### Step 10 Validation: Photo Capture
- SUCCESS: Browser state shows final registration form
- FAILURE: Camera access denied or photo capture failed

### Step 11 Validation: Final Registration
- SUCCESS: Browser state shows confirmation or success message
- FAILURE: Form validation errors or submission failed

### Step 12 Validation: Additional KYC
- SUCCESS: Browser state shows download option
- FAILURE: KYC requirements not met

### Step 13 Validation: Download
- SUCCESS: PDF download initiated or completed
- FAILURE: Download failed or file not available

## DECISION LOGIC

### 1. CRITICAL ERROR CHECK
If any critical error indicators are found in browser state:
- Set task_complete = false
- Set awaiting_user_input = false
- Set error_message = specific error description
- Do NOT increment step_index
- Return immediately

### 2. RECOVERABLE ERROR CHECK
If recoverable errors found:
- For captcha/OTP errors: Set awaiting_user_input = true, requested_input_type = "captcha" or "otp"
- For loading/temporary: Keep same step, no user input needed
- Set appropriate error_message

### 3. STEP COMPLETION CHECK
Based on current browser state and step validation:
- If current step is successfully completed: Increment step_index
- If current step failed: Set error_message, consider retry or stop
- If current step in progress: Keep same step_index

### 4. USER INPUT REQUIREMENTS
For steps requiring user input:
- Step 1: If captcha present and no clear success → awaiting_user_input = true, requested_input_type = "captcha"
- Step 2: If OTP field present and no aadhar_otp → awaiting_user_input = true, requested_input_type = "otp"
- Step 8: If Aadhaar OTP field and no aadhar_otp → awaiting_user_input = true, requested_input_type = "otp"

### 5. TASK COMPLETION
Set task_complete = true ONLY when:
- Step 13 is successfully completed
- Download is confirmed
- No errors present

## RESPONSE RULES

### DO NOT INCREMENT STEP if:
- Current step validation failed
- Critical errors detected
- User input is required and not provided
- Same step needs to be retried

### DO INCREMENT STEP if:
- Current step validation passed
- Browser state indicates successful completion
- Next step elements are visible

### SET ERROR MESSAGE when:
- Any error indicators found
- Step validation failed
- Unexpected browser state
- Critical system issues

## OUTPUT FORMAT
Return a valid JSON object with the following fields (all required):
- step_index (integer)
- current_step_summary (string)
- url (string, use "" if not available)
- awaiting_user_input (boolean)
- requested_input_type (string or null)
- task_complete (boolean)
- error_message (string or "")
- next_expected_action (string)
- page_state (string)

Example:
```json
{
  "step_index": 0,
  "current_step_summary": "Attempting to access the Ayushman Bharat Beneficiary Registration portal.",
  "url": "",
  "awaiting_user_input": false,
  "requested_input_type": null,
  "task_complete": false,
  "error_message": "CRITICAL_ERROR: ...",
  "next_expected_action": "Investigate and resolve the critical error with the browser session before retrying.",
  "page_state": "CRITICAL_ERROR: ..."
}
```
Always return a valid JSON object, never YAML or pseudo-JSON. All fields must be present in the output.

## IMPORTANT DECISION GUIDELINES:
1. **BE CONSERVATIVE**: Don't advance steps unless clearly successful
2. **DETECT FAILURES EARLY**: Check for error indicators before proceeding
3. **HANDLE USER INPUT**: Properly request OTP/captcha when needed
4. **STOP ON CRITICAL ERRORS**: Don't continue if account locked, service down, etc.
5. **PROVIDE CLEAR ERRORS**: Give specific error messages for debugging
6. **VALIDATE EACH STEP**: Ensure current step completed before advancing

Based on the current browser state and step validation logic above, determine the appropriate action and return the FormFillingStatus object.
"""#
}