import time
from abc import ABC
from datetime import datetime, timedelta

import pandas as pd
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from tqdm import tqdm

from .ABCParser import Parser
from .utils import change_html_path_to_csv, get_str_from_html, scroll_page


class WildberriesParser(Parser, ABC):
    def get_raw_html(self, url: str, filename='output.html'):
        super().get_raw_html(url, filename)
        self.__go_to_reviews()
        self.__scroll_and_save(filename)
        print(f'Data collected and stored in \"{filename}\"')
        self.driver.quit()

    def convert_html_to_csv(self, filename) -> pd.DataFrame:
        """
        Convert collected comments to DataFrame and save it in {filename}.csv.

        DataFrame columns:
            | (object) author - comment author's name
            | (object) country - their country
            | (int64 ) rate - product rating from 1 to 5
            | (object) text - review text
            | (object) date - date of the comment
            | (int64 ) upvote - likes to a comment from other users
            | (int64 ) downvote - dislikes to a comment from other users
            | (object) param_{i} - the i-th parameter of the product (e.g. colour)
            | (object) photos_count - number of photos left
            | (object) photo_{i} - link to the i-th photo
        """
        raw = get_str_from_html(filename)
        soup = BeautifulSoup(raw, "lxml")
        comments = soup.find_all(class_="comments__item")
        print(f"Found {len(comments)} reviews")

        df = pd.DataFrame()
        for i, comment in tqdm(enumerate(comments)):
            row = pd.DataFrame()
            row['author'] = comment.find(class_="feedback__header").text,
            row['country'] = comment.find(class_="feedback__country").get("class")[1][5:],
            row['rate'] = comment.find(class_="stars-line").get("class")[2][-1],
            row['text'] = str(comment.find(class_="feedback__text").text),
            row['date'] = self.__convert_datetime(comment.find(class_="feedback__date").text)
            votes = comment.find(class_="vote__wrap").find_all('span')
            row['upvote'], row['downvote'] = votes[0].text, votes[1].text
            for param in comment.find_all(class_="feedback__params-item"):
                spans = param.find_all('span')
                name = spans[0].text[:-1]
                for i, value in enumerate(spans[1:]):
                    row[f"param_{name}_{i}"] = value.text
            try:
                photos = comment.find(class_="feedback__photos").find_all('img')
                row['photos_count'] = len(photos)
                for idx_photo, photo in enumerate(photos):
                    row[f"photo_{idx_photo}"] = photo.get('src')
            except AttributeError:
                row['photos_count'] = 0
            df = pd.concat([df, row])
        newname = change_html_path_to_csv(filename)
        df.to_csv(newname, index=False)
        print('Done! Data saved to', newname)
        return df

    def __go_to_reviews(self) -> None:
        """
        Walk through the product page to get to the feedback page.
        """
        self.driver.execute_script("window.scrollTo(0, 500);")
        self.driver.find_element(By.ID, 'comments_reviews_link').click()
        time.sleep(2)
        self.driver.find_element(By.PARTIAL_LINK_TEXT, 'все отзывы').click()

    def __scroll_and_save(self, filename: str) -> None:
        """
        Scroll feedback page top-down and save page as html.
        """
        scroll_page(self.driver)
        with open(filename, "w", encoding="utf-8") as file:
            file.write(self.driver.page_source)

    @staticmethod
    def __convert_datetime(raw: str) -> datetime:
        """
        Wildberries datetime format converter.
        """
        date, times = raw.split(', ')
        hour, minute = map(int, times.split(':'))
        if date == 'Сегодня':
            return datetime(datetime.now().year, datetime.now().month, datetime.now().day, hour, minute)
        elif date == 'Вчера':
            yesterday = datetime.now() - timedelta(days=1)
            return datetime(yesterday.year, yesterday.month, yesterday.day, hour, minute)
        else:
            months = {
                'января': '01', 'февраля': '02', 'марта': '03', 'апреля': '04',
                'мая': '05', 'июня': '06', 'июля': '07', 'августа': '08',
                'сентября': '09', 'октября': '10', 'ноября': '11', 'декабря': '12'
            }
            date_list = date.split(' ')
            if len(date_list) != 3:
                date_list.append(str(datetime.now().year))
            date_list[1] = months[date_list[1]]
            return datetime.strptime(" ".join(date_list) + ', ' + times, "%d %m %Y, %H:%M")
