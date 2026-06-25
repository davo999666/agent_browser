import playwright.sync_api
from playwright._impl._errors import TargetClosedError
from typing import Optional
import logging
import random

logger = logging.getLogger(__name__)


class BrowserLifecycle:
    """Manages browser lifecycle (launch, context, page, close).
    
    Responsibilities:
    - Launch browser with proper configuration
    - Create browser context with stealth settings
    - Navigate to initial URL
    - Close browser and clean up resources
    """
    def __init__(self, url: str, headless: bool = True):
        self.url = url
        self.headless = headless
        self._playwright = None
        self._browser: Optional[playwright.sync_api.Browser] = None
        self._context: Optional[playwright.sync_api.BrowserContext] = None
        self._page: Optional[playwright.sync_api.Page] = None
        self._last_url: str = ""
    
    # ------------------------------------------------------------------
    # Browser lifecycle
    # ------------------------------------------------------------------
    
    def start(self) -> None:
        """Launch browser and open the target page."""
        self._playwright = playwright.sync_api.sync_playwright().start()
        self._browser = self._playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--window-size=1920,1080",
            ]
        )
        self._context = self._browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1080, "height": 800},
            locale="en-US",
            timezone_id="America/New_York",
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Cache-Control": "max-age=0",
            }
        )
        self._page = self._context.new_page()
        
        # Minimal stealth scripts
        self._page.add_init_script("""
            // Only override webdriver property
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            
            // Add minimal chrome runtime
            if (!window.chrome) {
                window.chrome = { runtime: {} };
            }
        """)
        
        # Human-like delay before navigation
        delay = random.uniform(1.0, 3.0)
        logger.info(f"Waiting {delay:.1f}s before navigation (human-like delay)")
        self._page.wait_for_timeout(int(delay * 1000))
        
        logger.info(f"Navigating to {self.url}")
        self._page.goto(self.url, wait_until="domcontentloaded", timeout=30000)
        self._last_url = self._page.url
    
    def stop(self) -> None:
        """Close browser and clean up resources."""
        if self._browser:
            try:
                self._browser.close()
            except Exception:
                pass
        if self._playwright:
            try:
                self._playwright.stop()
            except Exception:
                pass
    
    # ------------------------------------------------------------------
    # Page access
    # ------------------------------------------------------------------
    
    def get_page(self) -> Optional[playwright.sync_api.Page]:
        """Get the current page."""
        return self._page
    
    def get_last_url(self) -> str:
        """Get the last recorded URL."""
        return self._last_url
    
    def is_page_alive(self) -> bool:
        """Check if the page is still open and usable."""
        if self._page is None:
            return False
        try:
            self._page.url
            return True
        except (TargetClosedError, Exception):
            return False
    

