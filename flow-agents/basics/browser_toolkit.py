from browser_use import Agent, BrowserSession
from browser_use.llm import ChatOpenAI
import logging

logger = logging.getLogger(__name__)

class BrowserUseToolkit:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o")
        self.browser_session = BrowserSession(
            cdp_url="http://localhost:9222",  
            keep_alive=True,
        )
        self.browser_started = False

    async def _start_browser_if_needed(self):
        if not self.browser_started:
            await self.browser_session.start()
            self.browser_started = True

    async def close_browser(self):
        if self.browser_started:
            await self.browser_session.close()
            self.browser_started = False

    async def execute_browser_task(self, prompt: str):
        try:
            await self._start_browser_if_needed()
            agent = Agent(
                task=prompt,
                llm=self.llm,
                browser_session=self.browser_session,
            )
            page = await agent.browser_session.get_current_page()
            print(f"page content: {page}")
            result = await agent.run()
            return str(result)
        except Exception as e:
            return f"❌ Browser task failed: {e}"