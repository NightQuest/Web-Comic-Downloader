import os, urllib3
from typing import List, Literal
import requests
import mimetypes

from selenium.webdriver.common.by import By
from sanitize_filename import sanitize

from downloader import WebComicDownloader
from config import Config

class Application:
    def __init__(self, config: Config) -> None:
        self.config = config

    def resolveSelectorType(self, selector: list) -> tuple:
        if selector[0] == "id":
            selectorTuple = (By.ID, selector[1])
        elif selector[0] == "xpath":
            selectorTuple = (By.XPATH, selector[1])
        elif selector[0] == "link_text":
            selectorTuple = (By.LINK_TEXT, selector[1])
        elif selector[0] == "plink_text":
            selectorTuple = (By.PARTIAL_LINK_TEXT, selector[1])
        elif selector[0] == "name":
            selectorTuple = (By.NAME, selector[1])
        elif selector[0] == "tag_name":
            selectorTuple = (By.TAG_NAME, selector[1])
        elif selector[0] == "class_name":
            selectorTuple = (By.CLASS_NAME, selector[1])
        elif selector[0] == "css_selector":
            selectorTuple = (By.CSS_SELECTOR, selector[1])
        else: # Default to ID
            selectorTuple = (By.ID, selector[1])
        return selectorTuple

    def downloadComics(self) -> None:
        comics: list[dict] = self.config.get('comics')
        nextPage: str | None = None

        if not comics:
            print("No comics to download")
            exit()

        delay = self.config.get('delay') or 0.25
        fallbackExension = self.config.get('fallback_extension') or "png"

        for i in range(0, len(comics)):
            comicName = comics[i]['name']
            currentPage = nextPage = comics[i]['url']
            pageNum = comics[i]['page_num']
            enabled = comics[i]['enabled']

            if not enabled:
                print(f"Skipped: {comicName}")
                continue

            imageSelector = comics[i].get('image_selector')
            titleSelector = comics[i].get('title_selector')
            nextSelector = comics[i].get('next_selector')

            if imageSelector:
                imageSelector = self.resolveSelectorType(imageSelector)
            if titleSelector:
                titleSelector = self.resolveSelectorType(titleSelector)
            if nextSelector:
                nextSelector = self.resolveSelectorType(nextSelector)

            print(f"\nDownloading: {comicName}")

            if not imageSelector:
                print("Missing image selector")
                continue

            downloader = WebComicDownloader()

            while nextPage:
                complete = False
                url = None
                title = None

                while not complete and nextPage:
                    try:
                        downloader.load(nextPage)

                        if delay:
                            downloader.wait(delay)

                        currentPage = nextPage
                        url = downloader.getImageURL(imageSelector)

                        title = None
                        if titleSelector:
                            title = downloader.getTitle(titleSelector)
                            if title:
                                title = sanitize(title)

                        if nextSelector:
                            nextPage = downloader.getLink(nextSelector)

                        complete = True
                    except KeyboardInterrupt as e:
                        raise e
                    except:
                        downloader = WebComicDownloader()

                if not url:
                    break

                response = requests.get(url, headers={
                    "User-Agent": downloader.userAgent,
                    "Referer": downloader.getDomain()
                    })
                response.raise_for_status()

                fileType = mimetypes.guess_extension(response.headers['content-type'])
                if not fileType:
                    fileType = f".{fallbackExension}"

                if not os.path.exists(f"comics/{comicName}"):
                    os.mkdir(f"comics/{comicName}")

                if not title:
                    filename = f"{pageNum:05d}{fileType}"
                else:
                    filename = f"{pageNum:05d} - {title}{fileType}"

                print(f"Saving: {filename}")

                with open(f"comics/{comicName}/{filename}", 'wb') as file:
                    file.write(response.content)

                # Update config
                comics[i]['url'] = currentPage
                comics[i]['page_num'] = pageNum
                self.config.set('comics', comics)
                self.config._writeConfig()

                if nextPage:
                    nextPage = nextPage.strip().split('#')[0] # Get rid of #something-here

                if not nextPage or nextPage == currentPage:
                    nextPage = None
                else:
                    pageNum = pageNum + 1


if __name__ == "__main__":
    try:
        config = Config('config.json')

        if not os.path.exists('comics'):
            os.mkdir('comics')

        app = Application(config)
        app.downloadComics()
        print("\nComplete")
    except KeyboardInterrupt:
        print("\nAborted")
