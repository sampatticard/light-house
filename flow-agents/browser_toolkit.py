from browser_use import Agent, BrowserSession
from browser_use.llm import ChatOpenAI
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import traceback

logger = logging.getLogger(__name__)

class BrowserUseToolkit:
    def __init__(self):
        self.session_url = "http://localhost:9222"
        self.browser_session = None
        self.llm = ChatOpenAI(model="gpt-4o")
        self.agent = None
        self.last_action_time = None
        self.action_timeout = 60  # seconds
        self.page_load_timeout = 30  # seconds
        self.max_retries = 3
        self.page = None  # Track page separately

    async def _initialize_browser_session(self):
        """Initialize browser session with comprehensive error handling"""
        try:
            logger.info("🔄 Initializing browser session...")
            
            # Clean up existing session first
            if self.browser_session:
                try:
                    await self.browser_session.close()
                except Exception as e:
                    logger.warning(f"Error closing existing session: {e}")
                
            self.browser_session = None
            self.page = None
            
            # Wait for system to stabilize
            await asyncio.sleep(2)
            
            # Create new session
            self.browser_session = BrowserSession(
                cdp_url=self.session_url,
                keep_alive=True
            )
            
            # Start the session
            await self.browser_session.start()
            
            # Wait for session to fully initialize
            await asyncio.sleep(3)
            
            # Verify session has page attribute
            if hasattr(self.browser_session, 'page') and self.browser_session.page:
                self.page = self.browser_session.page
                logger.info("✅ Browser session initialized successfully with page")
            else:
                # Try to access page through context
                if hasattr(self.browser_session, 'context') and self.browser_session.context:
                    pages = self.browser_session.context.pages
                    if pages:
                        self.page = pages[0]
                        self.browser_session.page = self.page
                        logger.info("✅ Browser session initialized with page from context")
                    else:
                        # Create new page
                        self.page = await self.browser_session.context.new_page()
                        self.browser_session.page = self.page
                        logger.info("✅ Browser session initialized with new page")
                else:
                    raise Exception("Browser session created but no page or context available")
                    
        except Exception as e:
            logger.error(f"❌ Failed to initialize browser session: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise Exception(f"Browser session initialization failed: {str(e)}")

    async def _get_agent(self, task: str = None) -> Agent:
        """Get or create agent with enhanced error handling"""
        try:
            await self._initialize_browser_session()
            
            if self.agent is None or task:
                self.agent = Agent(
                    task=task or "Browser automation task",
                    llm=self.llm, 
                    browser_session=self.browser_session
                )
            return self.agent
        except Exception as e:
            logger.error(f"❌ Failed to get agent: {e}")
            raise

    async def ensure_page_ready(self):
        """Ensure browser page is ready with improved error handling"""
        max_retries = 5
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                logger.info(f"🔄 Ensuring page ready (attempt {retry_count + 1}/{max_retries})...")
                
                # Check if we have a browser session
                if not self.browser_session:
                    logger.info("🔄 No browser session, creating new one...")
                    await self._initialize_browser_session()
                
                # Check if page exists and is accessible
                if not self.page or (hasattr(self.page, 'is_closed') and self.page.is_closed()):
                    logger.info("🔄 Page not available or closed, reinitializing...")
                    await self._initialize_browser_session()
                
                # Test page accessibility with multiple checks
                try:
                    # Check if page is responsive
                    await asyncio.wait_for(self.page.evaluate("document.readyState"), timeout=5)
                    
                    # Check if page has content
                    url = await asyncio.wait_for(self.page.url, timeout=5)
                    
                    # Verify page is not blank
                    if url == "about:blank":
                        logger.warning("Page is blank, may need navigation")
                    
                    logger.info("✅ Page is ready and accessible")
                    return
                    
                except Exception as page_error:
                    logger.warning(f"Page accessibility test failed: {page_error}")
                    raise page_error
                    
            except Exception as e:
                retry_count += 1
                logger.error(f"🚨 Page ready check failed (attempt {retry_count}/{max_retries}): {e}")
                
                if retry_count >= max_retries:
                    logger.error("🚫 Failed to ensure page ready after all retries")
                    raise Exception(f"Page ready check failed after {max_retries} attempts: {str(e)}")
                
                # Reset everything and try again
                try:
                    if self.browser_session:
                        await self.browser_session.close()
                except Exception:
                    pass
                
                self.browser_session = None
                self.page = None
                self.agent = None
                
                # Progressive backoff
                wait_time = min(5 * retry_count, 15)
                logger.info(f"⏳ Waiting {wait_time} seconds before retry...")
                await asyncio.sleep(wait_time)

    async def get_page_state(self) -> str:
        """Get current page state with enhanced error handling"""
        try:
            await self.ensure_page_ready()
            
            if not self.page:
                return "CRITICAL_ERROR: No page available after initialization"
            
            # Use shorter timeouts for stability
            timeout = 8000  # 8 seconds
            
            # Get basic page info
            try:
                current_url = await asyncio.wait_for(self.page.url, timeout=5)
            except Exception as e:
                current_url = f"URL_ERROR: {str(e)}"
            
            try:
                page_title = await asyncio.wait_for(self.page.title(), timeout=5)
            except Exception as e:
                page_title = f"TITLE_ERROR: {str(e)}"
            
            # Get page content with comprehensive error handling
            try:
                page_content = await asyncio.wait_for(
                    self.page.evaluate('''
                        () => {
                            try {
                                // Check page state
                                const readyState = document.readyState;
                                if (readyState !== 'complete') {
                                    return `PAGE_LOADING: ${readyState}`;
                                }
                                
                                // Get body content
                                const body = document.body;
                                if (!body) return "NO_BODY_CONTENT";
                                
                                // Remove scripts and styles
                                const clonedBody = body.cloneNode(true);
                                const scripts = clonedBody.querySelectorAll('script, style, noscript');
                                scripts.forEach(el => el.remove());
                                
                                // Get visible text
                                const text = clonedBody.innerText || clonedBody.textContent || '';
                                
                                // Check for error indicators
                                const errorPatterns = [
                                    /error|failed|denied|blocked|unavailable/i,
                                    /maintenance|expired|invalid|locked/i,
                                    /service.*not.*available/i,
                                    /account.*locked/i,
                                    /session.*expired/i
                                ];
                                
                                const hasError = errorPatterns.some(pattern => pattern.test(text));
                                
                                if (hasError) {
                                    return `ERROR_DETECTED: ${text.substring(0, 500)}`;
                                }
                                
                                return text.substring(0, 1200); // Limit text length
                                
                            } catch (e) {
                                return `EVALUATION_ERROR: ${e.message}`;
                            }
                        }
                    '''),
                    timeout=8
                )
            except Exception as e:
                page_content = f"PAGE_CONTENT_ERROR: {str(e)}"
            
            # Get form information
            try:
                form_info = await asyncio.wait_for(
                    self.page.evaluate('''
                        () => {
                            try {
                                const forms = document.querySelectorAll('form');
                                const inputs = document.querySelectorAll('input, select, textarea');
                                const buttons = document.querySelectorAll('button, input[type="submit"], input[type="button"]');
                                
                                // Analyze input fields
                                const inputDetails = Array.from(inputs).slice(0, 10).map(inp => {
                                    return {
                                        type: inp.type || inp.tagName.toLowerCase(),
                                        placeholder: inp.placeholder || '',
                                        name: inp.name || '',
                                        id: inp.id || '',
                                        visible: inp.offsetParent !== null
                                    };
                                });
                                
                                // Check for specific field types
                                const hasOtpField = inputDetails.some(inp => 
                                    /otp/i.test(inp.placeholder + inp.name + inp.id)
                                );
                                
                                const hasCaptcha = document.querySelector('img[src*="captcha"], [id*="captcha"], [class*="captcha"]') !== null;
                                
                                const hasMobileField = inputDetails.some(inp => 
                                    /mobile|phone/i.test(inp.placeholder + inp.name + inp.id) ||
                                    inp.type === 'tel'
                                );
                                
                                return {
                                    forms_count: forms.length,
                                    inputs_count: inputs.length,
                                    buttons_count: buttons.length,
                                    input_details: inputDetails,
                                    has_otp_field: hasOtpField,
                                    has_captcha: hasCaptcha,
                                    has_mobile_field: hasMobileField
                                };
                            } catch (e) {
                                return {
                                    error: `FORM_ANALYSIS_ERROR: ${e.message}`,
                                    forms_count: 0,
                                    inputs_count: 0,
                                    buttons_count: 0,
                                    input_details: [],
                                    has_otp_field: false,
                                    has_captcha: false,
                                    has_mobile_field: false
                                };
                            }
                        }
                    '''),
                    timeout=8
                )
            except Exception as e:
                form_info = {"error": f"FORM_INFO_ERROR: {str(e)}"}
            
            # Build comprehensive state description
            state_description = f"""URL: {current_url}
Title: {page_title}
Page Status: {'READY' if not any(err in page_content for err in ['ERROR', 'LOADING']) else 'ERROR_OR_LOADING'}
Forms: {form_info.get('forms_count', 0)} | Inputs: {form_info.get('inputs_count', 0)} | Buttons: {form_info.get('buttons_count', 0)}
Fields Found: Mobile={form_info.get('has_mobile_field', False)}, OTP={form_info.get('has_otp_field', False)}, Captcha={form_info.get('has_captcha', False)}
Content: {page_content[:400]}..."""
            
            return state_description
            
        except Exception as e:
            logger.error(f"❌ Critical error getting page state: {e}")
            return f"CRITICAL_ERROR: Failed to get page state - {str(e)}"

    async def execute_action(self, action_decision, form_data) -> Dict[str, Any]:
        """Execute browser action with comprehensive error handling"""
        start_time = datetime.now()
        
        try:
            # Validation checks
            if not action_decision or not hasattr(action_decision, 'step_index'):
                return self._create_error_response("Invalid action decision provided")
            
            # Handle OTP requirements
            if action_decision.step_index in [2, 8] and not form_data.get('aadhar_otp'):
                logger.info("⏸️ OTP required but not provided")
                return {
                    "success": False,
                    "awaiting_user_input": True,
                    "requested_input_type": "otp",
                    "error": "OTP is required but not provided",
                    "page_state": await self.get_page_state(),
                    "url": await self._get_current_url()
                }
            
            # Ensure browser readiness
            await self.ensure_page_ready()
            
            # Build and execute action
            action_prompt = self._build_action_prompt(action_decision, form_data)
            logger.info(f"🎬 Executing step {action_decision.step_index}: {action_decision.current_step_summary}")
            
            # Execute with timeout and retry logic
            max_execution_retries = 2
            execution_timeout = 120  # 2 minutes
            
            for attempt in range(max_execution_retries):
                try:
                    agent = await self._get_agent(action_prompt)
                    
                    result = await asyncio.wait_for(
                        agent.run(),
                        timeout=execution_timeout
                    )
                    
                    # Get updated state
                    new_page_state = await self.get_page_state()
                    current_url = await self._get_current_url()
                    
                    # Validate result
                    if self._is_execution_successful(result, new_page_state, action_decision):
                        logger.info(f"✅ Step {action_decision.step_index} completed successfully")
                        return {
                            "success": True,
                            "result": result,
                            "page_state": new_page_state,
                            "url": current_url,
                            "execution_time": (datetime.now() - start_time).total_seconds()
                        }
                    else:
                        logger.warning(f"⚠️ Step {action_decision.step_index} validation failed (attempt {attempt + 1})")
                        if attempt < max_execution_retries - 1:
                            await asyncio.sleep(5)  # Wait before retry
                            continue
                        else:
                            return {
                                "success": False,
                                "error": "Action completed but validation failed after all retries",
                                "result": result,
                                "page_state": new_page_state,
                                "url": current_url
                            }
                            
                except asyncio.TimeoutError:
                    logger.error(f"⏰ Action execution timeout (attempt {attempt + 1})")
                    if attempt < max_execution_retries - 1:
                        await asyncio.sleep(10)  # Wait before retry
                        continue
                    else:
                        return self._create_error_response(f"Action execution timeout after {execution_timeout} seconds")
                        
        except Exception as e:
            logger.error(f"🚫 Critical action execution error: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return self._create_error_response(f"Critical execution error: {str(e)}")

    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            "success": False,
            "error": error_message,
            "page_state": "ERROR_STATE",
            "url": "unknown"
        }

    async def _get_current_url(self) -> str:
        """Get current URL with error handling"""
        try:
            if self.page:
                return await asyncio.wait_for(self.page.url, timeout=5)
        except Exception as e:
            logger.warning(f"Could not get current URL: {e}")
        return "unknown"

    def _is_execution_successful(self, result, page_state: str, action_decision) -> bool:
        """Enhanced validation of execution success"""
        try:
            # Check for error indicators
            error_indicators = [
                "ERROR_DETECTED",
                "CRITICAL_ERROR", 
                "PAGE_CONTENT_ERROR",
                "EVALUATION_ERROR",
                "TIMEOUT",
                "FAILED"
            ]
            
            if any(indicator in page_state for indicator in error_indicators):
                logger.warning(f"Error indicator found in page state: {page_state[:200]}")
                return False
            
            # Check result for errors
            if isinstance(result, str):
                result_lower = result.lower()
                if any(word in result_lower for word in ["error", "failed", "timeout", "denied"]):
                    logger.warning(f"Error indicator found in result: {result[:200]}")
                    return False
            
            # Step-specific validations
            step_validations = {
                0: lambda: any(indicator in page_state.lower() for indicator in ["beneficiary", "mobile", "phone", "login"]),
                1: lambda: any(indicator in page_state.lower() for indicator in ["otp", "verify", "code"]),
                2: lambda: any(indicator in page_state.lower() for indicator in ["enroll", "registration", "dashboard"]),
                3: lambda: any(indicator in page_state.lower() for indicator in ["aadhaar", "family", "search"]),
                4: lambda: any(indicator in page_state.lower() for indicator in ["ekyc", "verification", "method"]),
                # Add more as needed
            }
            
            step_validator = step_validations.get(action_decision.step_index)
            if step_validator:
                validation_result = step_validator()
                logger.info(f"Step {action_decision.step_index} validation result: {validation_result}")
                return validation_result
            
            # Default validation - no errors detected
            return True
            
        except Exception as e:
            logger.error(f"Error in validation: {e}")
            return False

    def _build_action_prompt(self, action_decision, form_data) -> str:
        """Build enhanced action prompt with better error handling"""
        step_actions = {
            0: "Navigate to https://beneficiary.nha.gov.in/ and verify successful page load. Look for mobile number input or login form.",
            1: f"Fill mobile number: {form_data.get('phone', '')}. Solve captcha if present. Click submit/verify button.",
            2: f"Enter OTP: {form_data.get('aadhar_otp', '')} in OTP field. Click login/verify button.",
            3: "Find and click enrollment/registration option appropriate for age and eligibility.",
            4: f"Enter Aadhaar number: {form_data.get('aadhaar_number', '')}. Fill Family ID: {form_data.get('family_id', '')} if field exists. Click search.",
            5: "Select 'Aadhaar OTP' eKYC method if available.",
            6: "Click 'Verify' or 'Start eKYC' button to begin verification.",
            7: "Accept consent form by checking 'I Agree' and clicking 'Allow' or 'Proceed'.",
            8: f"Enter Aadhaar OTP: {form_data.get('aadhar_otp', '')} for eKYC verification.",
            9: "Review displayed Aadhaar details and click 'Confirm' if correct.",
            10: "Enable camera access and capture photo. Click 'Proceed' after photo taken.",
            11: f"Fill final form with: Phone={form_data.get('phone', '')}, DOB={form_data.get('dob', '')}, etc. Submit form.",
            12: "Complete any additional KYC requirements as prompted.",
            13: "Click 'Download' button to download Ayushman Bharat card PDF."
        }
        
        base_action = step_actions.get(action_decision.step_index, "Execute current step with error handling.")
        
        return f"""
AYUSHMAN BHARAT AUTOMATION - STEP {action_decision.step_index}

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

    async def reset_session(self):
        """Complete browser session reset"""
        try:
            logger.info("🔄 Performing complete browser session reset...")
            
            # Close everything cleanly
            if self.browser_session:
                try:
                    await self.browser_session.close()
                except Exception as e:
                    logger.warning(f"Error closing browser session: {e}")
            
            # Reset all variables
            self.browser_session = None
            self.page = None
            self.agent = None
            self.last_action_time = None
            
            # Wait for cleanup
            await asyncio.sleep(3)
            
            # Force garbage collection
            import gc
            gc.collect()
            
            logger.info("✅ Browser session reset completed")
            
        except Exception as e:
            logger.error(f"❌ Error during session reset: {e}")
            raise

    async def submit_user_input(self, input_type: str, input_value: str) -> Dict[str, Any]:
        """Handle user input with improved error handling"""
        try:
            if not input_type or not input_value:
                return {"success": False, "error": "Input type and value are required"}
            
            await self.ensure_page_ready()
            
            # Build input-specific prompt
            input_prompts = {
                "otp": f"Find OTP input field and enter: {input_value}. Click submit/verify button.",
                "captcha": f"Find captcha input field and enter: {input_value}. Click submit button.",
                "mobile": f"Find mobile number field and enter: {input_value}. Click submit button."
            }
            
            prompt = input_prompts.get(input_type, f"Enter {input_type}: {input_value} in appropriate field.")
            
            enhanced_prompt = f"""
USER INPUT SUBMISSION - {input_type.upper()}

TASK: {prompt}

STEPS:
1. Locate the {input_type} input field (check for labels, placeholders, IDs)
2. Clear existing content if any
3. Enter value: {input_value}
4. Click submit/verify button
5. Wait for response (max 30 seconds)
6. Report success or specific error message

ERROR HANDLING:
- Field not found: Report "Field not found: {input_type}"
- Invalid input: Report "Invalid input: [error message]"
- Submission failed: Report "Submission failed: [reason]"
- Network error: Report "Network error: [details]"

Confirm successful submission by checking for success message or page change.
"""
            
            agent = await self._get_agent(enhanced_prompt)
            result = await asyncio.wait_for(agent.run(), timeout=90)
            
            new_state = await self.get_page_state()
            
            # Check for success indicators
            success_indicators = ["success", "verified", "accepted", "confirmed"]
            error_indicators = ["error", "invalid", "failed", "denied"]
            
            result_lower = str(result).lower()
            state_lower = new_state.lower()
            
            if any(indicator in result_lower or indicator in state_lower for indicator in error_indicators):
                return {
                    "success": False,
                    "error": f"Input submission failed: {result}",
                    "page_state": new_state
                }
            
            return {
                "success": True,
                "result": result,
                "page_state": new_state,
                "url": await self._get_current_url()
            }
            
        except Exception as e:
            logger.error(f"❌ Error submitting user input: {e}")
            return {"success": False, "error": str(e)}

    async def execute_browser_task(self, task: str, form_data: dict = None):
        """Execute browser task with enhanced error handling"""
        try:
            await self.ensure_page_ready()
            logger.info(f"📤 Executing browser task: {task[:100]}...")
            
            enhanced_task = f"""
{task}

ENHANCED ERROR HANDLING:
- Maximum execution time: 5 minutes
- Report specific errors when they occur
- Take screenshots for debugging
- Provide detailed error messages
- Don't continue if critical errors occur

TIMEOUT HANDLING:
- Element wait timeout: 15 seconds
- Page load timeout: 30 seconds
- Overall task timeout: 5 minutes
- Report timeout errors with context

SUCCESS CRITERIA:
- Task completed without errors
- Expected elements found and interacted with
- Page responses as expected
- No error messages displayed
"""
            
            agent = await self._get_agent(enhanced_task)
            result = await asyncio.wait_for(agent.run(), timeout=300)
            
            logger.info("✅ Browser task completed successfully")
            return {
                "success": True,
                "result": result,
                "page_state": await self.get_page_state(),
                "url": await self._get_current_url()
            }
            
        except asyncio.TimeoutError:
            logger.error("⏰ Browser task timeout")
            return {"success": False, "error": "Task execution timeout after 5 minutes"}
        except Exception as e:
            logger.error(f"❌ Browser task error: {e}")
            return {"success": False, "error": str(e)}

    def __del__(self):
        """Cleanup on destruction"""
        try:
            if self.browser_session:
                # Note: Can't use async in __del__, this is just a fallback
                pass
        except Exception:
            pass