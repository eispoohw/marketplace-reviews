import datetime
import re
import time
import warnings
from abc import ABC

import pandas as pd
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from tqdm import tqdm

from .ABCParser import Parser
from .utils import MONTHS, change_html_path_to_csv, get_str_from_html

APPROX_COMMENTS_PER_PAGE = 60
STRIP_CHARS = '\n\t  '
warnings.simplefilter(action='ignore', category=FutureWarning)


class OzonParser(Parser, ABC):
    def __init__(self):
        super().__init__()
        self.product_id = None

    def get_raw_html(self, url: str, filename="output.html") -> None:
        self._init_browser()
        self.__set_product_id(url)
        self.__collect_reviews(filename)

    def convert_html_to_csv(self, filename, newname=None) -> pd.DataFrame:
        """
        Convert collected comments to DataFrame and save it in {filename}.csv or newname if specified.

        DataFrame columns:
            | (object ) author - comment author's name
            | (object ) {feature_i} - product feature
            | (int64  ) rate - product rating from 1 to 5
            | (object ) {comment_i} - review text
            | (object) date - date of the comment
            | (int64 ) upvote - likes to a comment from other users
            | (int64 ) downvote - dislikes to a comment from other users
        """
        print('Converting html to csv...')
        soup = BeautifulSoup(get_str_from_html(filename), 'lxml')
        comments = soup.find_all(attrs={"data-review-uuid": re.compile(".")})
        print(f"Found {len(comments)} reviews")

        df = pd.DataFrame()
        for comment in tqdm(comments):
            divs = comment.findChildren("div", recursive=False)
            c_df = {
                'author': divs[0].find("div").findChildren("div", recursive=False)[1].find("div").text.strip(
                    STRIP_CHARS),
                'date': self.__convert_date(divs[0].findChildren("div", recursive=False)[-1].find("div").text)
            }
            """
            Product features 
                such as colour and size
            """
            comment_body = divs[1].findChildren("div", recursive=False)
            features = comment_body[0].find('a')
            if features:
                features = features.text.split(', ')
                for feat in features:
                    name, value = feat.split(': ')
                    name = name.replace(' ', "_").strip(STRIP_CHARS).lower()
                    c_df[name] = value.strip(STRIP_CHARS)
            """
            Comment
                Each is divided into sections:
                
                div : Section
                    div : section name
                    div span : section text
                    
                For example, "Достоинства": "...". Sometimes there is only one section without name.
                It should be called "Комментарий"
            """
            sections = comment_body[1].findChildren("div", recursive=False)
            for section in sections:
                rows = section.findChildren("div", recursive=False)
                if len(rows) == 2:
                    name = rows[0].text.strip(STRIP_CHARS).lower()
                else:
                    name = "комментарий"
                value = rows[-1].text.strip(STRIP_CHARS)
                c_df[name] = value
            """
            Rating
                rate is showed by <div class="aa5-a6" style="width:100%;"></div>
                where width=100% - 5 stars, 80% - 4, 60% - 3, 40% - 2, 20% - 1
            """
            stars = comment.find(class_="aa5-a6")
            stars_num = int(stars.get('style')[6:-2]) / 20
            c_df['rate'] = stars_num
            """
            Upvotes and downvotes
                They are span._4-e3 with values such as "Да 0"/"Нет 5"
            """
            votes = comment.find_all(class_="_4-e3")
            c_df['upvote'] = int(votes[0].text.strip(STRIP_CHARS)[3:])
            c_df['downvote'] = int(votes[1].text.strip(STRIP_CHARS)[4:])
            df = df.append(c_df, ignore_index=True)
        if newname:
            newname = change_html_path_to_csv(filename)
            df.to_csv(newname, index=False)
        print('Done! Data saved to', newname)
        return df

    def __set_product_id(self, url: str) -> None:
        url = url[:url.rfind('/')]
        self.product_id = url[url.rfind('-') + 1:]

    def __get_reviews_page(self, page: int) -> None:
        self.driver.get(f"https://www.ozon.ru/reviews/{self.product_id}/?page={page}")
        time.sleep(2)

    def __collect_reviews(self, filename: str) -> None:
        print('\nCollecting data ...')
        file = open(filename, "w", encoding="utf-8")
        page = 1
        while True:
            self.__get_reviews_page(page)
            review_div = self.driver.find_element(By.XPATH, "//div[@data-widget='webListReviews']")
            data = review_div.get_attribute('innerHTML')
            soup = BeautifulSoup(data, 'lxml')
            if soup.find(string='Показать больше отзывов'):
                print(page, end=" ")
                file.write(data)
                page += 1
            else:
                print(f'\nCompleted! Data collected and stored in \"{filename}\"\n')
                file.close()
                break

    @staticmethod
    def __convert_date(given: str) -> datetime.date:
        edited = given.rfind("изменен ")
        if edited != -1:
            given = given[8:]
        year = int(given[-4:])
        day, month = given[:given.rfind(" ") - 1].split(" ")
        month = MONTHS[month.lower()]
        return datetime.date(year, int(month), int(day))
