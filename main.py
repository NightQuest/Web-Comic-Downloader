from selenium.webdriver.common.by import By
from WebComicDownloader import WebComicDownloader

if __name__ == "__main__":
    # Config
    startPage = "COMIC_1_URL_HERE"
    pageNum = 1
    delay = 0.25
    imageSelector = (By.ID, 'cc-comic')
    titleSelector = (By.CLASS_NAME, 'cc-newsheader')
    nextSelector = (By.CLASS_NAME, 'cc-next')

    downloader = WebComicDownloader(imageSelector, titleSelector, nextSelector)

    downloader.download(startPage, pageNum, delay)

    print("Complete")
