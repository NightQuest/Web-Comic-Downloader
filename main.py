from selenium.webdriver.common.by import By
from downloader import WebComicDownloader
from config import Config

if __name__ == "__main__":
    config = Config('config.json')
    startPage = "COMIC_1_URL_HERE"
    pageNum = 1
    delay = config.get('delay') or 0.25
    imageSelector = (By.ID, 'cc-comic')
    titleSelector = (By.CLASS_NAME, 'cc-newsheader')
    nextSelector = (By.CLASS_NAME, 'cc-next')

    downloader = WebComicDownloader(config, imageSelector, titleSelector, nextSelector)

    downloader.download(startPage, pageNum, delay)

    print("Complete")
