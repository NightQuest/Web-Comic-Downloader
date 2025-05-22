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

    def wait(self, time: float) -> None:
        self.driver.implicitly_wait(time)

    def getDomain(self) -> str:
        return self.driver.execute_script('return window.location.origin;')

    def getTitle(self, elementSelector: tuple[str, str]) -> str:
        try:
            title = self.driver.find_element(elementSelector[0], elementSelector[1])
        except (SExceptions.NoSuchElementException, SExceptions.StaleElementReferenceException):
            return ""
        return title.text

    def getImageURL(self, elementSelector: tuple[str, str]) -> str | None:
        try:
            elem = self.driver.find_element(elementSelector[0], elementSelector[1])
        except SExceptions.NoSuchElementException:
            return None
        return elem.get_attribute('src')

    def getLink(self, elementSelector: tuple[str, str]) -> str | None:
        try:
            elem = self.driver.find_element(elementSelector[0], elementSelector[1])
        except SExceptions.NoSuchElementException:
            return None
        return elem.get_attribute('href')
