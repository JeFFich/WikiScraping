import scrapy
import requests
import re
from bs4 import BeautifulSoup


class FilmsSpider(scrapy.Spider):
    name = "films"
    allowed_domains = ["ru.wikipedia.org"]
    start_urls = ["https://ru.wikipedia.org/wiki/Категория:Фильмы_по_алфавиту"]

    def start_requests(self):
        URL = "https://ru.wikipedia.org/wiki/Категория:Фильмы_по_алфавиту"
        yield scrapy.Request(url=URL, callback=self.response_parser)

    @staticmethod
    def get_film_data(url):
        """Скрапинг страницы фильма при помощи BeautifulSoup"""
        soup = BeautifulSoup(requests.get(url).text)

        # Вся требуемая информация хранится в infobox, название фильма можно извлечь сразу из заголовка
        fim_info_dict = {
            "Название": soup.find("th", class_="infobox-above").getText().strip(),
            "Режиссёр": "-",
            "Жанр": "-",
            "Страна": "-",
            "Год": "-"
        }

        # Обработка исключения
        if fim_info_dict["Название"] == "Оглавление:…в начало":
            return None

        table = soup.find("table", class_="infobox")

        # В infobox информация хранится по строкам (tr), при этом строки с необходимой информацией имеют внутреннее
        # деление (th - td), где в th хранится название строки с информацией, а в td - содержание
        for row in table.findAll("tr"):

            # В начале идет какое-то количество строк без такого деления - название, название в ориг., постер и т.д.
            if row.find("td") and row.find("th"):

                # При извлечении текста сразу можно удалить незначащие пробелы (метод strip), сноски (регулярное
                # выражение с квадратными скобками) и unicode-разделители (параметер strip в getText)
                th = row.find("th").getText().strip()
                td = re.sub(r'\[.*?]', "", row.find("td").getText(strip=True).strip())

                # Проверка на извлечение только необходимой информации по названию строки
                if th == "Режиссёр" or th == "Режиссёры":
                    fim_info_dict["Режиссёр"] = td
                if th == "Жанр" or th == "Жанры":
                    fim_info_dict["Жанр"] = td
                if th == "Страна" or th == "Страны":
                    fim_info_dict["Страна"] = td
                if th == "Год" or th == "Года":
                    fim_info_dict["Год"] = td

        return fim_info_dict

    def response_parser(self, response):
        """Скрапинг страниц со списком фильмов по алфавиту"""
        for film in response.xpath("//div[@id='mw-pages']//div[@class='mw-category-group']//ul//li"):
            link = "https://ru.wikipedia.org/" + film.xpath(".//a/@href").get()  # Извлечение ссылки на фильм
            yield self.get_film_data(link)  # Скрапинг страницы фильма

        # Извлечение последней ссылки на странице, которая должна вести на следующую
        next_link = "https://ru.wikipedia.org/" + response.xpath("//div[@id='mw-pages']//a/@href")[-1].get()
        page_type = response.xpath("//div[@id='mw-pages']//a/text()")[-1].extract()

        # Если дошли до последней страницы, то последняя ссылка будет вести на предыдущую
        if page_type == "Следующая страница":
            yield response.follow(next_link, callback=self.response_parser)
