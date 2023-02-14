import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Any, Union

import pandas as pd
from selenium import webdriver


class Parser(ABC):
    def __init__(self):
        print('Parser created!')

    def __init_browser(self) -> None:
        """
        Creates Chrome webdriver.
        """
        print("Webdriver initialization...")
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        self.driver = webdriver.Chrome(options=options)
        print("Webdriver started!\n")
        self.driver.maximize_window()
        time.sleep(1)

    def _get_str_from_html(self, filename: Union[str, Path]) -> str:
        """
        Returns the contents of the specified html file.
        """
        with open(filename, "r", encoding="utf-8") as file:
            return file.read()

    @abstractmethod
    def get_raw_html(self, url: str, filename="output.html") -> Union[str, Path]:
        """
        Creates html file with found reviews.
        """
        self.__init_browser()
        print(f"Collecting data from {url} ...")
        self.driver.get(url)
        time.sleep(2)
        return filename

    @abstractmethod
    def convert_html_to_csv(self, filename) -> pd.DataFrame:
        return pd.DataFrame()
