from selenium import webdriver
from selenium.common import exceptions as SExceptions

class WebComicDownloader:
    def __init__(self,
        browser: str = "firefox",
        ) -> None:
        if browser == "firefox":
            options = webdriver.FirefoxOptions()
            options.add_argument("-headless")
            self.driver = webdriver.Firefox(options)
        self.userAgent = self.driver.execute_script('return navigator.userAgent;')

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

    def getImageURL(self, elementSelector: tuple[str, str]) -> str | None:
        try:
            elem = self.driver.find_element(elementSelector[0], elementSelector[1])
        except SExceptions.NoSuchElementException:
            return None

        # Wordpress in particular seems to have this
        origfile = elem.get_attribute('data-orig-file')
        if origfile:
            return origfile

        # Get largest image URL from srcset
        srcset = elem.get_attribute('srcset')
        width = elem.get_attribute('width')
        if srcset and width:
            srcset_largest = srcset.split(',')[-1].strip().split(' ')
            if int(width) < int(srcset_largest[1].removesuffix('w')):
                return srcset_largest[0]

        # Fallback to src
        return elem.get_attribute("src")

    def getLink(self, elementSelector: tuple[str, str]) -> str | None:
        try:
            elem = self.driver.find_element(elementSelector[0], elementSelector[1])
        except SExceptions.NoSuchElementException:
            return None
        return elem.get_attribute('href')
