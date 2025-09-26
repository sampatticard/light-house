import logging
from browser_use import Agent
from browser_use.llm import ChatOpenAI

logger = logging.getLogger(__name__)

class AgentOrchestrator:
    def __init__(self, session_manager, model="gpt-4o"):
        self.session_manager = session_manager
        self.llm = ChatOpenAI(model=model)
        self.agent = None

    async def get_agent(self, task=None):
        await self.session_manager.initialize_browser_session()
        if self.agent is None or task:
            self.agent = Agent(
                task=task or "Browser automation task",
                llm=self.llm,
                browser_session=self.session_manager.browser_session
            )
        return self.agent

    async def run_agent(self, prompt):
        agent = await self.get_agent(prompt)
        result = await agent.run()
        return result 