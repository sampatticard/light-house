import logging
from browser_toolkit import BrowserUseToolkit
from baml_client import b, types
from datetime import datetime, timedelta
from steps.ayushman_steps import get_form_step as get_ayushman_form_step
from steps.insurance_steps import get_form_step as get_insurance_form_step

logger = logging.getLogger(__name__)

class AutomationService:
    def __init__(self):
        self.browser_toolkit = BrowserUseToolkit()

    async def run_automation(self, current_status, form_data, form_type="ayushman"):
        logger.info(f"[run_automation] ENTRY: current_status={current_status}, form_data={form_data}, form_type={form_type}")
        # Select step logic and prompt builder based on form_type
        if form_type == "insurance":
            get_form_step = get_insurance_form_step
            build_prompt = self.browser_toolkit.prompt_builder.build_insurance_prompt
        else:
            get_form_step = get_ayushman_form_step
            build_prompt = self.browser_toolkit.prompt_builder.build_ayushman_prompt

        status_obj = types.FormFillingStatus(**current_status)
        max_iterations = 15
        iteration_count = 0
        consecutive_failures = 0
        max_consecutive_failures = 3
        last_step_index = status_obj.step_index
        step_retry_count = 0
        max_step_retries = 2
        start_time = datetime.now()
        max_execution_time = timedelta(minutes=10)

        logger.info(f"🚀 [run_automation] Starting browser automation from step {status_obj.step_index}")

        status = "error"  # Default value in case of early exit
        result = None     # Default value for agent result

        while iteration_count < max_iterations:
            logger.info(f"[run_automation] Iteration {iteration_count}, Step {status_obj.step_index}")
            if datetime.now() - start_time > max_execution_time:
                logger.error("⏰ Maximum execution time exceeded")
                status_obj.error_message = "Execution timeout: Maximum time limit exceeded"
                break
            iteration_count += 1
            if status_obj.step_index == last_step_index:
                step_retry_count += 1
                if step_retry_count > max_step_retries:
                    logger.error(f"🚫 Stuck on step {status_obj.step_index} after {max_step_retries} retries")
                    status_obj.error_message = f"Failed to complete step {status_obj.step_index} after {max_step_retries} attempts"
                    break
            else:
                step_retry_count = 0
                last_step_index = status_obj.step_index
            try:
                logger.info(f"[run_automation] Calling get_form_step with status: {status_obj.__dict__}, form_data: {form_data}")
                current_step, awaiting_user_input, input_type = get_form_step(status_obj.__dict__, form_data)
                logger.info(f"[run_automation] get_form_step returned: current_step={current_step}, awaiting_user_input={awaiting_user_input}, input_type={input_type}")
                # Build the prompt for the agent
                action_decision = type('ActionDecision', (object,), {
                    'step_index': status_obj.step_index,
                    'current_step_summary': current_step
                })()
                prompt = build_prompt(action_decision, form_data)
                logger.info(f"[run_automation] Built prompt: {prompt}")
                # Run the agent
                result = await self.browser_toolkit.agent_orchestrator.run_agent(prompt)
                logger.info(f"[run_automation] Agent result: {result}")
                # Update status_obj based on agent result
                status_obj.current_step_summary = current_step
                status_obj.awaiting_user_input = awaiting_user_input
                status_obj.requested_input_type = input_type
                status_obj.page_state = getattr(result, 'page_state', '') if hasattr(result, 'page_state') else ''
                status_obj.url = getattr(result, 'url', '') if hasattr(result, 'url') else ''
                status_obj.error_message = getattr(result, 'error', '') if hasattr(result, 'error') else ''
                status_obj.next_expected_action = getattr(result, 'next_action', '') if hasattr(result, 'next_action') else ''

                # --- CAPTCHA ERROR HANDLING ---
                error_text = ""
                if hasattr(result, 'extracted_content') and result.extracted_content:
                    error_text = result.extracted_content
                elif hasattr(result, 'error') and result.error:
                    error_text = result.error
                if isinstance(error_text, str) and "invalid captcha" in error_text.lower():
                    status_obj.error_message = "Invalid captcha, please try again."
                    status = "error"
                    logger.error("[run_automation] Captcha error detected, halting for retry.")
                    break
                # --- END CAPTCHA ERROR HANDLING ---

                # Determine if task is complete
                if hasattr(result, 'success') and result.success:
                    status_obj.task_complete = True
                    status = "completed"
                elif status_obj.awaiting_user_input:
                    status = "awaiting_user_input"
                elif status_obj.error_message:
                    status = "error"
                else:
                    status = "in_progress"
                # If task is complete or error, break loop
                if status_obj.task_complete or status == "error":
                    break
                # Otherwise, increment step
                status_obj.step_index += 1
                continue
            except Exception as e:
                consecutive_failures += 1
                logger.error(f"🚨 [run_automation] Unexpected error: {e}")
                status_obj.error_message = f"System error: {str(e)}"
                if consecutive_failures >= max_consecutive_failures:
                    logger.error("🚫 Too many consecutive system errors")
                    break
        response_data = {
            "status": status,
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
            "execution_time_seconds": (datetime.now() - start_time).total_seconds(),
            "agent_result": str(result) if result else None,
            "current_status": status_obj.__dict__
        }
        logger.info(f"[run_automation] FINAL RESPONSE: {response_data}")
        return response_data

    async def submit_user_input(self, input_type, input_value):
        return await self.browser_toolkit.submit_user_input(input_type, input_value)

    async def get_browser_status(self):
        state = await self.browser_toolkit.get_page_state()
        return {"page_state": state}

    async def reset_browser(self):
        await self.browser_toolkit.session_manager.reset_session()
        return {"success": True, "message": "Browser session reset successfully"} 