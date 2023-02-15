import time
from pathlib import Path
from typing import Union

from tqdm import tqdm


def scroll_page_generator(driver, scroll_pause_time: int):
    waited = False
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        # Wait to load page
        time.sleep(scroll_pause_time)
        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            if waited:
                break
            else:
                waited = True
        last_height = new_height
        yield


def scroll_page(driver, scroll_pause_time=1, with_info=True, reverse=False) -> None:
    if reverse:
        driver.execute_script("window.scrollTo(0, 0);")
        return

    if with_info:
        print('Scrolling page...')
        for _ in tqdm(scroll_page_generator(driver, scroll_pause_time)): pass
        print('Scrolling completed!\n')
    else:
        for _ in scroll_page_generator(driver, scroll_pause_time): pass


def get_str_from_html(filename: Union[str, Path]) -> str:
    """
    Returns the contents of the specified html file.
    """
    with open(filename, "r", encoding="utf-8") as file:
        return file.read()


def change_html_path_to_csv(filename: Union[str, Path]):
    if type(filename) == str:
        filename = Path(filename)
    return filename.parent / f"{filename.stem}.csv"
