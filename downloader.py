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

    def _parseSrcset(self, srcset_value: Optional[str]) -> list[tuple[int, str]]:
        """Parse a srcset string into a list of (width, url) tuples sorted descending by width."""
        if not srcset_value:
            return []
        candidates: list[tuple[int, str]] = []
        for part in srcset_value.split(','):
            pieces = part.strip().split()
            if len(pieces) >= 2 and pieces[1].endswith('w'):
                url = pieces[0]
                try:
                    w_val = int(pieces[1][:-1])  # strip trailing 'w'
                except ValueError:
                    continue
                candidates.append((w_val, url))
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates

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
            elements = self.driver.find_elements(elementSelector[0], elementSelector[1])
        except SExceptions.NoSuchElementException:
            return None

        urls: list[str] = []

        for el in elements:
            # 1) Prefer WordPress-specific attributes
            for attr in ('data-orig-file', 'data-image'):
                val = el.get_attribute(attr)
                if val:
                    urls.append(val)
                    break
            else:
                # 2) Prefer src unless width suggests a larger srcset candidate
                src = el.get_attribute('src')
                srcset_value = el.get_attribute('srcset') or ''
                width_attr = el.get_attribute('width')

                candidates = self._parseSrcset(srcset_value)

                chosen_url: str | None = None
                if candidates and width_attr is not None:
                    largest_w, largest_url = candidates[0]
                    try:
                        renderedWidth = int(str(width_attr).strip())
                        if renderedWidth < largest_w:
                            chosen_url = largest_url
                    except ValueError:
                        pass

                if chosen_url:
                    urls.append(chosen_url)
                else:
                    # Prefer src if present; otherwise, fall back to largest srcset candidate if available
                    if src:
                        urls.append(src)
                    elif candidates:
                        urls.append(candidates[0][1])

        if not urls:
            return None

        # De-duplicate while preserving order
        seen: set[str] = set()
        deDuped: list[str] = []
        for u in urls:
            if u and u not in seen:
                seen.add(u)
                deDuped.append(u)

        return deDuped if deDuped else None

    def getLink(self, elementSelector: tuple[str, str]) -> Optional[str]:
        if not self.driver:
            return None
        try:
            elem = self.driver.find_element(elementSelector[0], elementSelector[1])
        except SExceptions.NoSuchElementException:
            return None
        return elem.get_attribute('href')
