from selenium import webdriver
from selenium.common import exceptions as SExceptions
from typing import Optional

class WebComicDownloader:
    def __init__(self,
        browser: str = "firefox",
        ) -> None:
        self.driver: Optional[webdriver.Remote] = None
        self.userAgent: Optional[str] = None

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

            # Only attempt to query userAgent if driver exists
            if self.driver:
                self.userAgent = self.driver.execute_script('return navigator.userAgent;')
        except Exception:
            # If initialization fails midway, ensure we don't leak a partially created driver
            self.close()
            raise
    def __del__(self) -> None:
        self.driver.quit()

    def load(self, page: str):
        self.driver.get(page)
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    def wait(self, time: float) -> None:
        self.driver.implicitly_wait(time)

    def getDomain(self) -> str:
        return self.driver.execute_script('return window.location.origin;')

    def getTitle(self, elementSelector: tuple[str, str]) -> str | None:
        try:
            title = self.driver.find_element(elementSelector[0], elementSelector[1])
        except (SExceptions.NoSuchElementException, SExceptions.StaleElementReferenceException):
            return None

        if len(title.text.strip()) == 0:
            return None
        return title.text.strip()

    def getImageURLs(self, elementSelector: tuple[str, str]) -> list[str] | None:
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

    def getLink(self, elementSelector: tuple[str, str]) -> str | None:
        try:
            elem = self.driver.find_element(elementSelector[0], elementSelector[1])
        except SExceptions.NoSuchElementException:
            return None
        return elem.get_attribute('href')
