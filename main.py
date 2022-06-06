import base64
import os
from io import BytesIO

import scrapy
from scrapy.crawler import CrawlerProcess
from PIL import Image
import requests


class CreatingFiles:
    numer_image = 0

    def __init__(self, directory_name):
        self.directory_name = directory_name
        if not os.path.exists(directory_name):
            os.mkdir(directory_name)

    def __generation_name_file(self, img_format: str) -> str:
        self.numer_image += 1
        return f'./{self.directory_name}/{self.numer_image}.{img_format.lower()}'

    def save_img(self, img_data):
        img_save = Image.open(img_data)
        try:
            img_save.save(self.__generation_name_file(img_save.format))
        except OSError:
            print("Ошибка сохранения")

    def save_img_link(self, url):
        res = requests.get(url, stream=True)
        if res.status_code == 200:
            self.save_img(res.raw)

    def save_img_base64(self, img_src):
        base64_string = img_src.split('base64,')[1].encode('utf8')
        img_data = BytesIO(base64.decodebytes(base64_string))
        self.save_img(img_data)


class GoogleSpider(scrapy.Spider):
    name = "google_img"
    quantity_images = 15
    numer_image = 0
    custom_settings = {
        'ROBOTSTXT_OBEY': False,
        'DOWNLOAD_HANDLERS': {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        'TWISTED_REACTOR': "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Language': 'ru',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36'
        }
    }

    def start_requests(self):
        yield scrapy.Request(f"https://www.google.com/search?q={search_query}",
                             meta={"playwright": True})

    def parse(self, response):
        cf = CreatingFiles(directory_name=search_query)
        serp = response.css('div#rcnt')
        if len(serp) == 0:
            serp = response
        for img in serp.css('img')[:self.quantity_images]:
            img_data_src = img.css('::attr(data-src)').get('')
            img_src = img.css('::attr(src)').get('')
            if img_data_src != '':
                cf.save_img_link(img_data_src)
            elif img_src != '':
                if img_src.find('data:image') > -1:
                    cf.save_img_base64(img_src)
                else:
                    cf.save_img_link(img_src)


if __name__ == "__main__":
    search_query = input('Введите поисковый запрос (запрос по умолчанию "котики"): \n')
    if search_query == "":
        search_query = "котики"
    process = CrawlerProcess()
    process.crawl(GoogleSpider, search_query=search_query)
    process.start()
