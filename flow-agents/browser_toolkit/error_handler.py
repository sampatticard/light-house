import logging

logger = logging.getLogger(__name__)

class ErrorHandler:
    def __init__(self):
        self.error_indicators = [
            "ERROR_DETECTED", "CRITICAL_ERROR", "PAGE_CONTENT_ERROR",
            "EVALUATION_ERROR", "TIMEOUT", "FAILED"
        ]

    def create_error_response(self, error_message: str) -> dict:
        return {
            "success": False,
            "error": error_message,
            "page_state": "ERROR_STATE",
            "url": "unknown"
        }

    def is_execution_successful(self, result, page_state: str, action_decision) -> bool:
        try:
            if any(indicator in page_state for indicator in self.error_indicators):
                logger.warning(f"Error indicator found in page state: {page_state[:200]}")
                return False
            if isinstance(result, str):
                result_lower = result.lower()
                if any(word in result_lower for word in ["error", "failed", "timeout", "denied"]):
                    logger.warning(f"Error indicator found in result: {result[:200]}")
                    return False
            return True
        except Exception as e:
            logger.error(f"Error in validation: {e}")
            return False 