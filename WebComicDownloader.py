from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common import exceptions as SExceptions
from sanitize_filename import sanitize
import os
import requests
import mimetypes

class WebComicDownloader:
    def __init__(self,
        imageSelector: tuple[str, str],
        titleSelector: tuple[str, str] | None = None,
        nextSelector: tuple[str, str] | None = None,
        fallbackExension: str = ".png"
        ) -> None:
        self.imageSelector = imageSelector
        self.titleSelector = titleSelector
        self.nextSelector = nextSelector
        self.fallbackExension = fallbackExension
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

    def download(self, startURL: str, startIndex: int = 1, delay: float | None = None, folder: str = "images") -> None:
        currentPage = nextPage = startURL
        pageNum = startIndex

        while nextPage:
                self.load(nextPage)

                if delay:
                    self.wait(delay)

                currentPage = nextPage
                url = self.getImageURL(self.imageSelector)

                title = None
                if self.titleSelector:
                    title = sanitize(self.getTitle(self.titleSelector))

                if not url:
                    raise Exception("Failed to find comic image")

                response = requests.get(url, headers={
                    "User-Agent": self.userAgent,
                    "Referer": self.getDomain()
                    })
                response.raise_for_status()

                fileType = mimetypes.guess_extension(response.headers['content-type'])
                if not fileType:
                    fileType = self.fallbackExension

                if not os.path.exists(folder):
                    os.mkdir(folder)

                if not title:
                    filename = f"{pageNum:05d}{fileType}"
                else:
                    filename = f"{pageNum:05d} - {title}{fileType}"

                print(f"Saving: {filename}")

                with open(f"{folder}/{filename}", 'wb') as file:
                    file.write(response.content)

                if not self.nextSelector:
                    break

                nextPage = self.getLink(self.nextSelector)
                if not nextPage or nextPage == currentPage:
                    nextPage = None
                else:
                    pageNum = pageNum + 1
