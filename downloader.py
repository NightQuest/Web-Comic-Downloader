from selenium import webdriver
from selenium.common import exceptions as SExceptions
from selenium.webdriver.common.by import By
import atexit
from typing import Optional

class WebComicDownloader:
    def __init__(self,
        browser: str = "firefox",
        ) -> None:
        self.driver: Optional[webdriver.Remote] = None
        self.userAgent: Optional[str] = None
        self._closed: bool = False

        try:
            if browser.lower() == "firefox":
                options = webdriver.FirefoxOptions()
                options.add_argument("-headless")
                # Disable caches in Firefox profile (migrated to options preferences)
                options.set_preference("browser.cache.disk.enable", False)
                options.set_preference("browser.cache.memory.enable", False)
                options.set_preference("browser.cache.offline.enable", False)
                options.set_preference("network.http.use-cache", False)
                self.driver = webdriver.Firefox(options=options)

            # Register an atexit hook to ensure cleanup even if __del__ is skipped
            atexit.register(self.close)

            # Only attempt to query userAgent if driver exists
            if self.driver:
                self.userAgent = self.driver.execute_script('return navigator.userAgent;')
        except Exception:
            # If initialization fails midway, ensure we don't leak a partially created driver
            self.close()
            raise

    def __enter__(self) -> 'WebComicDownloader':
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        self.close()
        # Do not suppress exceptions
        return False

    def close(self) -> None:
        """Idempotent cleanup of the webdriver resources."""
        if self._closed:
            return
        self._closed = True
        if self.driver is not None:
            try:
                # Attempt to close the current window if still open
                self.driver.close()
                self.driver.quit()
            except Exception:
                pass
            finally:
                self.driver = None

    def __del__(self) -> None:
        # Be defensive in finalizer; never raise
        try:
            self.close()
        except Exception:
            pass

    def load(self, page: str) -> None:
        if not self.driver:
            raise RuntimeError("WebComicDownloader is closed or not initialized.")

        # Navigate to about:blank first to encourage release of prior page resources
        try:
            self.driver.get("about:blank")
        except Exception:
            # Ignore failures to navigate to about:blank and proceed
            pass

        # Now navigate to the requested page
        self.driver.get(page)
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    def wait(self, time: float) -> None:
        if not self.driver:
            raise RuntimeError("WebComicDownloader is closed or not initialized.")
        self.driver.implicitly_wait(time)

    def getDomain(self) -> str:
        if not self.driver:
            raise RuntimeError("WebComicDownloader is closed or not initialized.")
        return self.driver.execute_script('return window.location.origin;')

    def getTitle(self, elementSelector: tuple[str, str]) -> Optional[str]:
        if not self.driver:
            return None
        by, selector = elementSelector

        # Support XPath expressions that request an attribute directly via '/@attr'
        # Example: (By.XPATH, "//img[@id='cc-comic']/@alt")
        attr_to_read: Optional[str] = None
        if by == By.XPATH and '/@' in selector:
            try:
                xpath_part, attr_part = selector.rsplit('/@', 1)
                attr_to_read = attr_part.strip()
                # Find the element using the XPath without the attribute part
                element = self.driver.find_element(By.XPATH, xpath_part)
                value = element.get_attribute(attr_to_read)
                if value is None:
                    return None
                value = value.strip()
                return value if value else None
            except (SExceptions.NoSuchElementException, SExceptions.StaleElementReferenceException):
                return None
            except Exception:
                # Fall back to standard behavior below if parsing fails
                pass

        # Standard element text retrieval path
        try:
            element = self.driver.find_element(by, selector)
        except (SExceptions.NoSuchElementException, SExceptions.StaleElementReferenceException):
            return None

        text = element.text.strip() if element.text else ''
        return text if text else None

    def getImageURLs(self, elementSelector: tuple[str, str]) -> Optional[list[str]]:
        if not self.driver:
            return None
        try:
            elems = self.driver.find_elements(elementSelector[0], elementSelector[1])
        except SExceptions.NoSuchElementException:
            return None

        ret = []

        for elem in elems:
            # Wordpress in particular seems to have this
            origfile = elem.get_attribute('data-orig-file')
            if origfile:
                ret.append(origfile)
                continue

            # Some Wordpress seems to have this instead of data-orig-file
            imgfile = elem.get_attribute('data-image')
            if imgfile:
                ret.append(imgfile)
                continue

            # Get largest image URL from srcset
            srcset = elem.get_attribute('srcset')
            width = elem.get_attribute('width')
            if srcset and width:
                srcset_largest = srcset.split(',')[-1].strip().split(' ')
                if int(width) < int(srcset_largest[1].removesuffix('w')):
                    ret.append(srcset_largest[0])
                    continue

            # Fallback to src
            ret.append(elem.get_attribute("src"))

        if len(ret) >= 1:
            return ret

        return None

    def getLink(self, elementSelector: tuple[str, str]) -> Optional[str]:
        if not self.driver:
            return None
        try:
            elem = self.driver.find_element(elementSelector[0], elementSelector[1])
        except SExceptions.NoSuchElementException:
            return None
        return elem.get_attribute('href')
