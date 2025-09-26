import logging
import asyncio
from browser_use import BrowserSession
import traceback

logger = logging.getLogger(__name__)

class SessionManager:
    def __init__(self, session_url="http://localhost:9222"):
        self.session_url = session_url
        self.browser_session = None
        self.page = None

    async def initialize_browser_session(self):
        try:
            logger.info("🔄 Initializing browser session...")
            if self.browser_session:
                try:
                    await self.browser_session.close()
                except Exception as e:
                    logger.warning(f"Error closing existing session: {e}")
            self.browser_session = None
            self.page = None
            await asyncio.sleep(2)
            self.browser_session = BrowserSession(
                cdp_url=self.session_url,
                keep_alive=True
            )
            await self.browser_session.start()
            await asyncio.sleep(2)
            self.page = await self.browser_session.get_current_page()
            self.browser_session.page = self.page
            logger.info("✅ Browser session initialized successfully with page")
        except Exception as e:
            logger.error(f"❌ Failed to initialize browser session: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise Exception(f"Browser session initialization failed: {str(e)}")

    async def ensure_page_ready(self, max_retries=5):
        retry_count = 0
        while retry_count < max_retries:
            try:
                logger.info(f"🔄 Ensuring page ready (attempt {retry_count + 1}/{max_retries})...")
                if not self.browser_session:
                    logger.info("🔄 No browser session, creating new one...")
                    await self.initialize_browser_session()
                if not self.page or (hasattr(self.page, 'is_closed') and self.page.is_closed()):
                    logger.info("🔄 Page not available or closed, reinitializing...")
                    await self.initialize_browser_session()
                try:
                    await asyncio.wait_for(self.page.evaluate("document.readyState"), timeout=5)
                    url = self.page.url
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
                try:
                    if self.browser_session:
                        await self.browser_session.close()
                except Exception:
                    pass
                self.browser_session = None
                self.page = None
                await asyncio.sleep(min(5 * retry_count, 15))

    async def reset_session(self):
        try:
            logger.info("🔄 Performing complete browser session reset...")
            if self.browser_session:
                try:
                    await self.browser_session.close()
                except Exception as e:
                    logger.warning(f"Error closing browser session: {e}")
            self.browser_session = None
            self.page = None
            await asyncio.sleep(3)
            import gc
            gc.collect()
            logger.info("✅ Browser session reset completed")
        except Exception as e:
            logger.error(f"❌ Error during session reset: {e}")
            raise

    async def get_current_url(self):
        try:
            if self.page:
                return self.page.url
        except Exception as e:
            logger.warning(f"Could not get current URL: {e}")
        return "unknown" 