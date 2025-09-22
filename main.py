import os
import requests
import mimetypes
import base64

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
        download_by = self.config.get('download_by')
        overwrite_existing: bool = self.config.get('overwrite_existing') == True
        update_config: bool = self.config.get('update_config') == True

        if download_by == "name_desc":
            comics = sorted(comics, key=lambda comic: comic['name'])
        elif download_by == "name_asc":
            comics = sorted(comics, key=lambda comic: comic['name'], reverse=True)

        for i in range(0, len(comics)):
            comicName = comics[i]['name']
            currentPage = nextPage = comics[i]['url']
            pageNum = comics[i]['page_num']
            enabled = comics[i]['enabled']

            if not enabled:
                print(f"\nSkipped: {comicName}")
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

            pageCount = 0;
            while nextPage:
                complete = False
                url = None
                title = None
                pageCount = pageCount + 1

                # Selenium seems to have a memory leak
                # restart every 100 pages
                if pageCount == 100:
                    pageCount = 0
                    downloader = WebComicDownloader()

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

                schema = url.split(':')[0]
                contentType = None
                content = None

                if schema == "data": # data:image/jpeg;base64,/9j/4TbYRXhpZgAATU0AKgAAAAgADQEA
                    data = url[5:].split(';')

                    contentType = data[0]
                    data = data[1].split(',')

                    if data[0] == "base64":
                        content = base64.b64decode(data[1])

                elif schema == "http" or schema == "https":
                    response = requests.get(url, headers={
                        "User-Agent": downloader.userAgent,
                        "Referer": downloader.getDomain()
                        })
                    response.raise_for_status()
                    contentType = response.headers['content-type']
                    content = response.content

                if not contentType or not content:
                    break

                fileType = mimetypes.guess_extension(contentType)
                if not fileType:
                    fileType = f".{fallbackExension}"

                if not os.path.exists(f"comics/{comicName}"):
                    os.mkdir(f"comics/{comicName}")

                if not title:
                    filename = f"{pageNum:05d}{fileType}"
                else:
                    filename = f"{pageNum:05d} - {title}{fileType}"

                exists = os.path.exists(f"comics/{comicName}/{filename}")

                if not overwrite_existing and exists:
                    print(f"Skipped: {filename}")
                else:
                    if exists:
                        print(f"Overwriting: {filename}")
                    else:
                        print(f"Saving: {filename}")

                    with open(f"comics/{comicName}/{filename}", 'wb') as file:
                        file.write(content)

                # Update config
                if update_config:
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
