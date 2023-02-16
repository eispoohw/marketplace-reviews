import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union, Optional

import pandas as pd
import undetected_chromedriver as uc


class Parser(ABC):
    def __init__(self):
        print('Parser created!')

    def _init_browser(self) -> None:
        """
        Creates Chrome webdriver.
        """
        self.driver = uc.Chrome()
        print("Webdriver started.")

    @abstractmethod
    def get_raw_html(self, url: str, filename="output.html") -> None:
        """
        Creates html file with found reviews.
        """
        self._init_browser()
        print(f"Collecting data from {url} ...")
        self.driver.get(url)
        time.sleep(2)

    @abstractmethod
    def convert_html_to_csv(self, filename: Union[str, Path], newname: Optional[Union[str, Path]]) -> pd.DataFrame:
        """
        Convert collected html data to csv and DataFrame according to selected marketplace.
        """
        pass

    def __del__(self):
        try:
            self.driver.quit()
        except AttributeError:
            pass
