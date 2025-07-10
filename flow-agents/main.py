import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from browser_toolkit import BrowserUseToolkit
from baml_client import b, types
import asyncio
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

browser_toolkit = BrowserUseToolkit()

# Error categories that should stop execution
CRITICAL_ERRORS = [
    "account is locked",
    "exceeded the maximum number of limits",
    "blocked",
    "invalid credentials",
    "session expired",
    "unauthorized access",
    "service unavailable",
    "maximum attempts exceeded"
]

# Recoverable errors that can be retried
RECOVERABLE_ERRORS = [
    "network",
    "timeout",
    "connection",
    "temporary"
]

@app.route("/api/browser/execute", methods=["POST"])
async def handle_browser_task():
    data = request.get_json()
    if not data:
        return jsonify({"error": "form_data is required"}), 400

    current_status = data.get('current_status') or {
        "step_index": 0,
        "current_step_summary": "",
        "url": "",
        "awaiting_user_input": False,
        "requested_input_type": None,
        "task_complete": False,
        "error_message": "",
        "next_expected_action": "",
        "page_state": ""
    }

    form_data = data.get('form_data', {})
    
    # Convert to BAML types
    status_obj = types.FormFillingStatus(**current_status)
    
    max_iterations = 15  # Reduced from 20
    iteration_count = 0
    consecutive_failures = 0
    max_consecutive_failures = 3
    last_step_index = status_obj.step_index
    step_retry_count = 0
    max_step_retries = 2
    
    # Track execution time to prevent infinite loops
    start_time = datetime.now()
    max_execution_time = timedelta(minutes=10)

    logger.info(f"🚀 Starting browser automation from step {status_obj.step_index}")

    while iteration_count < max_iterations:
        # Check execution time limit
        if datetime.now() - start_time > max_execution_time:
            logger.error("⏰ Maximum execution time exceeded")
            status_obj.error_message = "Execution timeout: Maximum time limit exceeded"
            break

        iteration_count += 1
        logger.info(f"🔄 Iteration {iteration_count}, Step {status_obj.step_index}")
        
        # Check if we're stuck on the same step
        if status_obj.step_index == last_step_index:
            step_retry_count += 1
            if step_retry_count > max_step_retries:
                logger.error(f"🚫 Stuck on step {status_obj.step_index} after {max_step_retries} retries")
                status_obj.error_message = f"Failed to complete step {status_obj.step_index} after {max_step_retries} attempts"
                break
        else:
            # Reset retry count when moving to new step
            step_retry_count = 0
            last_step_index = status_obj.step_index

        try:
            # Get current browser state with error handling
            try:
                current_browser_state = await browser_toolkit.get_page_state()
                logger.info(f"📄 Current page state: {current_browser_state[:100]}...")
            except Exception as e:
                logger.error(f"❌ Failed to get page state: {e}")
                status_obj.error_message = f"Browser state error: {str(e)}"
                break

            # Check for critical errors in page state
            if is_critical_error_in_state(current_browser_state):
                logger.error("🚫 Critical error detected in page state")
                status_obj.error_message = "Critical error detected on page"
                break

            # Let BAML decide what to do next
            try:
                action_decision = b.FormFilling(
                    task_steps="Ayushman Bharat Card Registration",
                    current_status=status_obj,
                    current_browser_state=current_browser_state,
                    phone=form_data.get('phone', "9330575742"),
                    aadhaar_number=form_data.get('aadhaar_number', "123412341234"),
                    aadhar_otp=form_data.get('aadhar_otp'),
                    dob=form_data.get('dob', "1950-01-01"),
                    relationship=form_data.get('relationship', "Self"),
                    pin_code=form_data.get('pin_code', "110001"),
                    district=form_data.get('district', "New Delhi"),
                    sub_district=form_data.get('sub_district', "Chanakyapuri"),
                    village=form_data.get('village', "VillageName"),
                    area_type=form_data.get('area_type', "Urban"),
                    family_id=form_data.get('family_id', "FAM123")
                )
                # --- Fix: Ensure url is always a string ---
                if hasattr(action_decision, 'url') and action_decision.url is None:
                    action_decision.url = ""
            except Exception as e:
                logger.error(f"❌ BAML decision error: {e}")
                status_obj.error_message = f"Decision engine error: {str(e)}"
                break
            
            logger.info(f"🎯 BAML Decision: {action_decision.current_step_summary}")
            
            # Validate action decision
            if not is_valid_action_decision(action_decision, status_obj):
                logger.error("🚫 Invalid action decision received")
                status_obj.error_message = "Invalid action decision from decision engine"
                break

            # Execute the browser action
            execution_result = await browser_toolkit.execute_action(action_decision, form_data)
            
            # Process execution result
            if execution_result.get('success', False):
                # Success case
                consecutive_failures = 0  # Reset failure counter
                status_obj.step_index = action_decision.step_index
                status_obj.current_step_summary = action_decision.current_step_summary
                status_obj.url = execution_result.get('url', status_obj.url)
                status_obj.error_message = ""
                status_obj.next_expected_action = action_decision.next_expected_action
                status_obj.page_state = execution_result.get('page_state', '')
                
                # Handle special states
                if action_decision.awaiting_user_input:
                    status_obj.awaiting_user_input = True
                    status_obj.requested_input_type = action_decision.requested_input_type
                    logger.info(f"⏸️ Awaiting user input: {action_decision.requested_input_type}")
                    break
                    
                if action_decision.task_complete:
                    status_obj.task_complete = True
                    logger.info("✅ Task completed successfully!")
                    break
                    
            else:
                # Failure case
                consecutive_failures += 1
                error_message = execution_result.get('error', 'Unknown execution error')
                status_obj.error_message = error_message
                logger.error(f"❌ Execution failed: {error_message}")
                
                # Check if awaiting user input
                if execution_result.get('awaiting_user_input'):
                    status_obj.awaiting_user_input = True
                    status_obj.requested_input_type = execution_result.get('requested_input_type')
                    logger.info(f"⏸️ Awaiting user input: {execution_result.get('requested_input_type')}")
                    break
                
                # Check for critical errors
                if is_critical_error(error_message):
                    logger.error("🚫 Critical error detected, stopping execution")
                    break
                
                # Check consecutive failures
                if consecutive_failures >= max_consecutive_failures:
                    logger.error(f"🚫 Too many consecutive failures ({consecutive_failures})")
                    status_obj.error_message = f"Automation failed after {consecutive_failures} consecutive attempts"
                    break
                
                # Handle specific error types
                if is_recoverable_error(error_message):
                    logger.info("🔄 Recoverable error, retrying...")
                    await asyncio.sleep(2)  # Brief pause before retry
                    continue
                else:
                    logger.error("🚫 Non-recoverable error, stopping execution")
                    break

        except Exception as e:
            consecutive_failures += 1
            logger.error(f"🚨 Unexpected error: {e}")
            status_obj.error_message = f"System error: {str(e)}"
            
            if consecutive_failures >= max_consecutive_failures:
                logger.error("🚫 Too many consecutive system errors")
                break
            
            # Brief pause before retry
            await asyncio.sleep(2)

    # Final status determination
    final_status = determine_final_status(status_obj, iteration_count, max_iterations)
    
    # Convert back to dict for JSON response
    response_data = {
        "status": final_status,
        "step_index": status_obj.step_index,
        "current_step_summary": status_obj.current_step_summary,
        "url": status_obj.url,
        "awaiting_user_input": status_obj.awaiting_user_input,
        "requested_input_type": status_obj.requested_input_type,
        "task_complete": status_obj.task_complete,
        "error_message": status_obj.error_message,
        "next_expected_action": status_obj.next_expected_action,
        "page_state": status_obj.page_state,
        "iterations_completed": iteration_count,
        "execution_time_seconds": (datetime.now() - start_time).total_seconds()
    }
    
    logger.info(f"🏁 Execution finished with status: {final_status}")
    return jsonify(response_data)

def is_critical_error(error_message: str) -> bool:
    """Check if error is critical and should stop execution"""
    if not error_message:
        return False
    
    error_lower = error_message.lower()
    return any(critical_error in error_lower for critical_error in CRITICAL_ERRORS)

def is_recoverable_error(error_message: str) -> bool:
    """Check if error is recoverable and can be retried"""
    if not error_message:
        return False
    
    error_lower = error_message.lower()
    return any(recoverable_error in error_lower for recoverable_error in RECOVERABLE_ERRORS)

def is_critical_error_in_state(page_state: str) -> bool:
    """Check if page state indicates critical errors"""
    if not page_state:
        return False
    
    state_lower = page_state.lower()
    critical_indicators = [
        "access denied",
        "account locked",
        "service unavailable",
        "maintenance mode",
        "error 500",
        "error 503",
        "session expired"
    ]
    
    return any(indicator in state_lower for indicator in critical_indicators)

def is_valid_action_decision(action_decision, current_status) -> bool:
    """Validate action decision from BAML"""
    try:
        # Check if required fields exist
        if not hasattr(action_decision, 'step_index') or not hasattr(action_decision, 'current_step_summary'):
            return False
        
        # Check if step index is reasonable
        if action_decision.step_index < 0 or action_decision.step_index > 20:
            return False
        
        # Check if step is progressing (not going backwards unless retry)
        if action_decision.step_index < current_status.step_index - 1:
            return False
        
        return True
    except Exception:
        return False

def determine_final_status(status_obj, iteration_count, max_iterations) -> str:
    """Determine final status based on execution result"""
    if status_obj.task_complete:
        return "completed"
    elif status_obj.awaiting_user_input:
        return "awaiting_input"
    elif iteration_count >= max_iterations:
        return "timeout"
    elif status_obj.error_message:
        if is_critical_error(status_obj.error_message):
            return "critical_error"
        else:
            return "error"
    else:
        return "stopped"

@app.route("/api/browser/submit_input", methods=["POST"])
async def submit_user_input():
    """Handle user input submission (OTP, Captcha, etc.)"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "input_data is required"}), 400
    
    input_type = data.get('input_type')
    input_value = data.get('input_value')
    
    if not input_type or not input_value:
        return jsonify({"error": "input_type and input_value are required"}), 400
    
    try:
        result = await browser_toolkit.submit_user_input(input_type, input_value)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error submitting user input: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/browser/status", methods=["GET"])
async def get_browser_status():
    """Get current browser state"""
    try:
        state = await browser_toolkit.get_page_state()
        return jsonify({"page_state": state})
    except Exception as e:
        logger.error(f"Error getting browser status: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/browser/reset", methods=["POST"])
async def reset_browser():
    """Reset browser session"""
    try:
        # Reset the browser toolkit
        global browser_toolkit
        browser_toolkit = BrowserUseToolkit()
        logger.info("🔄 Browser session reset")
        return jsonify({"success": True, "message": "Browser session reset successfully"})
    except Exception as e:
        logger.error(f"Error resetting browser: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)