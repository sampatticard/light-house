"""
Browser toolkit package for modular browser automation.
Includes session management, agent orchestration, prompt building, and error handling.
"""

from .session_manager import SessionManager
from .agent_orchestrator import AgentOrchestrator
from .prompt_builder import PromptBuilder
from .error_handler import ErrorHandler

class BrowserUseToolkit:
    def __init__(self):
        self.session_manager = SessionManager()
        self.agent_orchestrator = AgentOrchestrator(self.session_manager)
        self.prompt_builder = PromptBuilder()
        self.error_handler = ErrorHandler()

    async def execute_action(self, action_decision, form_data):
        prompt = self.prompt_builder.build_ayushman_prompt(action_decision, form_data)
        result = await self.agent_orchestrator.run_agent(prompt)
        return {"result": result} 