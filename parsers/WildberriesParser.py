import pathlib
import time
from abc import ABC
from datetime import datetime, timedelta

import pandas as pd
from .ABCParser import Parser
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from tqdm import tqdm
from .utils import scroll_page


class WildberriesReviewsParser(Parser, ABC):
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

    def get_raw_html(self, url: str, filename='output.html'):
        super().get_raw_html(url, filename)
        self.__go_to_reviews()
        self.__scroll_and_save(filename)
        print(f'Data collected and stored in {filename}')
        self.driver.quit()
        return filename

    def __convert_datetime(self, raw: str) -> datetime:
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

    def convert_html_to_csv(self, filename) -> pd.DataFrame:
        print("Starting to convert")
        raw = self._get_str_from_html(filename)
        soup = BeautifulSoup(raw, "lxml")
        print("Soup created")
        comments = soup.find_all(class_="comments__item")
        print(f"Found {len(comments)} reviews")

        df = pd.DataFrame()
        # author | country |  rate | text | date | upvote | downvote | param_... | photos_count | photo_...
        for i, comment in tqdm(enumerate(comments)):
            df.loc[i, 'author'] = comment.find(class_="feedback__header").text
            df.loc[i, 'country'] = comment.find(class_="feedback__country").get("class")[1][5:]
            df.loc[i, 'rate'] = comment.find(class_="stars-line").get("class")[2][-1]
            df.loc[i, 'text'] = str(comment.find(class_="feedback__text").text)
            df.loc[i, 'date'] = self.__convert_datetime(comment.find(class_="feedback__date").text)
            votes = comment.find(class_="vote__wrap").find_all('span')
            df.loc[i, 'upvote'], df.loc[i, 'downvote'] = votes[0].text, votes[1].text
            for param in comment.find_all(class_="feedback__params-item"):
                spans = param.find_all('span')
                name = spans[0].text[:-1]
                for i, value in enumerate(spans[1:]):
                    df.loc[i, f"param_{name}_{i}"] = value.text
            photos = comment.find_all(class_="j-feedback-photo")
            df.loc[i, 'photos_count'] = len(photos)
            for idx_photo, photo in enumerate(photos):
                df.loc[i, f"photo_{idx_photo}"] = photo.get('src')
        filename = pathlib.Path(filename)
        newname = filename.parent / f"{filename.stem}.csv"
        df.to_csv(newname, index=False)
        print('Done! Data saved to', newname)
        return df
