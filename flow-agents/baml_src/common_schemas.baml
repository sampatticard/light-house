class FormFillingStatus {
  step_index int @description("Current step number (0-based)")
  current_step_summary string @description("Summary of the current step")
  url string @description("Current page URL")
  awaiting_user_input bool @description("True if paused for input like OTP")
  requested_input_type string? @description("Type of input requested, e.g., 'otp', 'captcha', or empty if not waiting")
  task_complete bool @description("True if all steps are done")
  error_message string? @description("Error message if something went wrong")
  next_expected_action string? @description("What will happen next")
  page_state string? @description("What's currently visible on the page")
}